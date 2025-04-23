#!/bin/bash

# Define the service name and Terraform directory
SERVICE_NAME="llm-gateway"
TERRAFORM_DIR="infrastructure/terraform"

# Build and push the container
./deploy/build-container.sh $SERVICE_NAME

# Get Terraform outputs using the direct output values
echo "Retrieving Terraform outputs..."
REDIS_ENDPOINT=$(cd "$TERRAFORM_DIR" && terraform output -raw redis_ratelimit_endpoint)
REDIS_PORT=$(cd "$TERRAFORM_DIR" && terraform output -raw redis_ratelimit_port)
REDIS_PASSWORD_SECRET_ARN=$(cd "$TERRAFORM_DIR" && terraform output -raw redis_password_secret_arn)
DYNAMODB_USAGE_PLANS_TABLE=$(cd "$TERRAFORM_DIR" && terraform output -raw usage_plans_table_name)
DYNAMODB_USAGE_LOGS_TABLE=$(cd "$TERRAFORM_DIR" && terraform output -raw usage_logs_table_name)
LLM_GATEWAY_ROLE_ARN=$(cd "$TERRAFORM_DIR" && terraform output -raw llm_gateway_role_arn)
COGNITO_USER_POOL_ID=$(cd "$TERRAFORM_DIR" && terraform output -raw cognito_user_pool_id)
COGNITO_USER_CLIENT_ID=$(cd "$TERRAFORM_DIR" && terraform output -raw cognito_user_client_id)
COGNITO_M2M_CLIENT_ID=$(cd "$TERRAFORM_DIR" && terraform output -raw cognito_m2m_client_id)

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
  --set config.REDIS_HOST=$REDIS_ENDPOINT \
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
