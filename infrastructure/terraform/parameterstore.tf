# AWS SSM Parameter Store for configuration.
# Since the cluster doesn't have public access & the bastion / VPC gets created with the cluster,
# we opted to store the outputs we need in parameter store (just configs, no secrets) and use an external secrets operator (ESO)
# which is managed by Argo to pull it down into the cluster when the user finishes the Argo bootstrap. 
# Without this approach, there's a chicken / egg problem since we can't install the secret 
# via terraform directly (no public endpoint & no VPC / bastion to run the command from.)

locals {
  # Common tags for all parameters
  parameter_tags = {
    Environment = var.environment
    Terraform   = "true"
    Service     = "agentic-platform"
  }
  
  # Base path for all parameters
  parameter_base_path = "/agentic-platform/config"
}

# Single parameter store with all configuration values in a flat structure
resource "aws_ssm_parameter" "agentic_platform_config" {
  name        = "${local.parameter_base_path}/${var.environment}"
  description = "All configuration values for the Agentic Platform"
  type        = "String"
  value       = jsonencode({
    # Infrastructure values
    VPC_ID                = aws_vpc.main.id
    EKS_CLUSTER_NAME      = aws_eks_cluster.main.name
    EKS_CLUSTER_ID        = aws_eks_cluster.main.id
    EKS_CLUSTER_ENDPOINT  = aws_eks_cluster.main.endpoint
    EKS_NODE_GROUP_ID     = aws_eks_node_group.main.id
    AWS_DEFAULT_REGION    = data.aws_region.current.name
    KMS_KEY_ARN           = var.enable_kms_encryption ? aws_kms_key.main[0].arn : null
    KMS_KEY_ID            = var.enable_kms_encryption ? aws_kms_key.main[0].key_id : null
    KMS_KEY_ALIAS         = var.enable_kms_encryption ? aws_kms_alias.main[0].name : null
    ENVIRONMENT           = var.environment
    
    # Cognito values
    COGNITO_USER_POOL_ID              = aws_cognito_user_pool.main.id
    COGNITO_USER_POOL_ARN             = aws_cognito_user_pool.main.arn
    COGNITO_USER_CLIENT_ID            = aws_cognito_user_pool_client.web_client.id
    COGNITO_M2M_CLIENT_ID             = aws_cognito_user_pool_client.m2m_client.id
    COGNITO_IDENTITY_POOL_ID          = aws_cognito_identity_pool.main.id
    COGNITO_DOMAIN                    = var.use_custom_domain && var.domain_name != "" ? "https://${var.environment}.${var.domain_name}" : "https://${aws_cognito_user_pool_domain.main.domain}.auth.${var.aws_region}.amazoncognito.com"
    COGNITO_SUPER_ADMIN_GROUP_NAME    = aws_cognito_user_group.super_admin.name
    COGNITO_PLATFORM_ADMIN_GROUP_NAME = aws_cognito_user_group.platform_admin.name
    COGNITO_PLATFORM_USER_GROUP_NAME  = aws_cognito_user_group.platform_user.name
    OAUTH_TOKEN_ENDPOINT              = "${var.use_custom_domain && var.domain_name != "" ? "https://${var.environment}.${var.domain_name}" : "https://${aws_cognito_user_pool_domain.main.domain}.auth.${var.aws_region}.amazoncognito.com"}/oauth2/token"
    M2M_CREDENTIALS_SECRET_ARN        = aws_secretsmanager_secret.m2m_credentials.arn
    
    # Database values
    PG_WRITER_ENDPOINT            = aws_rds_cluster.postgres.endpoint
    PG_READER_ENDPOINT            = aws_rds_cluster.postgres.reader_endpoint
    POSTGRES_CLUSTER_ID           = aws_rds_cluster.postgres.id
    PG_PORT                       = aws_rds_cluster.postgres.port
    PG_DATABASE                   = aws_rds_cluster.postgres.database_name
    POSTGRES_MASTER_USERNAME      = aws_rds_cluster.postgres.master_username
    PG_USER                       = var.postgres_iam_username
    PG_READ_ONLY_USER             = var.postgres_iam_username
    PG_PASSWORD_SECRET_ARN           = aws_rds_cluster.postgres.master_user_secret[0].secret_arn
    POSTGRES_SECURITY_GROUP_ID    = aws_security_group.postgres.id
    POSTGRES_PARAMETER_GROUP_NAME = aws_rds_cluster_parameter_group.postgres.name
    POSTGRES_BACKUP_VAULT_NAME    = aws_backup_vault.postgres.name
    POSTGRES_SNS_TOPIC_ARN        = aws_sns_topic.postgres_events.arn
    
    # Service endpoints
    REDIS_HOST                   = aws_elasticache_replication_group.redis_ratelimit.primary_endpoint_address
    REDIS_PORT                   = 6379
    REDIS_PASSWORD_SECRET_ARN    = aws_secretsmanager_secret.redis_auth.arn
    OPENSEARCH_ENDPOINT          = aws_opensearch_domain.observability.endpoint
    OPENSEARCH_DASHBOARD_ENDPOINT = aws_opensearch_domain.observability.dashboard_endpoint
    
    # IAM roles
    LLM_GATEWAY_ROLE_ARN                = aws_iam_role.llm_gateway_role.arn
    MEMORY_GATEWAY_ROLE_ARN             = aws_iam_role.memory_gateway_role.arn
    RETRIEVAL_GATEWAY_ROLE_ARN          = aws_iam_role.retrieval_gateway_role.arn
    OTEL_COLLECTOR_ROLE_ARN             = aws_iam_role.otel_collector_role.arn
    AWS_LOAD_BALANCER_CONTROLLER_ROLE_ARN = aws_iam_role.aws_load_balancer_controller.arn
    EXTERNAL_SECRETS_ROLE_ARN           = aws_iam_role.external_secrets_role.arn
    
    # Other resources
    KNOWLEDGE_BASE_ID        = module.bedrock.default_kb_identifier
    DYNAMODB_USAGE_PLANS_TABLE   = aws_dynamodb_table.usage_plans.name
    DYNAMODB_USAGE_LOGS_TABLE    = aws_dynamodb_table.usage_logs.name
    
    # EKS addons values
    CLUSTER_NAME                      = aws_eks_cluster.main.name
    REGION                            = data.aws_region.current.name
    LOAD_BALANCER_CONTROLLER_ROLE_ARN = aws_iam_role.aws_load_balancer_controller.arn
  })
  tags = local.parameter_tags
}
