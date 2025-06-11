#!/bin/bash

# Define the service name and Terraform directory
SERVICE_NAME="llm-gateway"

# Build and push the container
./deploy/build-container.sh $SERVICE_NAME

# Extract terraform variables from parameter store
PARAMS=$(aws ssm get-parameter \
  --name "/agentic-platform/config/dev" \
  --with-decryption \
  --query 'Parameter.Value' \
  --output text)

REDIS_HOST=$(echo "$PARAMS" | jq -r '.REDIS_HOST')
REDIS_PORT=$(echo "$PARAMS" | jq -r '.REDIS_PORT')
REDIS_PASSWORD_SECRET_ARN=$(echo "$PARAMS" | jq -r '.REDIS_PASSWORD_SECRET_ARN')
DYNAMODB_USAGE_PLANS_TABLE=$(echo "$PARAMS" | jq -r '.DYNAMODB_USAGE_PLANS_TABLE')
DYNAMODB_USAGE_LOGS_TABLE=$(echo "$PARAMS" | jq -r '.DYNAMODB_USAGE_LOGS_TABLE')
LLM_GATEWAY_ROLE_ARN=$(echo "$PARAMS" | jq -r '.LLM_GATEWAY_ROLE_ARN')
COGNITO_USER_POOL_ID=$(echo "$PARAMS" | jq -r '.COGNITO_USER_POOL_ID')
COGNITO_USER_CLIENT_ID=$(echo "$PARAMS" | jq -r '.COGNITO_USER_CLIENT_ID')
COGNITO_M2M_CLIENT_ID=$(echo "$PARAMS" | jq -r '.COGNITO_M2M_CLIENT_ID')


# Get ECR URI for Helm
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region)
ECR_REPO_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/agentic-platform-${SERVICE_NAME}"

# Deploy with Helm
echo "Deploying to Kubernetes with Helm..."
helm upgrade --install $SERVICE_NAME ./k8s/helm/charts/agentic-service \
  --set image.repository=$ECR_REPO_URI \
  --set nameOverride=$SERVICE_NAME \
  --set serviceAccount.roleArn=$LLM_GATEWAY_ROLE_ARN \
  --set serviceAccount.name="llm-gateway-sa" \
  --set config.AWS_DEFAULT_REGION=$AWS_REGION \
  --set config.REDIS_HOST=$REDIS_HOST \
  --set config.REDIS_PORT=$REDIS_PORT \
  --set config.REDIS_PASSWORD_SECRET_ARN=$REDIS_PASSWORD_SECRET_ARN \
  --set config.DYNAMODB_USAGE_PLANS_TABLE=$DYNAMODB_USAGE_PLANS_TABLE \
  --set config.DYNAMODB_USAGE_LOGS_TABLE=$DYNAMODB_USAGE_LOGS_TABLE \
  --set config.COGNITO_USER_POOL_ID=$COGNITO_USER_POOL_ID \
  --set config.COGNITO_USER_CLIENT_ID=$COGNITO_USER_CLIENT_ID \
  --set config.COGNITO_M2M_CLIENT_ID=$COGNITO_M2M_CLIENT_ID \
  --set ingress.enabled=true \
  --set ingress.path="/$SERVICE_NAME"

echo "Deployment complete!"
