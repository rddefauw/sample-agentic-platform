# Security group for OpenSearch
resource "aws_security_group" "opensearch" {
  # checkov:skip=CKV2_AWS_5: "This security group is attached to the OpenSearch domain in the vpc_options block. Checkov false positive."
  # checkov:skip=CKV_AWS_382: "OpenSearch requires outbound access for cluster communication and AWS API integration"
  name_prefix = "${local.name_prefix}opensearch-sg"
  vpc_id      = aws_vpc.main.id
  description = "Security group for OpenSearch domain logs-agentic-search"

  # Keep it locked down by default - you can add specific ingress rules later
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    self        = true
    description = "Allow HTTPS traffic within the security group for OpenSearch cluster communication"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic from OpenSearch cluster"
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}opensearch-sg"
    }
  )
}

# Create IAM role for OpenSearch master user
resource "aws_iam_role" "opensearch_master_user" {
  name = "${local.name_prefix}opensearch-master-user"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"  # Allow account root to assume
        }
      }
    ]
  })

  tags = local.common_tags
}

# Reference the role that's assumed to exist already
data "aws_iam_role" "opensearch_service_role" {
  name = "AWSServiceRoleForAmazonOpenSearchService"
}


# OpenSearch Domain
resource "aws_opensearch_domain" "observability" {
  # checkov:skip=CKV2_AWS_52: "Fine-grained access control is implemented through AWS IAM roles and policies instead of internal user database"
  domain_name    = "observability"
  engine_version = "OpenSearch_2.17"

  cluster_config {
    instance_type          = "t3.small.search"
    instance_count         = 2  # Changed to 2 for high availability
    zone_awareness_enabled = true  # Enable zone awareness for HA
    
    # Add dedicated master nodes
    dedicated_master_enabled = true
    dedicated_master_type   = "t3.small.search"
    dedicated_master_count  = 3  # Recommended odd number for quorum

    # Enable warm storage if needed
    warm_enabled = false  # Set to true if you need warm storage
  }

  vpc_options {
    subnet_ids         = [aws_subnet.private_1.id, aws_subnet.private_2.id]  # Use both private subnets for HA
    security_group_ids = [aws_security_group.opensearch.id]
  }

  ebs_options {
    ebs_enabled = true
    volume_size = 10
    volume_type = "gp3"
    # Add IOPS and throughput for better performance
    iops        = 3000
    throughput  = 125
  }

  encrypt_at_rest {
    enabled    = true
    kms_key_id = var.enable_kms_encryption ? aws_kms_key.main[0].arn : null
  }

  node_to_node_encryption {
    enabled = true
  }

  domain_endpoint_options {
    enforce_https       = true
    tls_security_policy = "Policy-Min-TLS-1-2-2019-07"
  }

  # Enable automated snapshot
  snapshot_options {
    automated_snapshot_start_hour = 23  # 11 PM UTC
  }

  # Enable logging
  log_publishing_options {
    cloudwatch_log_group_arn = aws_cloudwatch_log_group.opensearch_logs.arn
    log_type                 = "INDEX_SLOW_LOGS"
    enabled                  = true
  }

  log_publishing_options {
    cloudwatch_log_group_arn = aws_cloudwatch_log_group.opensearch_logs.arn
    log_type                 = "SEARCH_SLOW_LOGS"
    enabled                  = true
  }

  # Add audit logging to fix CKV_AWS_317
  log_publishing_options {
    cloudwatch_log_group_arn = aws_cloudwatch_log_group.opensearch_logs.arn
    log_type                 = "AUDIT_LOGS"
    enabled                  = true
  }

  advanced_security_options {
    enabled                        = true
    internal_user_database_enabled = false
    master_user_options {
      master_user_arn = aws_iam_role.opensearch_master_user.arn
    }
    anonymous_auth_enabled         = false
  }

  access_policies = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = [
            aws_iam_role.opensearch_master_user.arn,
            aws_iam_role.opensearch_readonly.arn
          ]
        }
        Action = "es:*"
        Resource = "arn:aws:es:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:domain/logs-agentic-search/*"
      }
    ]
  })

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}opensearch"
    }
  )

  # Use a simple depends_on without the missing resource
  depends_on = [
    aws_cloudwatch_log_resource_policy.opensearch_logs
  ]
}

# Add to KMS key policy if encryption is enabled
resource "aws_kms_key_policy" "opensearch" {
  count  = var.enable_kms_encryption ? 1 : 0
  key_id = aws_kms_key.main[0].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat(
      jsondecode(aws_kms_key.main[0].policy).Statement,
      [
        {
          Sid    = "Allow OpenSearch Service"
          Effect = "Allow"
          Principal = {
            Service = "es.amazonaws.com"
          }
          Action = [
            "kms:Encrypt",
            "kms:Decrypt",
            "kms:ReEncrypt*",
            "kms:GenerateDataKey*",
            "kms:Describe*"
          ]
          Resource = "*"
        }
      ]
    )
  })
}

# CloudWatch Log Group for OpenSearch logs
resource "aws_cloudwatch_log_group" "opensearch_logs" {
  # checkov:skip=CKV_AWS_158: KMS encryption is conditionally enabled based on var.enable_kms_encryption
  name              = "/aws/opensearch/${local.name_prefix}logs"
  retention_in_days = 365
  kms_key_id        = var.enable_kms_encryption ? aws_kms_key.main[0].arn : null

  tags = local.common_tags
}

# CloudWatch Logs resource policy for OpenSearch
resource "aws_cloudwatch_log_resource_policy" "opensearch_logs" {
  policy_name     = "${local.name_prefix}opensearch-logs-policy"
  policy_document = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "es.amazonaws.com"
        }
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:PutLogEventsBatch"
        ]
        Resource = "${aws_cloudwatch_log_group.opensearch_logs.arn}:*"
      }
    ]
  })
}

# Add IAM role for OpenSearch logging
resource "aws_iam_role" "opensearch_log_publishing" {
  name = "${local.name_prefix}opensearch-log-publishing"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "es.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# IAM policy for OpenSearch logging
resource "aws_iam_role_policy" "opensearch_log_publishing" {
  name = "${local.name_prefix}opensearch-log-publishing"
  role = aws_iam_role.opensearch_log_publishing.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:PutLogEventsBatch"
        ]
        Resource = "${aws_cloudwatch_log_group.opensearch_logs.arn}:*"
      }
    ]
  })
}

# Example: Read-only role for applications
resource "aws_iam_role" "opensearch_readonly" {
  name = "${local.name_prefix}opensearch-readonly"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = ["ec2.amazonaws.com", "lambda.amazonaws.com"]  # Allow EC2 and Lambda to assume
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "opensearch_readonly" {
  name = "${local.name_prefix}opensearch-readonly-policy"
  role = aws_iam_role.opensearch_readonly.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "es:ESHttpGet",
          "es:ESHttpHead",
          "es:ESHttpPost"  # For search operations
        ]
        Resource = "${aws_opensearch_domain.observability.arn}/*"
      }
    ]
  })
}