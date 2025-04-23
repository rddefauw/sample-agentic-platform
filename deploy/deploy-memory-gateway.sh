#!/bin/bash

# Define the service name and Terraform directory
SERVICE_NAME="memory-gateway"
TERRAFORM_DIR="infrastructure/terraform"

# Build and push the container
./deploy/build-container.sh $SERVICE_NAME

# Get Terraform outputs using the direct output values
echo "Retrieving Terraform outputs..."

# Get PostgreSQL database outputs
POSTGRES_ENDPOINT=$(cd "$TERRAFORM_DIR" && terraform output -raw postgres_cluster_endpoint)
POSTGRES_READER_ENDPOINT=$(cd "$TERRAFORM_DIR" && terraform output -raw postgres_reader_endpoint)
POSTGRES_PORT=$(cd "$TERRAFORM_DIR" && terraform output -raw postgres_port)
POSTGRES_DB_NAME=$(cd "$TERRAFORM_DIR" && terraform output -raw postgres_database_name)
POSTGRES_USERNAME=$(cd "$TERRAFORM_DIR" && terraform output -raw postgres_iam_username)
POSTGRES_SECRET_ARN=$(cd "$TERRAFORM_DIR" && terraform output -raw postgres_master_secret_arn)

# Get Cognito outputs
COGNITO_USER_POOL_ID=$(cd "$TERRAFORM_DIR" && terraform output -raw cognito_user_pool_id)
COGNITO_USER_CLIENT_ID=$(cd "$TERRAFORM_DIR" && terraform output -raw cognito_user_client_id)
COGNITO_M2M_CLIENT_ID=$(cd "$TERRAFORM_DIR" && terraform output -raw cognito_m2m_client_id)

# Get IAM role ARN for memory gateway (create this in your IAM terraform)
MEMORY_GATEWAY_ROLE_ARN=$(cd "$TERRAFORM_DIR" && terraform output -raw memory_gateway_role_arn || echo "")

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
  --set config.PG_WRITER_ENDPOINT=$POSTGRES_ENDPOINT \
  --set config.PG_READER_ENDPOINT=$POSTGRES_READER_ENDPOINT \
  --set config.PG_PORT=$POSTGRES_PORT \
  --set config.PG_DATABASE=$POSTGRES_DB_NAME \
  --set config.PG_USER=$POSTGRES_USERNAME \
  --set config.PG_READ_ONLY_USER=$POSTGRES_USERNAME \
  --set config.PG_PASSWORD_SECRET_ARN=$POSTGRES_SECRET_ARN \
  --set config.ENVIRONMENT="dev" \
  --set ingress.enabled=true \
  --set ingress.path="/$SERVICE_NAME"

echo "Deployment complete!"
