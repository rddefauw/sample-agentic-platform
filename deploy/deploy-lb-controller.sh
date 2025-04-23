#!/bin/bash
# set -e

# Because the chart requires information from the Terraform output, 
# we need to run this script after the Terraform deployment is complete.

# Define the Terraform directory
TERRAFORM_DIR="infrastructure/terraform"

# Get values directly using absolute paths
echo "Retrieving Terraform outputs..."
CLUSTER_NAME=$(cd "$TERRAFORM_DIR" && terraform output -raw eks_cluster_name)
ROLE_ARN=$(cd "$TERRAFORM_DIR" && terraform output -raw aws_load_balancer_controller_role_arn)
VPC_ID=$(cd "$TERRAFORM_DIR" && terraform output -raw vpc_id)
REGION=$(aws configure get region)

echo "Retrieved values:"

# Path to Helm chart
CHART_DIR="k8s/helm/charts/lb-controller"

# Update dependencies
echo "Updating Helm dependencies..."
helm dependency update "$CHART_DIR"

# Install/upgrade the chart with the preferred name "lb-controller"
echo "Installing cluster components with name lb-controller..."

helm upgrade --install lb-controller "$CHART_DIR"  \
    --namespace kube-system \
    --create-namespace \
    --set aws-load-balancer-controller.clusterName="$CLUSTER_NAME" \
    --set aws-load-balancer-controller.region="$REGION" \
    --set aws-load-balancer-controller.vpcId="$VPC_ID" \
    --set "aws-load-balancer-controller.serviceAccount.annotations.eks\.amazonaws\.com/role-arn=$ROLE_ARN"

echo "Cluster components deployed successfully!"