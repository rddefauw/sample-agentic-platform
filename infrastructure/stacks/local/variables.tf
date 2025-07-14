########################################################
# Core Variables
########################################################

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "agentic-platform"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

########################################################
# Kubernetes Variables
########################################################

variable "kubernetes_namespace" {
  description = "Kubernetes namespace for resources"
  type        = string
  default     = "default"
}

variable "use_local_proxy" {
  description = "Use local kubectl proxy instead of direct EKS connection"
  type        = bool
  default     = false
}

variable "otel_chart_path" {
  description = "Path to the OTEL collectors Helm chart"
  type        = string
  default     = "../../../k8s/helm/charts/otel"
}

########################################################
# Database Variables
########################################################

variable "create_database_resources" {
  description = "Whether to create database tables and users"
  type        = bool
  default     = true
}
