#!/bin/bash

# Exit on error
set -e

# Static variables
ARGOCD_NAMESPACE="argocd"

# CLI based variables
AWS_REGION=$(aws configure get region)
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Extract terraform variables from parameter store
PARAMS=$(aws ssm get-parameter \
  --name "/agentic-platform/config/dev" \
  --with-decryption \
  --query 'Parameter.Value' \
  --output text)

VPC_ID=$(echo "$PARAMS" | jq -r '.VPC_ID')
CLUSTER_NAME=$(echo "$PARAMS" | jq -r '.CLUSTER_NAME')
ENVIRONMENT=$(echo "$PARAMS" | jq -r '.ENVIRONMENT')
AWS_LOAD_BALANCER_CONTROLLER_ROLE_ARN=$(echo "$PARAMS" | jq -r '.AWS_LOAD_BALANCER_CONTROLLER_ROLE_ARN')
EXTERNAL_SECRETS_ROLE_ARN=$(echo "$PARAMS" | jq -r '.EXTERNAL_SECRETS_ROLE_ARN')


# Parse command line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --name-prefix)
      NAME_PREFIX="$2"
      shift 2
      ;;
    --git-repo)
      GIT_REPO_URL="$2"
      shift 2
      ;;
    --git-username)
      GIT_USERNAME="$2"
      shift 2
      ;;
    --git-password)
      GIT_PASSWORD="$2"
      shift 2
      ;;
    --cluster-name)
      CLUSTER_NAME="$2"
      shift 2
      ;;
    --environment)
      ENVIRONMENT="$2"
      shift 2
      ;;
    --vpc-id)
      VPC_ID="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      shift
      ;;
  esac
done

echo "=== Bootstrap Configuration ==="
echo "AWS Account ID: $AWS_ACCOUNT_ID"
echo "AWS Region: $AWS_REGION"
echo "Name Prefix: $NAME_PREFIX"
echo "Environment: $ENVIRONMENT"
echo "Cluster Name: $CLUSTER_NAME"
echo "VPC ID: $VPC_ID"
echo "Git Repository URL: $GIT_REPO_URL"
echo "Git Username: $GIT_USERNAME"
echo "ArgoCD Namespace: $ARGOCD_NAMESPACE"
echo "Secret Name: $SECRET_NAME"
echo "============================="

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Check for required tools
for cmd in kubectl aws helm argocd; do
  if ! command_exists "$cmd"; then
    echo "Error: $cmd is required but not installed. Please install it and try again."
    exit 1
  fi
done

# Check if kubectl can connect to the cluster
echo "Checking connection to Kubernetes cluster..."
if ! kubectl get nodes &>/dev/null; then
  echo "Error: Cannot connect to Kubernetes cluster. Please check your kubeconfig."
  exit 1
fi

# Validate required parameters
if [ -z "$VPC_ID" ]; then
  echo "Error: VPC ID is required. Please provide it with --vpc-id parameter."
  exit 1
fi

if [ -z "$CLUSTER_NAME" ]; then
  echo "Error: CLUSTER NAME is required. Please provide it with --cluster-name parameter."
  exit 1
fi

# Create ArgoCD namespace if it doesn't exist
echo "Creating ArgoCD namespace if it doesn't exist..."
kubectl create namespace $ARGOCD_NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Install ArgoCD
echo "Installing ArgoCD..."
kubectl apply -n $ARGOCD_NAMESPACE -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD to be ready
echo "Waiting for ArgoCD to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n $ARGOCD_NAMESPACE

# Get ArgoCD admin password
echo "Getting ArgoCD admin password..."
ARGOCD_PASSWORD=$(kubectl -n $ARGOCD_NAMESPACE get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)

# Setup port-forward and login to ArgoCD
echo "Setting up port-forward and logging into ArgoCD..."
kubectl port-forward svc/argocd-server -n $ARGOCD_NAMESPACE 8081:443 >/dev/null 2>&1 &
PORT_FORWARD_PID=$!

# Wait for port-forward
sleep 5

# Login to ArgoCD
argocd login localhost:8081 --username admin --password "$ARGOCD_PASSWORD" --insecure

# Add git repository if credentials provided
if [ -n "$GIT_USERNAME" ] && [ -n "$GIT_PASSWORD" ]; then
  echo "Adding git repository to ArgoCD..."
  argocd repo add "$GIT_REPO_URL" --username "$GIT_USERNAME" --password "$GIT_PASSWORD" --upsert
fi

# 5. Create bootstrap parent application
echo "Applying the app of app manifest and substituting the default git repo with user passed one."
sed "s|repoURL:.*|repoURL: $GIT_REPO_URL|" k8s/argocd/app-of-apps.yaml | kubectl apply -f -

# 6. Trigger initial sync
echo "Syncing parent application..."
argocd app sync app-of-apps

# Kill port-forward - try gentle kill first, then find by port
echo "Stopping port-forward..."
if [ -n "$PORT_FORWARD_PID" ]; then
  kill $PORT_FORWARD_PID 2>/dev/null || true
  sleep 2
fi

# Find any remaining processes using port 8081 and kill them
REMAINING_PIDS=$(ps aux | grep '[k]ubectl.*port-forward.*8081' | awk '{print $2}')
if [ -n "$REMAINING_PIDS" ]; then
  echo "Found remaining port-forward processes, killing them..."
  echo $REMAINING_PIDS | xargs kill 2>/dev/null || true
  sleep 2
  # Force kill if still running
  echo $REMAINING_PIDS | xargs kill -9 2>/dev/null || true
fi

# # Construct the ESO IRSA ARN
# ESO_ROLE_NAME="${NAME_PREFIX}external-secrets-role"
# ESO_IRSA_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/${ESO_ROLE_NAME}"
# echo "ESO IRSA ARN: $ESO_IRSA_ARN"

# Create a secret with the ESO IRSA ARN for other components that might need it
echo "Creating bootstrap configuration secret..."
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: $SECRET_NAME
  namespace: $ARGOCD_NAMESPACE
type: Opaque
stringData:
  eso-irsa-role-arn: "$ESO_IRSA_ARN"
  aws-region: "$AWS_REGION"
  git-repo-url: "$GIT_REPO_URL"
EOF

# Create cluster secret with metadata for ApplicationSet templating
echo "Creating cluster secret with metadata labels and annotations..."
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: ${CLUSTER_NAME}-cluster-secret
  namespace: $ARGOCD_NAMESPACE
  labels:
    argocd.argoproj.io/secret-type: cluster
    # Custom labels for ApplicationSet templating
    accountId: "$AWS_ACCOUNT_ID"
    environment: "$ENVIRONMENT"
    region: "$AWS_REGION"
    vpcId: "$VPC_ID"
    clusterName: "$CLUSTER_NAME"
    cluster-type: "eks"
    managed-by: "argocd"
  annotations:
    # Custom annotations for ApplicationSet bootstrapping
    accountId: "$AWS_ACCOUNT_ID"
    environment: "$ENVIRONMENT"
    region: "$AWS_REGION"
    vpcId: "$VPC_ID"
    esoArn: "$EXTERNAL_SECRETS_ROLE_ARN"
    lbcArn: "$AWS_LOAD_BALANCER_CONTROLLER_ROLE_ARN"
    createdBy: "bootstrapScript"
type: Opaque
stringData:
  name: "$CLUSTER_NAME"
  server: "https://kubernetes.default.svc"
  config: |
    {
      "tlsClientConfig": {
        "insecure": false
      }
    }
EOF

echo "Bootstrap completed successfully!"
echo "ArgoCD Admin Password: $ARGOCD_PASSWORD"
echo ""
echo "To access ArgoCD UI, run:"
echo "kubectl port-forward svc/argocd-server -n $ARGOCD_NAMESPACE 8081:443"
echo "Then open https://localhost:8081 in your browser"

echo ""
echo "Cluster metadata available for ApplicationSet templating:"
echo "- {{.metadata.labels.accountId}} = $AWS_ACCOUNT_ID"
echo "- {{.metadata.labels.environment}} = $ENVIRONMENT"
echo "- {{.metadata.labels.region}} = $AWS_REGION"
echo "- {{.metadata.labels.vpcId}} = $VPC_ID"
echo "- {{.metadata.annotations.\"cluster.argoproj.io/accountId\"}} = $AWS_ACCOUNT_ID"
echo "- {{.metadata.annotations.\"cluster.argoproj.io/environment\"}} = $ENVIRONMENT"
echo "- {{.metadata.annotations.\"cluster.argoproj.io/region\"}} = $AWS_REGION"
echo "- {{.metadata.annotations.\"cluster.argoproj.io/vpcId\"}} = $VPC_ID"