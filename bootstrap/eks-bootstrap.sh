#!/bin/bash

set -e  # Exit on any error

echo "========================================="
echo "Bootstrapping EKS Cluster Essentials"
echo "========================================="

# Extract terraform outputs from parameter store
echo "🔍 Retrieving configuration from Parameter Store..."
PARAMS=$(aws ssm get-parameter \
  --name "/agentic-platform/config/dev" \
  --with-decryption \
  --query 'Parameter.Value' \
  --output text)

# Extract all needed values
CLUSTER_NAME=$(echo "$PARAMS" | jq -r '.CLUSTER_NAME')
AWS_LOAD_BALANCER_CONTROLLER_ROLE_ARN=$(echo "$PARAMS" | jq -r '.AWS_LOAD_BALANCER_CONTROLLER_ROLE_ARN')
VPC_ID=$(echo "$PARAMS" | jq -r '.VPC_ID')
EXTERNAL_SECRETS_ROLE_ARN=$(echo "$PARAMS" | jq -r '.EXTERNAL_SECRETS_ROLE_ARN')
OTEL_COLLECTOR_ROLE_ARN=$(echo "$PARAMS" | jq -r '.OTEL_COLLECTOR_ROLE_ARN')

REGION=$(aws configure get region)

echo "✅ Configuration retrieved successfully"

# 1. Deploy Storage
echo ""
echo "🚀 Deploying Storage..."
helm upgrade --install storage ./k8s/helm/charts/storage \
  --namespace kube-system
echo "✅ Storage deployed"

# 2. Deploy Load Balancer Controller
echo ""
echo "🚀 Deploying Load Balancer Controller..."
helm dependency update k8s/helm/charts/lb-controller
helm upgrade --install lb-controller k8s/helm/charts/lb-controller \
    --namespace kube-system \
    --create-namespace \
    --set aws-load-balancer-controller.clusterName="$CLUSTER_NAME" \
    --set aws-load-balancer-controller.region="$REGION" \
    --set aws-load-balancer-controller.vpcId="$VPC_ID" \
    --set "aws-load-balancer-controller.serviceAccount.annotations.eks\.amazonaws\.com/role-arn=$AWS_LOAD_BALANCER_CONTROLLER_ROLE_ARN"
echo "✅ Load Balancer Controller deployed"

# 3. Deploy External Secrets
echo ""
echo "🚀 Deploying External Secrets..."
helm dependency update k8s/helm/charts/external-secrets-operator
helm upgrade --install external-secrets k8s/helm/charts/external-secrets-operator \
    --namespace external-secrets-system \
    --create-namespace \
    --set serviceAccount.roleArn="$EXTERNAL_SECRETS_ROLE_ARN" \
    --set aws.region="$REGION" \
    --set environment="dev" \
    --set external-secrets.installCRDs=true \
    --set external-secrets.namespace=external-secrets-system

helm upgrade --install external-secrets-config k8s/helm/charts/external-secrets-config \
    --namespace default \
    --set aws.region="$REGION" \
    --set environment="dev"
echo "✅ External Secrets deployed"

# 4. Deploy OTEL Collectors
echo ""
echo "🚀 Deploying OTEL Collectors..."
helm upgrade --install otel ./k8s/helm/charts/otel \
  --namespace observability \
  --create-namespace \
  --set serviceAccount.roleArn="${OTEL_COLLECTOR_ROLE_ARN}" \
  --set clusterName="${CLUSTER_NAME}" \
  --set region="${REGION}"
echo "✅ OTEL Collectors deployed"

echo ""
echo "========================================="
echo "✅ All cluster essentials deployed!"
echo "========================================="