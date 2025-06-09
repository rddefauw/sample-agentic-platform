# Common resource identifier

output "kms_key_arn" {
  description = "ARN of the KMS key used for encryption"
  value       = var.enable_kms_encryption ? aws_kms_key.main[0].arn : null
}

output "kms_key_id" {
  description = "ID of the KMS key used for encryption"
  value       = var.enable_kms_encryption ? aws_kms_key.main[0].key_id : null
}

output "kms_key_alias" {
  description = "Alias of the KMS key used for encryption"
  value       = var.enable_kms_encryption ? aws_kms_alias.main[0].name : null
}

########################################################
# VPC Outputs
########################################################

output "vpc_id" {
  description = "The ID of the VPC"
  value       = aws_vpc.main.id
}

########################################################
# Observability Stack Outputs
########################################################


output "opensearch_endpoint" {
  description = "OpenSearch domain endpoint"
  value       = aws_opensearch_domain.observability.endpoint
}

output "opensearch_dashboard_endpoint" {
  description = "OpenSearch dashboard endpoint"
  value       = aws_opensearch_domain.observability.dashboard_endpoint
}

# EKS Cluster Outputs
output "eks_cluster_id" {
  description = "The name of the EKS cluster"
  value       = aws_eks_cluster.main.id
}

output "eks_cluster_name" {
  description = "The name of the EKS cluster"
  value       = aws_eks_cluster.main.name
}

output "eks_cluster_endpoint" {
  description = "The endpoint for the EKS cluster API server"
  value       = aws_eks_cluster.main.endpoint
}

output "eks_node_group_id" {
  description = "The ID of the EKS node group"
  value       = aws_eks_node_group.main.id
}

output "eks_addons_required_values" {
  description = "Required values for EKS addons"
  value = {
    cluster_name                      = aws_eks_cluster.main.name
    vpc_id                            = aws_vpc.main.id
    region                            = data.aws_region.current.name
    load_balancer_controller_role_arn = aws_iam_role.aws_load_balancer_controller.arn
  }
}

output "retrieval_gateway_role_arn" {
  description = "ARN of the IAM role for Bedrock Knowledge Base operations"
  value       = aws_iam_role.retrieval_gateway_role.arn
}

output "otel_collector_role_arn" {
  description = "ARN of the IAM role for OpenTelemetry Collector"
  value       = aws_iam_role.otel_collector_role.arn
}

# Add output for the role ARN
output "memory_gateway_role_arn" {
  description = "ARN of the IAM role for Memory Gateway"
  value       = aws_iam_role.memory_gateway_role.arn
}

# Add output for the role ARN
output "llm_gateway_role_arn" {
  description = "ARN of the IAM role for LLM Gateway"
  value       = aws_iam_role.llm_gateway_role.arn
}


# NEW: Combined JSON output with all IRSA role ARNs
output "irsa_roles" {
  description = "All IAM Roles for Service Accounts (IRSA)"
  value = {
    llm_gateway       = aws_iam_role.llm_gateway_role.arn
    memory_gateway    = aws_iam_role.memory_gateway_role.arn
    bedrock_retrieval = aws_iam_role.retrieval_gateway_role.arn
    otel_collector    = aws_iam_role.otel_collector_role.arn
    secrets-operator  = aws_iam_role.external_secrets_role.arn
  }
}

output "redis_ratelimit_endpoint" {
  description = "Redis rate limiting cluster primary endpoint"
  value       = aws_elasticache_replication_group.redis_ratelimit.primary_endpoint_address
}

output "redis_ratelimit_port" {
  description = "Redis port"
  value       = 6379
}

output "redis_password_secret_arn" {
  description = "Secret ARN for Redis password"
  value       = aws_secretsmanager_secret.redis_auth.arn
}

# Outputs for PostgreSQL Aurora cluster
output "postgres_cluster_endpoint" {
  description = "Writer endpoint for the PostgreSQL cluster"
  value       = aws_rds_cluster.postgres.endpoint
}

output "postgres_reader_endpoint" {
  description = "Reader endpoint for the PostgreSQL cluster"
  value       = aws_rds_cluster.postgres.reader_endpoint
}

output "postgres_cluster_id" {
  description = "Identifier of the PostgreSQL cluster"
  value       = aws_rds_cluster.postgres.id
}

output "postgres_port" {
  description = "Port of the PostgreSQL cluster"
  value       = aws_rds_cluster.postgres.port
}

output "postgres_database_name" {
  description = "Name of the PostgreSQL database"
  value       = aws_rds_cluster.postgres.database_name
}

output "postgres_master_username" {
  description = "Master username for the PostgreSQL cluster"
  value       = aws_rds_cluster.postgres.master_username
}
output "postgres_iam_username" {
  description = "IAM username for the PostgreSQL cluster"
  value       = var.postgres_iam_username
}

output "postgres_master_secret_arn" {
  description = "ARN of the secret containing the master password"
  value       = aws_rds_cluster.postgres.master_user_secret[0].secret_arn
}

output "postgres_security_group_id" {
  description = "ID of the security group for the PostgreSQL cluster"
  value       = aws_security_group.postgres.id
}

output "postgres_parameter_group_name" {
  description = "Name of the PostgreSQL cluster parameter group"
  value       = aws_rds_cluster_parameter_group.postgres.name
}

output "postgres_backup_vault_name" {
  description = "Name of the AWS Backup vault for PostgreSQL"
  value       = aws_backup_vault.postgres.name
}

output "postgres_sns_topic_arn" {
  description = "ARN of the SNS topic for PostgreSQL events"
  value       = aws_sns_topic.postgres_events.arn
}

# Output the IAM role ARN for the AWS Load Balancer Controller
output "aws_load_balancer_controller_role_arn" {
  description = "ARN of the IAM role used by the AWS Load Balancer Controller"
  value       = aws_iam_role.aws_load_balancer_controller.arn
}

 output "knowledge_base_id" {
  value = module.bedrock.default_kb_identifier
  description = "The identifier of the default knowledge base"
}

output "usage_plans_table_name" {
  description = "DynamoDB table name for usage plans"
  value       = aws_dynamodb_table.usage_plans.name
}

output "usage_logs_table_name" {
  description = "DynamoDB table name for usage logs"
  value       = aws_dynamodb_table.usage_logs.name
}

output "cognito_user_pool_id" {
  value       = aws_cognito_user_pool.main.id
  description = "ID of the Cognito User Pool"
}

output "cognito_user_pool_arn" {
  value       = aws_cognito_user_pool.main.arn
  description = "ARN of the Cognito User Pool"
}

output "cognito_user_client_id" {
  value       = aws_cognito_user_pool_client.web_client.id
  description = "ID of the Cognito User Pool Web Client"
}

output "cognito_identity_pool_id" {
  value       = aws_cognito_identity_pool.main.id
  description = "ID of the Cognito Identity Pool"
}

output "cognito_domain" {
  value       = var.use_custom_domain && var.domain_name != "" ? "https://${var.environment}.${var.domain_name}" : "https://${aws_cognito_user_pool_domain.main.domain}.auth.${var.aws_region}.amazoncognito.com"
  description = "Domain URL for authentication"
}

output "cognito_super_admin_group_name" {
  value       = aws_cognito_user_group.super_admin.name
  description = "Name of the Cognito super admin user group"
}

output "cognito_platform_admin_group_name" {
  value       = aws_cognito_user_group.platform_admin.name
  description = "Name of the Cognito platform admin user group"
}

output "cognito_platform_user_group_name" {
  value       = aws_cognito_user_group.platform_user.name
  description = "Name of the Cognito platform user group"
}

output "cognito_m2m_client_id" {
  value       = aws_cognito_user_pool_client.m2m_client.id
  description = "ID of the machine-to-machine client"
}

output "m2m_credentials_secret_arn" {
  value       = aws_secretsmanager_secret.m2m_credentials.arn
  description = "ARN of the secret containing M2M credentials"
}

output "oauth_token_endpoint" {
  value       = "${var.use_custom_domain && var.domain_name != "" ? "https://${var.environment}.${var.domain_name}" : "https://${aws_cognito_user_pool_domain.main.domain}.auth.${var.aws_region}.amazoncognito.com"}/oauth2/token"
  description = "OAuth2 token endpoint for all authentication flows"
}

