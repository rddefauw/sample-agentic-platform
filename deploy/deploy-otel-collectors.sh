#!/bin/bash

# Get all IRSA roles
IRSA_ROLES=$(terraform -chdir=infrastructure/terraform output -json irsa_roles)

# Extract specific role ARNs
OTEL_ROLE_ARN=$(echo $IRSA_ROLES | jq -r '.otel_collector')

# Get OpenSearch endpoint
CLUSTER_NAME=$(terraform -chdir=infrastructure/terraform output -raw eks_cluster_name)
REGION=$(aws configure get region)

# Install the OpenTelemetry Helm chart
helm upgrade --install otel ./k8s/helm/charts/otel \
  --namespace observability \
  --create-namespace \
  --set irsaRoleArn="${OTEL_ROLE_ARN}" \
  --set clusterName="${CLUSTER_NAME}" \
  --set region="${REGION}"

