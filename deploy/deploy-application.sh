#!/bin/bash

# Check if service name is provided
if [ $# -lt 1 ] || [ $# -gt 2 ]; then
    echo "Usage: $0 <service-name> [--build]"
    echo "  --build: Build and push container before deploying"
    exit 1
fi

SERVICE_NAME=$1
BUILD_CONTAINER=false

# Check for build flag
if [ $# -eq 2 ] && [ "$2" = "--build" ]; then
    BUILD_CONTAINER=true
fi

# Create overlay file if it doesn't exist
OVERLAY_FILE="k8s/helm/values/overlay/aws-overlay-values.yaml"
if [ ! -f "$OVERLAY_FILE" ]; then
    mkdir -p k8s/helm/values/overlay
    
    AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
    AWS_REGION=$(aws configure get region)
    
    cat > "$OVERLAY_FILE" << EOF
aws:
  account: "$AWS_ACCOUNT"
  region: "$AWS_REGION"
  stackPrefix: "agent-ptfm"
EOF
fi

# Build and push the container if requested
if [ "$BUILD_CONTAINER" = true ]; then
    echo "Building and pushing container..."
    ./deploy/build-container.sh $SERVICE_NAME
    if [ $? -ne 0 ]; then
        echo "Error: Container build failed"
        exit 1
    fi
fi

# Deploy with Helm using values files
echo "Deploying $SERVICE_NAME to Kubernetes with Helm..."
helm upgrade --install $SERVICE_NAME ./k8s/helm/charts/agentic-service \
  -f k8s/helm/values/applications/${SERVICE_NAME}-values.yaml \
  -f k8s/helm/values/overlay/aws-overlay-values.yaml

echo "Deployment complete!"
