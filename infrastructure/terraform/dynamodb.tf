resource "aws_dynamodb_table" "usage_plans" {
  name             = "${local.name_prefix}usage-plans"
  billing_mode     = "PAY_PER_REQUEST"
  # --- Use the id as the hash key to minimize hot spotting.
  hash_key         = "entity_id"  # Example: API_KEY=<hash>, USER=<uuid>
  range_key        = "entity_type" # Example: API_KEY, USER, etc.

  stream_enabled   = true
  stream_view_type = "NEW_AND_OLD_IMAGES"

  # --- Attribute Definitions ---
  attribute {
    name = "entity_id"
    type = "S"
  }
  
  attribute {
    name = "entity_type"
    type = "S"
  }
  
  # GSI for tenant_id lookup
  attribute {
    name = "tenant_id"
    type = "S"
  }
  
  global_secondary_index {
    name            = "tenant_index"
    hash_key        = "tenant_id"
    projection_type = "ALL"
  }

  # --- Other Settings ---
  server_side_encryption {
    enabled     = true
    kms_key_arn = var.enable_kms_encryption ? aws_kms_key.main[0].arn : null
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = merge(
    local.common_tags,
    {
      Name        = "UsagePlans"
      Description = "Usage plan management for LLM Gateway"
    }
  )
}

resource "aws_dynamodb_table" "usage_logs" {
  name           = "${local.name_prefix}usage-logs"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "tenant_id"
  range_key      = "usage_id"
  stream_enabled = true
  stream_view_type = "NEW_IMAGE"  # For exporting to S3

  attribute {
    name = "tenant_id"
    type = "S"
  }

  attribute {
    name = "usage_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "N"
  }

  global_secondary_index {
    name               = "tenant_timestamp_index"
    hash_key          = "tenant_id"
    range_key         = "timestamp"
    projection_type   = "ALL"
  }

  ttl {
    attribute_name = "ttl"
    enabled       = true
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = var.enable_kms_encryption ? aws_kms_key.main[0].arn : null
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = merge(
    local.common_tags,
    {
      Name        = "UsageLogs" 
      Description = "API usage tracking for LLM Gateway"
    }
  )
}