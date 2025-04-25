# Redis Security Group
resource "aws_security_group" "redis_ratelimit" {
  # checkov:skip=CKV_AWS_23: All security group rules have descriptions
  # checkov:skip=CKV_AWS_382: Egress is intentionally restricted to VPC CIDR only
  name        = "${local.name_prefix}redis-ratelimit-sg"
  description = "Security group for Redis rate limiting cluster"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "Redis from VPC"
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.main.cidr_block]
  }

  egress {
    description = "Redis to VPC services only"
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.main.cidr_block]  // Restrict to VPC CIDR only
  }

  tags = local.common_tags
}

# ElastiCache subnet group
resource "aws_elasticache_subnet_group" "redis_ratelimit" {
  name       = "${local.name_prefix}ratelimit"
  subnet_ids = [aws_subnet.private_1.id, aws_subnet.private_2.id]
  
  tags = local.common_tags
}

# Add parameter group
resource "aws_elasticache_parameter_group" "redis_ratelimit" {
  family = "redis7"
  name   = "${local.name_prefix}redis-ratelimit"
  
  tags = local.common_tags
}

# Add Secrets Manager resources for Redis auth
resource "random_password" "redis_auth_token" {
  length = 32
  special = false  # ElastiCache auth tokens can only contain alphanumeric characters
}

resource "aws_secretsmanager_secret" "redis_auth" {
  # checkov:skip=CKV2_AWS_57: As a sample, its a bit heavy handed to rotate the secret. This is called out in the readme. 
  # checkov:skip=CKV_AWS_149: KMS key is conditionally used based on var.enable_kms_encryption
  name          = "${local.name_prefix}redis-auth-${local.suffix}"
  description   = "Auth token for Redis rate limiting cluster"
  kms_key_id    = var.enable_kms_encryption ? aws_kms_key.main[0].arn : null
  
  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "redis_auth" {
  secret_id     = aws_secretsmanager_secret.redis_auth.id
  secret_string = random_password.redis_auth_token.result
}

# Modify the replication group configuration
resource "aws_elasticache_replication_group" "redis_ratelimit" {
  # checkov:skip=CKV_AWS_31: Using IAM authentication instead of auth token
  # checkov:skip=CKV_AWS_191: KMS key is conditionally used based on var.enable_kms_encryption
  replication_group_id       = "${local.name_prefix}ratelimitgid"
  description               = "Redis cluster for rate limiting in ${var.stack_name}"
  node_type                 = "cache.t4g.micro"
  port                      = 6379
  engine_version           = "7.0"
  parameter_group_name     = aws_elasticache_parameter_group.redis_ratelimit.name
  automatic_failover_enabled = true
  multi_az_enabled         = true
  num_cache_clusters       = 2

  subnet_group_name    = aws_elasticache_subnet_group.redis_ratelimit.name
  security_group_ids   = [aws_security_group.redis_ratelimit.id]
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  kms_key_id               = var.enable_kms_encryption ? aws_kms_key.main[0].arn : null

  auth_token = random_password.redis_auth_token.result

  auto_minor_version_upgrade = true
  maintenance_window        = "mon:03:00-mon:04:00"
  snapshot_window          = "02:00-03:00"
  snapshot_retention_limit = var.environment == "prod" ? 7 : 1

  tags = local.common_tags
}

# Modify the IAM policy to include Secrets Manager access instead of ElastiCache IAM auth
resource "aws_iam_policy" "redis_connect" {
  name        = "${local.name_prefix}redis-connect"
  description = "Policy to allow connection to Redis cluster and access auth token"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_secretsmanager_secret.redis_auth.arn
        ]
      }
    ]
  })
}
