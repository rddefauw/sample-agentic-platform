#!/bin/bash

# Deploy with Helm
echo "Deploying storage to Kubernetes with Helm..."
helm upgrade --install storage ./k8s/helm/charts/storage \
  --namespace kube-system

echo "Deployment complete!" 