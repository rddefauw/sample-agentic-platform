#!/bin/bash

# Check if container type is provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <service-name>"
    echo "Available services: langgraph-chat, optimizer-workflow, mcp-tool-server, llm-gateway"
    exit 1
fi

SERVICE_NAME="$1"

# Define valid services in an array
VALID_SERVICES=(
    "langgraph-chat"
    "prompt-chaining"
    "routing"
    "parallelization"
    "orchestrator"
    "evaluator-optimizer"
    "llm-gateway"
    "memory-gateway"
    "retrieval-gateway"
    "diy-agent"
    "pydanticai-agent"
)

# Check if service name is in the array
VALID=0
for svc in "${VALID_SERVICES[@]}"; do
    if [ "$SERVICE_NAME" = "$svc" ]; then
        VALID=1
        break
    fi
done

if [ "$VALID" -eq 0 ]; then
    echo "Invalid service name. Please use one of the following: ${VALID_SERVICES[*]}"
    exit 0
fi

# Move to project root
cd "$(dirname "$0")/.."

# Configuration
AWS_REGION=$(aws configure get region)
ECR_REPO_NAME="agentic-platform-${SERVICE_NAME}"  # Repository name based on service
IMAGE_TAG="latest"  # Using latest tag

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME"

# Authenticate Docker with ECR
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

# Create ECR repository if it doesn't exist
aws ecr describe-repositories --repository-names "$ECR_REPO_NAME" --region "$AWS_REGION" || \
    aws ecr create-repository --repository-name "$ECR_REPO_NAME" --region "$AWS_REGION"

# Determine Dockerfile path based on service name
DOCKERFILE_PATH="docker/${SERVICE_NAME}/Dockerfile"

# Build Docker image
echo "Building Docker image..."
docker build --platform linux/amd64 -t "$ECR_REPO_URI:$IMAGE_TAG" -f "$DOCKERFILE_PATH" .

# Push to ECR
echo "Pushing to ECR..."
docker push "$ECR_REPO_URI:$IMAGE_TAG"

echo "Done! Image pushed to: $ECR_REPO_URI:$IMAGE_TAG"
