#!/bin/bash

# Define all services to deploy
SERVICES=(
    "langgraph-chat"
    "prompt-chaining"
    "routing"
    "parallelization"
    "orchestrator"
    "evaluator-optimizer"
    "diy-agent"
    "pydanticai-agent"
)

echo "Starting deployment of all agents..."

# Loop through each service and deploy
for SERVICE in "${SERVICES[@]}"; do
    echo "=========================================="
    echo "Deploying $SERVICE"
    echo "=========================================="
    
    # Call the deploy script for each service
    . ./deploy/deploy-agent.sh "$SERVICE"
    
    # Check if deployment was successful
    if [ $? -eq 0 ]; then
        echo "✅ Successfully deployed $SERVICE"
    else
        echo "❌ Failed to deploy $SERVICE"
    fi
    
    echo ""
done

echo "All deployments completed!"
