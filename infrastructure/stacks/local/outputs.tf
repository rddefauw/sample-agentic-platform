########################################################
# Kubernetes Outputs
########################################################

output "kubernetes_config_map_name" {
  description = "Name of the platform configuration ConfigMap"
  value       = module.kubernetes.config_map_name
}

output "kubernetes_config_map_namespace" {
  description = "Namespace of the platform configuration ConfigMap"
  value       = module.kubernetes.config_map_namespace
}

########################################################
# Platform Configuration Outputs
########################################################

output "platform_config_keys" {
  description = "List of configuration keys available in the platform config"
  value       = keys(local.platform_config)
  sensitive   = true
}

output "eks_cluster_name" {
  description = "Name of the EKS cluster from platform config"
  value       = local.platform_config.EKS_CLUSTER_NAME
  sensitive   = true
}
