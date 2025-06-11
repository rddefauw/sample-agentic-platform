#!/bin/bash

# Define the service name and Terraform directory
SERVICE_NAME="memory-gateway"

# Build and push the container
./deploy/build-container.sh $SERVICE_NAME

# Get Terraform outputs using the direct output values
echo "Retrieving Terraform outputs..."

# Extract terraform variables from parameter store
PARAMS=$(aws ssm get-parameter \
  --name "/agentic-platform/config/dev" \
  --with-decryption \
  --query 'Parameter.Value' \
  --output text)

PG_WRITER_ENDPOINT=$(echo "$PARAMS" | jq -r '.PG_WRITER_ENDPOINT')
PG_READER_ENDPOINT=$(echo "$PARAMS" | jq -r '.PG_READER_ENDPOINT')
PG_PORT=$(echo "$PARAMS" | jq -r '.PG_PORT')
PG_DATABASE=$(echo "$PARAMS" | jq -r '.PG_DATABASE')
PG_USER=$(echo "$PARAMS" | jq -r '.PG_USER')
PG_PASSWORD_SECRET_ARN=$(echo "$PARAMS" | jq -r '.PG_PASSWORD_SECRET_ARN')
COGNITO_USER_POOL_ID=$(echo "$PARAMS" | jq -r '.COGNITO_USER_POOL_ID')
COGNITO_USER_CLIENT_ID=$(echo "$PARAMS" | jq -r '.COGNITO_USER_CLIENT_ID')
COGNITO_M2M_CLIENT_ID=$(echo "$PARAMS" | jq -r '.COGNITO_M2M_CLIENT_ID')
MEMORY_GATEWAY_ROLE_ARN=$(echo "$PARAMS" | jq -r '.MEMORY_GATEWAY_ROLE_ARN')


# Get ECR URI for Helm
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region)
ECR_REPO_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/agentic-platform-${SERVICE_NAME}"

# Deploy with Helm using the generic agentic-service chart
echo "Deploying to Kubernetes with Helm..."
helm upgrade --install $SERVICE_NAME ./k8s/helm/charts/agentic-service \
  --set image.repository=$ECR_REPO_URI \
  --set nameOverride=$SERVICE_NAME \
  --set serviceAccount.roleArn=$MEMORY_GATEWAY_ROLE_ARN \
  --set serviceAccount.name="memory-gateway-sa" \
  --set config.AWS_DEFAULT_REGION=$AWS_REGION \
  --set config.COGNITO_USER_POOL_ID=$COGNITO_USER_POOL_ID \
  --set config.COGNITO_USER_CLIENT_ID=$COGNITO_USER_CLIENT_ID \
  --set config.COGNITO_M2M_CLIENT_ID=$COGNITO_M2M_CLIENT_ID \
  --set config.PG_WRITER_ENDPOINT=$PG_WRITER_ENDPOINT \
  --set config.PG_READER_ENDPOINT=$PG_READER_ENDPOINT \
  --set config.PG_PORT=$PG_PORT \
  --set config.PG_DATABASE=$PG_DATABASE \
  --set config.PG_USER=$PG_USER \
  --set config.PG_READ_ONLY_USER=$PG_USER \
  --set config.PG_PASSWORD_SECRET_ARN=$PG_PASSWORD_SECRET_ARN \
  --set config.ENVIRONMENT="dev" \
  --set ingress.enabled=true \
  --set ingress.path="/$SERVICE_NAME"

echo "Deployment complete!"
