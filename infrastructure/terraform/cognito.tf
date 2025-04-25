########################################################
# Auth Module - AWS Cognito
########################################################

resource "aws_cognito_user_pool" "main" {
  name = "${local.name_prefix}user-pool"
  
  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]
  mfa_configuration        = "OFF"
  
  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_numbers   = true
    require_symbols   = true
    require_uppercase = true
    temporary_password_validity_days = 7
  }
  
  admin_create_user_config {
    allow_admin_create_user_only = false
  }
  
  schema {
    attribute_data_type      = "String"
    developer_only_attribute = false
    mutable                  = true
    name                     = "email"
    required                 = true
    
    string_attribute_constraints {
      min_length = 1
      max_length = 256
    }
  }
  
  email_configuration {
    email_sending_account = "COGNITO_DEFAULT"
  }
  
  verification_message_template {
    default_email_option = "CONFIRM_WITH_CODE"
    email_subject        = "Your verification code"
    email_message        = "Your verification code is {####}"
  }
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}user-pool"
    }
  )
}

# App client for web applications
resource "aws_cognito_user_pool_client" "web_client" {
  name                         = "${local.name_prefix}web-client"
  user_pool_id                 = aws_cognito_user_pool.main.id
  generate_secret              = false
  refresh_token_validity       = 30
  prevent_user_existence_errors = "ENABLED"
  explicit_auth_flows = [
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_PASSWORD_AUTH"
  ]
  
  callback_urls        = var.use_custom_domain ? ["https://${var.environment}.${var.domain_name}/callback", "http://localhost:3000/callback"] : ["https://${aws_cognito_user_pool_domain.main.domain}.auth.${var.aws_region}.amazoncognito.com/oauth2/idpresponse", "http://localhost:3000/callback"]
  logout_urls          = var.use_custom_domain ? ["https://${var.environment}.${var.domain_name}/logout", "http://localhost:3000/logout"] : ["https://${aws_cognito_user_pool_domain.main.domain}.auth.${var.aws_region}.amazoncognito.com/logout", "http://localhost:3000/logout"]
  allowed_oauth_flows  = ["code", "implicit"]
  allowed_oauth_scopes = ["email", "openid", "profile"]
  supported_identity_providers = ["COGNITO"]
}

# Identity Pool for federated identities (optional)
resource "aws_cognito_identity_pool" "main" {
  identity_pool_name               = "${local.name_prefix}identity-pool"
  allow_unauthenticated_identities = false
  
  cognito_identity_providers {
    client_id               = aws_cognito_user_pool_client.web_client.id
    provider_name           = "cognito-idp.${var.aws_region}.amazonaws.com/${aws_cognito_user_pool.main.id}"
    server_side_token_check = false
  }
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}identity-pool"
    }
  )
}

# IAM roles for the Identity Pool
resource "aws_iam_role" "authenticated" {
  name = "${local.name_prefix}cognito-authenticated"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = "cognito-identity.amazonaws.com"
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "cognito-identity.amazonaws.com:aud" = aws_cognito_identity_pool.main.id
          }
          "ForAnyValue:StringLike" = {
            "cognito-identity.amazonaws.com:amr" = "authenticated"
          }
        }
      }
    ]
  })
  
  tags = local.common_tags
}

# Basic permissions for authenticated users - FIXED VERSION
resource "aws_iam_role_policy" "authenticated" {
  name = "${local.name_prefix}authenticated-policy"
  role = aws_iam_role.authenticated.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "mobileanalytics:PutEvents"
        ]
        Resource = "*"
        Condition = {
          "StringLike": {
            "mobileanalytics:app-id": var.use_custom_domain ? [
              "com.${var.domain_name}.*",
              "${var.environment}.${var.domain_name}.*"
            ] : [
              "${local.name_prefix}*",
              "${var.environment}-${random_string.suffix.result}*"
            ]
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "cognito-sync:ListRecords",
          "cognito-sync:GetIdentityPoolConfiguration",
          "cognito-sync:GetDataset"
        ]
        Resource = [
          "arn:aws:cognito-sync:${var.aws_region}:${data.aws_caller_identity.current.account_id}:identitypool/${aws_cognito_identity_pool.main.id}/identity/*/dataset/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "cognito-sync:UpdateRecords",
          "cognito-sync:RefreshDataset",
          "cognito-sync:DescribeDataset",
          "cognito-sync:DeleteDataset"
        ]
        Resource = [
          "arn:aws:cognito-sync:${var.aws_region}:${data.aws_caller_identity.current.account_id}:identitypool/${aws_cognito_identity_pool.main.id}/identity/*/dataset/*"
        ]
        Condition = {
          "StringEquals": {
            "cognito-identity.amazonaws.com:sub": ["${data.aws_caller_identity.current.user_id}"]
          }
        }
      }
    ]
  })
}

# Connect the Identity Pool with the IAM roles
resource "aws_cognito_identity_pool_roles_attachment" "main" {
  identity_pool_id = aws_cognito_identity_pool.main.id
  
  roles = {
    "authenticated" = aws_iam_role.authenticated.arn
  }
}

# Create a custom domain for the Cognito User Pool (optional)
resource "aws_cognito_user_pool_domain" "main" {
  domain       = "${var.environment}-auth-${random_string.suffix.result}"
  user_pool_id = aws_cognito_user_pool.main.id
}

# Add a resource server for API authorization
resource "aws_cognito_resource_server" "api" {
  name         = "${local.name_prefix}api-resource"
  identifier   = var.use_custom_domain ? "api.${var.environment}.${var.domain_name}" : "api.${var.environment}.${random_string.suffix.result}"
  user_pool_id = aws_cognito_user_pool.main.id
  
  scope {
    scope_name        = "read"
    scope_description = "Read access to the API"
  }
  
  scope {
    scope_name        = "write"
    scope_description = "Write access to the API"
  }
  
  scope {
    scope_name        = "admin"
    scope_description = "Admin access to the API"
  }
}

# Create user groups for platform access levels
resource "aws_cognito_user_group" "super_admin" {
  name         = "super_admin"
  user_pool_id = aws_cognito_user_pool.main.id
  description  = "Super administrators with full system access"
  precedence   = 1  # Highest precedence
}

resource "aws_cognito_user_group" "platform_admin" {
  name         = "platform_admin"
  user_pool_id = aws_cognito_user_pool.main.id
  description  = "Platform administrators with administrative access"
  precedence   = 2  # Medium precedence
}

resource "aws_cognito_user_group" "platform_user" {
  name         = "platform_user"
  user_pool_id = aws_cognito_user_pool.main.id
  description  = "Regular platform users with standard access"
  precedence   = 3  # Lowest precedence
}

# M2M client for service-to-service communication
resource "aws_cognito_user_pool_client" "m2m_client" {
  name                           = "${local.name_prefix}m2m-client-${local.suffix}"
  user_pool_id                   = aws_cognito_user_pool.main.id
  generate_secret                = true # Required for client credentials flow
  refresh_token_validity         = 30
  access_token_validity          = 1440  # 24 hours token validity
  id_token_validity              = 1440  # 24 hours token validity 
  prevent_user_existence_errors  = "ENABLED"
  token_validity_units {
    access_token  = "minutes"
    id_token      = "minutes"
    refresh_token = "days"
  }
  
  # Client credentials is the key flow for M2M
  allowed_oauth_flows  = ["client_credentials"]
  
  # IMPORTANT: Add this parameter
  allowed_oauth_flows_user_pool_client = true
  
  # Use the existing resource server's scopes
  allowed_oauth_scopes = [
    "${aws_cognito_resource_server.api.identifier}/read",
    "${aws_cognito_resource_server.api.identifier}/write",
  ]
  supported_identity_providers = ["COGNITO"]
}

# Store M2M credentials in Secrets Manager for secure access
resource "aws_secretsmanager_secret" "m2m_credentials" {
  # checkov:skip=CKV2_AWS_57: As a sample, its a bit heavy handed to rotate the secret. This is called out in the readme. 
  # checkov:skip=CKV_AWS_149: KMS key is conditionally used based on var.enable_kms_encryption
  name        = "${local.name_prefix}m2m-credentials-${local.suffix}"
  description = "Machine-to-machine client credentials for service auth"
  kms_key_id  = var.enable_kms_encryption ? aws_kms_key.main[0].arn : null
  
  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "m2m_credentials" {
  secret_id     = aws_secretsmanager_secret.m2m_credentials.id
  secret_string = jsonencode({
    client_id     = aws_cognito_user_pool_client.m2m_client.id
    client_secret = aws_cognito_user_pool_client.m2m_client.client_secret
    token_url     = "${var.use_custom_domain && var.domain_name != "" ? "https://${var.environment}.${var.domain_name}" : "https://${aws_cognito_user_pool_domain.main.domain}.auth.${var.aws_region}.amazoncognito.com"}/oauth2/token"
    scopes        = join(" ", [
      "${aws_cognito_resource_server.api.identifier}/read",
      "${aws_cognito_resource_server.api.identifier}/write",
    ])
  })
}
