#!/bin/bash

# Extract terraform variables from parameter store
PARAMS=$(aws ssm get-parameter \
  --name "/agentic-platform/config/dev" \
  --with-decryption \
  --query 'Parameter.Value' \
  --output text)

CLUSTER_NAME=$(echo "$PARAMS" | jq -r '.CLUSTER_NAME')
OTEL_COLLECTOR_ROLE_ARN=$(echo "$PARAMS" | jq -r '.OTEL_COLLECTOR_ROLE_ARN')

AWS_REGION=$(aws configure get region)

# Install the OpenTelemetry Helm chart
helm upgrade --install otel ./k8s/helm/charts/otel \
  --namespace observability \
  --create-namespace \
  --set serviceAccount.roleArn="${OTEL_COLLECTOR_ROLE_ARN}" \
  --set clusterName="${CLUSTER_NAME}" \
  --set region="${AWS_REGION}"

