#!/bin/bash
# set -e

# Extract terraform variables from parameter store
PARAMS=$(aws ssm get-parameter \
  --name "/agentic-platform/config/dev" \
  --with-decryption \
  --query 'Parameter.Value' \
  --output text)

EXTERNAL_SECRETS_ROLE_ARN=$(echo "$PARAMS" | jq -r '.EXTERNAL_SECRETS_ROLE_ARN')

REGION=$(aws configure get region)

echo "Retrieved values:"

# Path to Helm chart
CHART_DIR_OPERATOR="k8s/helm/charts/external-secrets-operator"
CHART_DIR_CONFIG="k8s/helm/charts/external-secrets-config"

# Update dependencies
echo "Updating Helm dependencies..."
helm dependency update "$CHART_DIR_OPERATOR"

# Install/upgrade the chart with the preferred name "external-secrets"
echo "Installing external secrets operator..."

helm upgrade --install external-secrets "$CHART_DIR_OPERATOR" \
    --namespace external-secrets-system \
    --create-namespace \
    --set serviceAccount.roleArn="$EXTERNAL_SECRETS_ROLE_ARN" \
    --set aws.region="$REGION" \
    --set environment="dev" \
    --set external-secrets.installCRDs=true \
    --set external-secrets.namespace=external-secrets-system

echo "External secrets operator deployed successfully!"

# Path to Helm chart

# Install/upgrade the chart
echo "Installing external secrets configuration..."

helm upgrade --install external-secrets-config "$CHART_DIR_CONFIG" \
    --namespace default \
    --set aws.region="$REGION" \
    --set environment="dev"

echo "External secrets configuration deployed successfully!" 