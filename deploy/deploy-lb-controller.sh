#!/bin/bash
# set -e

# Extract terraform variables from parameter store
PARAMS=$(aws ssm get-parameter \
  --name "/agentic-platform/config/dev" \
  --with-decryption \
  --query 'Parameter.Value' \
  --output text)

CLUSTER_NAME=$(echo "$PARAMS" | jq -r '.CLUSTER_NAME')
AWS_LOAD_BALANCER_CONTROLLER_ROLE_ARN=$(echo "$PARAMS" | jq -r '.AWS_LOAD_BALANCER_CONTROLLER_ROLE_ARN')
VPC_ID=$(echo "$PARAMS" | jq -r '.VPC_ID')


REGION=$(aws configure get region)

echo "Retrieved values:"

# Path to Helm chart
CHART_DIR="k8s/helm/charts/lb-controller"

# Update dependencies
echo "Updating Helm dependencies..."
helm dependency update "$CHART_DIR"

# Install/upgrade the chart with the preferred name "lb-controller"
echo "Installing cluster components with name lb-controller..."

helm upgrade --install lb-controller "$CHART_DIR"  \
    --namespace kube-system \
    --create-namespace \
    --set aws-load-balancer-controller.clusterName="$CLUSTER_NAME" \
    --set aws-load-balancer-controller.region="$REGION" \
    --set aws-load-balancer-controller.vpcId="$VPC_ID" \
    --set "aws-load-balancer-controller.serviceAccount.annotations.eks\.amazonaws\.com/role-arn=$AWS_LOAD_BALANCER_CONTROLLER_ROLE_ARN"

echo "Cluster components deployed successfully!"