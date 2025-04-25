# Aurora PostgreSQL Cluster with Checkov suppressions
resource "aws_rds_cluster" "postgres" {
  # checkov:skip=CKV_AWS_327: "Encryption is configurable via the enable_kms_encryption variable"
  cluster_identifier      = "${local.name_prefix}postgres"
  engine                  = "aurora-postgresql"
  engine_version          = "16.6"
  database_name           = "postgres"
  master_username         = "postgres"
  # Use Secrets Manager to manage the password instead of hardcoding it
  manage_master_user_password = true
  iam_database_authentication_enabled = true
  storage_encrypted       = true
  # KMS encryption is conditionally enabled based on var.enable_kms_encryption
  kms_key_id              = var.enable_kms_encryption ? aws_kms_key.main[0].arn : null
  backup_retention_period = 7
  preferred_backup_window = "03:00-04:00"
  preferred_maintenance_window = "sat:05:00-sat:06:00"
  skip_final_snapshot     = false
  final_snapshot_identifier = "${local.name_prefix}postgres-final-snapshot-${local.suffix}"
  
  vpc_security_group_ids = [aws_security_group.postgres.id]
  db_subnet_group_name   = aws_db_subnet_group.postgres.name

  enabled_cloudwatch_logs_exports = ["postgresql"]
  
  deletion_protection = var.postgres_deletion_protection
  copy_tags_to_snapshot = true
  
  db_cluster_parameter_group_name = aws_rds_cluster_parameter_group.postgres.name
  
  tags = merge(
    local.common_tags,
    {
      Name = "Postgres"
    }
  )
}

# Parameter group for cluster level with supported extensions
resource "aws_rds_cluster_parameter_group" "postgres" {
  name   = "${local.name_prefix}postgres-params"
  family = "aurora-postgresql16"

  parameter {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements"  # Using a supported extension
  }

  parameter {
    name  = "log_statement"
    value = "ddl"
  }
  
  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }

  tags = local.common_tags
}

resource "aws_rds_cluster_instance" "postgres" {
  # checkov:skip=CKV_AWS_354: "Performance Insights encryption is configurable via the enable_kms_encryption variable"
  count                = 2
  identifier           = "${local.name_prefix}postgres-${count.index}"
  cluster_identifier   = aws_rds_cluster.postgres.id
  instance_class       = "db.t4g.medium"
  engine               = aws_rds_cluster.postgres.engine
  engine_version       = aws_rds_cluster.postgres.engine_version

  auto_minor_version_upgrade = true
  performance_insights_enabled = true
  performance_insights_kms_key_id = var.enable_kms_encryption ? aws_kms_key.main[0].arn : null
  monitoring_interval        = 60
  monitoring_role_arn       = aws_iam_role.rds_monitoring.arn
  db_parameter_group_name    = aws_db_parameter_group.postgres.name
  
  tags = local.common_tags
}

# Instance parameter group
resource "aws_db_parameter_group" "postgres" {
  name   = "${local.name_prefix}postgres-instance-params"
  family = "aurora-postgresql16"

  tags = local.common_tags
}

# Subnet group for the cluster
resource "aws_db_subnet_group" "postgres" {
  name       = "${local.name_prefix}postgres"
  subnet_ids = [aws_subnet.private_1.id, aws_subnet.private_2.id]

  tags = local.common_tags
}

# Security group for the cluster
resource "aws_security_group" "postgres" {
  name_prefix = "${local.name_prefix}postgres-"
  vpc_id      = aws_vpc.main.id
  description = "Security group for PostgreSQL database"

  tags = local.common_tags

  lifecycle {
    create_before_destroy = true
  }
}

# Ingress rule - Allow from EKS nodes security group
resource "aws_security_group_rule" "postgres_ingress_eks_nodes" {
  type              = "ingress"
  from_port         = 5432
  to_port           = 5432
  protocol          = "tcp"
  security_group_id = aws_security_group.postgres.id
  source_security_group_id = aws_security_group.eks_nodes_sg.id
  description       = "Allow PostgreSQL traffic from EKS nodes"
}

# Egress rule
resource "aws_security_group_rule" "postgres_egress" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  security_group_id = aws_security_group.postgres.id
  cidr_blocks       = [aws_vpc.main.cidr_block]
  description       = "Allow outbound traffic only within the VPC"
}

# Add ingress rule to allow traffic from code server instance to PostgreSQL
resource "aws_security_group_rule" "postgres_ingress_bastion" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  security_group_id        = aws_security_group.postgres.id
  source_security_group_id = aws_security_group.bastion_sg.id
  description              = "Allow PostgreSQL traffic from code server instance"
}

# IAM role for RDS monitoring
resource "aws_iam_role" "rds_monitoring" {
  name = "${local.name_prefix}rds-monitoring"
  description = "Role for RDS enhanced monitoring"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })
  
  tags = local.common_tags
}

# Add policy attachment instead of using managed_policy_arns
resource "aws_iam_role_policy_attachment" "rds_monitoring_policy" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# AWS Backup Plan for PostgreSQL cluster - simplified name
resource "aws_backup_plan" "postgres" {
  name = "${local.name_prefix}pg-backup-plan"

  rule {
    rule_name         = "daily-backup"
    target_vault_name = aws_backup_vault.postgres.name
    schedule          = "cron(0 2 * * ? *)"  # Daily at 2:00 AM UTC
    
    lifecycle {
      delete_after = 35  # Keep backups for 35 days
    }
  }

  tags = local.common_tags
}

# SNS Topic for RDS Event Notifications with KMS encryption
resource "aws_sns_topic" "postgres_events" {
  name = "${local.name_prefix}postgres-events"
  kms_master_key_id = var.enable_kms_encryption ? aws_kms_key.main[0].id : "alias/aws/sns"  # Use AWS managed key if custom KMS not enabled
  
  tags = local.common_tags
}

# RDS Event Subscription - fix invalid event category
resource "aws_db_event_subscription" "postgres_events" {
  name      = "${local.name_prefix}postgres-event-subscription"
  sns_topic = aws_sns_topic.postgres_events.arn
  
  source_type = "db-cluster"
  source_ids  = [aws_rds_cluster.postgres.id]
  
  # Event categories to monitor - removing "restoration" which isn't valid for db-cluster
  event_categories = [
    "failover",
    "failure",
    "maintenance",
    "notification",
    "creation",
    "deletion",
    "configuration change"
  ]
  
  enabled = true
  tags    = local.common_tags
}

# AWS Backup Vault for PostgreSQL cluster with correct KMS key reference
resource "aws_backup_vault" "postgres" {
  # checkov:skip=CKV_AWS_166: "Optional KMS key."
  name = "${local.name_prefix}pg-vault"
  
  # Use KMS key only if enable_kms_encryption is true, otherwise use null
  # AWS will use its own encryption if we don't specify a key
  kms_key_arn = var.enable_kms_encryption ? aws_kms_key.main[0].arn : null

  force_destroy = true
  
  tags = local.common_tags
}

resource "aws_backup_selection" "postgres" {
  name         = "${local.name_prefix}pg-backup"
  iam_role_arn = aws_iam_role.backup_role.arn
  plan_id      = aws_backup_plan.postgres.id

  resources = [
    aws_rds_cluster.postgres.arn
  ]
}

# IAM Role for AWS Backup - simplified name
resource "aws_iam_role" "backup_role" {
  name = "${local.name_prefix}backup-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "backup.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# Attach AWS Backup service role policy
resource "aws_iam_role_policy_attachment" "backup_policy" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup"
  role       = aws_iam_role.backup_role.name
}

# IAM policy for RDS IAM authentication
resource "aws_iam_policy" "rds_connect_policy" {
  name        = "${local.name_prefix}rds-connect-policy"
  description = "Policy to allow IAM authentication to RDS"
  
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [ # nosemgrep: no-iam-resource-exposure
          "rds-db:connect"
        ],
        Resource = [
          "arn:aws:rds-db:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:dbuser:${aws_rds_cluster.postgres.cluster_resource_id}/*"
        ]
      }
    ]
  })
  
  tags = local.common_tags
}

# # Attach the RDS connect policy to the management instance role
# resource "aws_iam_role_policy_attachment" "management_rds_connect" {
#   policy_arn = aws_iam_policy.rds_connect_policy.arn
#   role       = aws_iam_role.management_role.name
# }
