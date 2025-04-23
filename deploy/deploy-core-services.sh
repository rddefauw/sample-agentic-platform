#!/bin/bash
# deploy/deploy-core-services.sh

# Exit on errors
set -e

echo "=== Deploying Core Services ==="
echo "This script will deploy all core infrastructure components and services."

# Step 1: Deploy AWS Load Balancer Controller
echo ""
echo "=== Deploying AWS Load Balancer Controller ==="
./deploy/deploy-lb-controller.sh

# Step 2: Deploy OpenTelemetry Collectors
echo ""
echo "=== Deploying OpenTelemetry Collectors ==="
./deploy/deploy-otel-collectors.sh

# Step 3: Deploy LLM Gateway
echo ""
echo "=== Deploying LLM Gateway ==="
./deploy/deploy-llm-gateway.sh

# Step 4: Deploy Memory Gateway
echo ""
echo "=== Deploying Memory Gateway ==="
./deploy/deploy-memory-gateway.sh

# Step 5: Deploy Retrieval Gateway
echo ""
echo "=== Deploying Retrieval Gateway ==="
./deploy/deploy-retrieval-gateway.sh

# Additional services can be added here as needed

echo ""
echo "=== All Core Services Deployed Successfully ==="
echo "Core platform is ready to use." 