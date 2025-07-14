# Application Setup Layer
#
# This layer handles application-level configuration and setup that requires
# the infrastructure to be deployed first. It includes:
# - Kubernetes resources (ConfigMaps, Secrets, etc.)
# - Database table creation and user setup
# - Application-specific configurations
#
# This layer runs after the platform layer and requires VPC connectivity
# to access private resources like EKS clusters and RDS databases.

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 2.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = ">= 2.0"
    }
    postgresql = {
      source  = "cyrilgdn/postgresql"
      version = ">= 1.21.0"
    }
  }
}

# Get current region and account data
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

# Local values
locals {
  name_prefix = "${var.environment}-${var.project_name}"
  common_tags = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "terraform"
    Layer       = "application"
  }
}

########################################################
# Data Sources - Get Platform Configuration
########################################################

# Get platform configuration from parameter store
data "aws_ssm_parameter" "platform_config" {
  name = "/agentic-platform/config/${var.environment}"
}

locals {
  # Parse the platform configuration JSON
  platform_config = jsondecode(data.aws_ssm_parameter.platform_config.value)
}

########################################################
# PostgreSQL Master Credentials
########################################################

# Get PostgreSQL master credentials from Secrets Manager
data "aws_secretsmanager_secret_version" "postgres_master" {
  secret_id = local.platform_config.PG_PASSWORD_SECRET_ARN
}

locals {
  postgres_master_credentials = jsondecode(data.aws_secretsmanager_secret_version.postgres_master.secret_string)
}

########################################################
# Kubernetes Provider Configuration
########################################################

# Configure Kubernetes provider to connect to EKS cluster
data "aws_eks_cluster" "main" {
  name = local.platform_config.EKS_CLUSTER_NAME
}

data "aws_eks_cluster_auth" "main" {
  name = local.platform_config.EKS_CLUSTER_NAME
}

provider "kubernetes" {
  # Use proxy when running locally, direct connection in CI/CD
  host = var.use_local_proxy ? "http://localhost:8080" : data.aws_eks_cluster.main.endpoint

  # Only use these for direct EKS connection (CI/CD in VPC)
  cluster_ca_certificate = var.use_local_proxy ? null : base64decode(data.aws_eks_cluster.main.certificate_authority[0].data)
  token                  = var.use_local_proxy ? null : data.aws_eks_cluster_auth.main.token
}

provider "helm" {
  kubernetes = {
    # Use proxy when running locally, direct connection in CI/CD
    host = var.use_local_proxy ? "http://localhost:8080" : data.aws_eks_cluster.main.endpoint

    # Only use these for direct EKS connection (CI/CD in VPC)
    cluster_ca_certificate = var.use_local_proxy ? null : base64decode(data.aws_eks_cluster.main.certificate_authority[0].data)
    token                  = var.use_local_proxy ? null : data.aws_eks_cluster_auth.main.token
  }
}

provider "postgresql" {
  # Use local proxy or direct connection based on variable
  host     = var.use_local_proxy ? "localhost" : local.platform_config.PG_WRITER_ENDPOINT
  port     = var.use_local_proxy ? 5432 : local.platform_config.PG_PORT
  database = local.platform_config.PG_DATABASE
  username = local.postgres_master_credentials.username
  password = local.postgres_master_credentials.password
  sslmode  = var.use_local_proxy ? "disable" : "require"

  # Connection settings
  connect_timeout = 15
  superuser       = false
}

########################################################
# Kubernetes Resources
########################################################

module "kubernetes" {
  source = "../../modules/kubernetes"

  # ConfigMap configuration
  namespace          = var.kubernetes_namespace
  configuration_data = local.platform_config

  # External Secrets Operator configuration
  external_secrets_service_account_role_arn = try(local.platform_config.EXTERNAL_SECRETS_ROLE_ARN, "")

  # AWS Load Balancer Controller configuration
  aws_load_balancer_controller_service_account_role_arn = try(local.platform_config.AWS_LOAD_BALANCER_CONTROLLER_ROLE_ARN, "")
  cluster_name                                          = local.platform_config.EKS_CLUSTER_NAME
  aws_region                                            = var.aws_region
  vpc_id                                                = local.platform_config.VPC_ID

  # OTEL Collectors configuration
  otel_chart_path         = var.otel_chart_path
  otel_collector_role_arn = try(local.platform_config.OTEL_COLLECTOR_ROLE_ARN, "")
}

########################################################
# PostgreSQL Administrative Setup
########################################################

module "postgres_admin_setup" {
  count = var.create_database_resources ? 1 : 0

  source = "../../modules/postgres-admin-setup"

  # Connection configuration
  postgres_host           = local.platform_config.PG_WRITER_ENDPOINT
  postgres_port           = local.platform_config.PG_PORT
  postgres_admin_username = local.postgres_master_credentials.username
  postgres_admin_password = local.postgres_master_credentials.password

  # LiteLLM secret configuration
  litellm_secret_name = local.platform_config.LITELLM_SECRET_NAME

  # AWS configuration for secrets
  name_prefix           = "${var.environment}-${var.project_name}"
  common_tags           = local.common_tags
  enable_kms_encryption = local.platform_config.KMS_KEY_ARN != null
  kms_key_arn           = local.platform_config.KMS_KEY_ARN
}
