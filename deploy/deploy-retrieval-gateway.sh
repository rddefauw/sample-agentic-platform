#!/bin/bash

# Define the service name and Terraform directory
SERVICE_NAME="retrieval-gateway"

# Build and push the container
./deploy/build-container.sh $SERVICE_NAME

# Extract terraform variables from parameter store
PARAMS=$(aws ssm get-parameter \
  --name "/agentic-platform/config/dev" \
  --with-decryption \
  --query 'Parameter.Value' \
  --output text)

KNOWLEDGE_BASE_ID=$(echo "$PARAMS" | jq -r '.KNOWLEDGE_BASE_ID')
COGNITO_USER_POOL_ID=$(echo "$PARAMS" | jq -r '.COGNITO_USER_POOL_ID')
COGNITO_USER_CLIENT_ID=$(echo "$PARAMS" | jq -r '.COGNITO_USER_CLIENT_ID')
COGNITO_M2M_CLIENT_ID=$(echo "$PARAMS" | jq -r '.COGNITO_M2M_CLIENT_ID')
RETRIEVAL_GATEWAY_ROLE_ARN=$(echo "$PARAMS" | jq -r '.RETRIEVAL_GATEWAY_ROLE_ARN')

# Get ECR URI for Helm
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region)
ECR_REPO_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/agentic-platform-${SERVICE_NAME}"

# Deploy with Helm using the generic agentic-service chart
echo "Deploying to Kubernetes with Helm..."
helm upgrade --install $SERVICE_NAME ./k8s/helm/charts/agentic-service \
  --set image.repository=$ECR_REPO_URI \
  --set nameOverride=$SERVICE_NAME \
  --set serviceAccount.roleArn=$RETRIEVAL_GATEWAY_ROLE_ARN \
  --set serviceAccount.name="retrieval-gateway-sa" \
  --set config.AWS_DEFAULT_REGION=$AWS_REGION \
  --set config.COGNITO_USER_POOL_ID=$COGNITO_USER_POOL_ID \
  --set config.COGNITO_USER_CLIENT_ID=$COGNITO_USER_CLIENT_ID \
  --set config.COGNITO_M2M_CLIENT_ID=$COGNITO_M2M_CLIENT_ID \
  --set config.KNOWLEDGE_BASE_ID=$KNOWLEDGE_BASE_ID \
  --set config.ENVIRONMENT="dev" \
  --set ingress.enabled=true \
  --set ingress.path="/$SERVICE_NAME"

echo "Deployment complete!"
