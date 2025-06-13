#!/bin/bash

# Deploy with Helm
echo "Deploying cluster-base to Kubernetes with Helm..."
helm upgrade --install cluster-base ./k8s/helm/charts/cluster-base \
  --namespace kube-system

echo "Deployment complete!" 