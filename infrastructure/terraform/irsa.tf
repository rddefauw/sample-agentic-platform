# IAM Roles for Service Accounts (IRSA)
# Enables Kubernetes service accounts to assume IAM roles

#################################################################
# IRSA setup for Bedrock Knowledge Base operations
#################################################################




resource "aws_iam_policy" "bedrock_retrieval_policy" {
  name        = "${local.name_prefix}bedrock-retrieval-policy"
  description = "Policy to allow Bedrock Knowledge Base operations"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:Retrieve",
          "bedrock:RetrieveAndGenerate",
          "bedrock:ListKnowledgeBases",
          "bedrock:GetKnowledgeBase"
        ]
        Resource = [
          # Allow operations on all knowledge bases in the account across all regions
          "arn:aws:bedrock:*:${data.aws_caller_identity.current.account_id}:knowledge-base/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel"  # Required for combining retrieval with generation
        ]
        Resource = [
          # Allow access to all models in the account across all regions (needed for generation)
          "arn:aws:bedrock:*:${data.aws_caller_identity.current.account_id}:model/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:ListKnowledgeBases"
        ]
        Resource = [
          # This is a list operation that requires a broader scope
          "arn:aws:bedrock:*:${data.aws_caller_identity.current.account_id}:*"
        ]
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role" "retrieval_gateway_role" {
  name = "${local.name_prefix}retrieval-gateway-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/${replace(aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")}"
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "${replace(aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")}:sub": "system:serviceaccount:default:retrieval-gateway-sa"
          }
        }
      }
    ]
  })

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}memory-gateway-role"
    }
  )
}

resource "aws_iam_role_policy_attachment" "bedrock_retrieval_attachment" {
  policy_arn = aws_iam_policy.bedrock_retrieval_policy.arn
  role       = aws_iam_role.retrieval_gateway_role.name
}

#################################################################
# IRSA for OpenTelemetry Collector with OpenSearch access
#################################################################

resource "aws_iam_policy" "otel_opensearch_policy" {
  name        = "${local.name_prefix}otel-opensearch-policy"
  description = "Policy to allow OpenTelemetry collector to access OpenSearch"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "es:ESHttpGet", 
          "es:ESHttpHead",
          "es:ESHttpPost",
          "es:ESHttpPut",
          "es:ESHttpDelete"
        ]
        Resource = [
          "${aws_opensearch_domain.observability.arn}/*"
        ]
      }
    ]
  })

  tags = local.common_tags
}

# Add CloudWatch and X-Ray permissions for the OTEL collector
resource "aws_iam_policy" "otel_cloudwatch_xray_policy" {
  name        = "${local.name_prefix}otel-cloudwatch-xray-policy"
  description = "Policy to allow OpenTelemetry collector to send telemetry to CloudWatch and X-Ray"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # CloudWatch Logs permissions
      {
        Effect = "Allow"
        Action = [
          "logs:PutLogEvents",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:DescribeLogStreams",
          "logs:DescribeLogGroups"
        ]
        Resource = [
          "arn:aws:logs:*:${data.aws_caller_identity.current.account_id}:log-group:/aws/containerinsights/*",
          "arn:aws:logs:*:${data.aws_caller_identity.current.account_id}:log-group:/aws/containerinsights/*:log-stream:*"
        ]
      },
      # CloudWatch Metrics permissions
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData"
        ]
        Resource = "*"
      },
      # X-Ray permissions
      {
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords",
          "xray:GetSamplingRules",
          "xray:GetSamplingTargets",
          "xray:GetSamplingStatisticSummaries"
        ]
        Resource = "*"
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role" "otel_collector_role" {
  name = "${local.name_prefix}otel-collector-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/${replace(aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")}"
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "${replace(aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")}:sub": "system:serviceaccount:observability:otel-collector"
          }
        }
      }
    ]
  })

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}otel-collector-role"
    }
  )
}

resource "aws_iam_role_policy_attachment" "otel_opensearch_attachment" {
  policy_arn = aws_iam_policy.otel_opensearch_policy.arn
  role       = aws_iam_role.otel_collector_role.name
}

# Attach the CloudWatch and X-Ray policy to the OTEL collector role
resource "aws_iam_role_policy_attachment" "otel_cloudwatch_xray_attachment" {
  policy_arn = aws_iam_policy.otel_cloudwatch_xray_policy.arn
  role       = aws_iam_role.otel_collector_role.name
}

########################################################
# LLM Gateway IRSA
########################################################

#################################################################
# IRSA setup for Bedrock model invocation
#################################################################
resource "aws_iam_policy" "bedrock_invoke_policy" {
  name        = "${local.name_prefix}bedrock-invoke-policy"
  description = "Policy to allow invoking Bedrock models and access Redis rate limiter"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = [
          # Allow access to all models in the account across all regions
          "arn:aws:bedrock:*:${data.aws_caller_identity.current.account_id}:model/*",
          # Allow access to all inference profiles in the account across all regions
          "arn:aws:bedrock:*:${data.aws_caller_identity.current.account_id}:inference-profile/*",
          # Allow access to AWS foundation models
          "arn:aws:bedrock:*::foundation-model/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:ListFoundationModels",
          "bedrock:GetFoundationModel"
        ]
        Resource = [
          # These are read-only list operations that require * resource
          # but we're scoping them to only foundation model related actions
          "arn:aws:bedrock:*:${data.aws_caller_identity.current.account_id}:*"
        ]
      },
      # Redis rate limiter access
      {
        Effect = "Allow",
        Action = [
          "elasticache:Connect",
           "secretsmanager:GetSecretValue"
        ],
        Resource = [
          aws_elasticache_replication_group.redis_ratelimit.arn,
          aws_secretsmanager_secret.redis_auth.arn
        ]
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_policy" "redis_access_policy" {
  name        = "${local.name_prefix}redis-access-policy"
  description = "Policy to allow access to Redis rate limiting cluster"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "elasticache:Connect",
           "secretsmanager:GetSecretValue"
        ],
        Resource = [
          aws_elasticache_replication_group.redis_ratelimit.arn,
          aws_secretsmanager_secret.redis_auth.arn
        ]
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_policy" "llm_gateway_dynamodb_policy" {
  name        = "${local.name_prefix}llm-gateway-dynamodb-policy"
  description = "Policy to allow LLM Gateway to access its DynamoDB tables"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.usage_plans.arn,
          aws_dynamodb_table.usage_logs.arn,
          # Include GSI ARNs
          "${aws_dynamodb_table.usage_logs.arn}/index/*"
        ]
      }
    ]
  })

  tags = local.common_tags
}

# LLM Gateway Service Account Role
resource "aws_iam_role" "llm_gateway_role" {
  name = "${local.name_prefix}llm-gateway-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/${replace(aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")}"
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "${replace(aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")}:sub": "system:serviceaccount:default:llm-gateway-sa"
          }
        }
      }
    ]
  })

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}llm-gateway-role"
    }
  )
}

# Attach policies to the LLM Gateway role
resource "aws_iam_role_policy_attachment" "llm_gateway_dynamodb_attachment" {
  policy_arn = aws_iam_policy.llm_gateway_dynamodb_policy.arn
  role       = aws_iam_role.llm_gateway_role.name
}

resource "aws_iam_role_policy_attachment" "llm_gateway_bedrock_attachment" {
  policy_arn = aws_iam_policy.bedrock_invoke_policy.arn
  role       = aws_iam_role.llm_gateway_role.name
}

resource "aws_iam_role_policy_attachment" "llm_gateway_redis_attachment" {
  policy_arn = aws_iam_policy.redis_access_policy.arn
  role       = aws_iam_role.llm_gateway_role.name
}

# Memory Gateway PostgreSQL Access Policy
resource "aws_iam_policy" "memory_gateway_postgres_policy" {
  name        = "${local.name_prefix}memory-gateway-postgres-policy"
  description = "Policy to allow Memory Gateway to access PostgreSQL and retrieve its password"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # Allow access to the Postgres master password secret
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          aws_rds_cluster.postgres.master_user_secret[0].secret_arn
        ]
      },
      # Allow RDS IAM authentication (if using IAM auth instead of password)
      {
        Effect = "Allow"
        Action = [ # nosemgrep: no-iam-resource-exposure
          "rds-db:connect"
        ]
        Resource = [
          "arn:aws:rds-db:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:dbuser:${aws_rds_cluster.postgres.cluster_resource_id}/*"
        ]
      }
    ]
  })

  tags = local.common_tags
}

#################################################################
# IRSA for Memory Gateway
#################################################################
resource "aws_iam_role" "memory_gateway_role" {
  name = "${local.name_prefix}memory-gateway-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/${replace(aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")}"
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "${replace(aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")}:sub": "system:serviceaccount:default:memory-gateway-sa"
          }
        }
      }
    ]
  })

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}memory-gateway-role"
    }
  )
}

# Attach policy to the Memory Gateway role
resource "aws_iam_role_policy_attachment" "memory_gateway_postgres_attachment" {
  policy_arn = aws_iam_policy.memory_gateway_postgres_policy.arn
  role       = aws_iam_role.memory_gateway_role.name
}

# Add additional policies if needed (e.g., CloudWatch logging)
resource "aws_iam_role_policy_attachment" "memory_gateway_cloudwatch_attachment" {
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
  role       = aws_iam_role.memory_gateway_role.name
}

#################################################################
# IRSA for External Secrets Operator to read from Parameter Store
#################################################################
resource "aws_iam_policy" "external_secrets_parameter_store_policy" {
  name        = "${local.name_prefix}external-secrets-parameter-store-policy"
  description = "Policy to allow External Secrets Operator to read from Parameter Store"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:GetParametersByPath",
          "ssm:DescribeParameters"
        ]
        Resource = [
          "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/*"
        ]
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role" "external_secrets_role" {
  name = "${local.name_prefix}external-secrets-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/${replace(aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")}"
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "${replace(aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")}:sub": "system:serviceaccount:external-secrets-system:external-secrets-sa"
          }
        }
      }
    ]
  })

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}external-secrets-role"
    }
  )
}

# Attach policy to the External Secrets role
resource "aws_iam_role_policy_attachment" "external_secrets_parameter_store_attachment" {
  policy_arn = aws_iam_policy.external_secrets_parameter_store_policy.arn
  role       = aws_iam_role.external_secrets_role.name
}

#################################################################
# IRSA for EBS CSI Driver
#################################################################
resource "aws_iam_role" "ebs_csi_driver_role" {
  name = "${local.name_prefix}ebs-csi-driver-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          # CHANGE THIS LINE to match your other roles:
          Federated = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/${replace(aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")}"
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "${replace(aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")}:sub" = "system:serviceaccount:kube-system:ebs-csi-controller-sa"
            "${replace(aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")}:aud" = "sts.amazonaws.com"
          }
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "ebs_csi_driver_service_account_policy" {
  role       = aws_iam_role.ebs_csi_driver_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"
}