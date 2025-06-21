########################################################
# S3 Bucket for Static Website Hosting
########################################################

resource "aws_s3_bucket" "spa_website" {
  # checkov:skip=CKV_AWS_144:Cross-region replication not required for sample website - adds unnecessary cost and complexity
  # checkov:skip=CKV_AWS_145:S3 default encryption (AES256) is sufficient for static website content, KMS not required
  # checkov:skip=CKV_AWS_21:S3 versioning disabled - website content is versioned through CI/CD and stored in Git
  # checkov:skip=CKV2_AWS_62:Event notifications not required for static website hosting - no automated processing needed
  # checkov:skip=CKV_AWS_18:Access logging not needed for sample UI.
  bucket        = "${local.name_prefix}spa-website-${local.suffix}"
  force_destroy = true

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}spa-website-${local.suffix}"
    Type = "StaticWebsite"
  })
}

resource "aws_s3_bucket_versioning" "spa_website" {
  bucket = aws_s3_bucket.spa_website.id
  versioning_configuration {
    status = "Suspended"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "spa_website" {
  bucket = aws_s3_bucket.spa_website.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

########################################################
# S3 Bucket Lifecycle Configuration
########################################################

resource "aws_s3_bucket_lifecycle_configuration" "spa_website" {
  bucket = aws_s3_bucket.spa_website.id

  rule {
    id     = "spa_website_lifecycle"
    status = "Enabled"

    filter {
      prefix = ""
    }

    # Delete incomplete multipart uploads after 7 days
    # Website content is versioned through CI/CD and stored in Git, no need for S3 versioning
    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}


resource "aws_s3_bucket_public_access_block" "spa_website" {
  bucket = aws_s3_bucket.spa_website.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

########################################################
# S3 Bucket Policy for CloudFront Access
########################################################

data "aws_iam_policy_document" "spa_website_policy" {
  statement {
    sid    = "AllowCloudFrontServicePrincipal"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    actions = [
      "s3:GetObject"
    ]

    resources = [
      "${aws_s3_bucket.spa_website.arn}/*"
    ]

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.spa_website.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "spa_website" {
  bucket = aws_s3_bucket.spa_website.id
  policy = data.aws_iam_policy_document.spa_website_policy.json

  depends_on = [aws_cloudfront_distribution.spa_website]
}

########################################################
# S3 Outputs
########################################################

output "spa_website_bucket_name" {
  description = "Name of the S3 bucket for the SPA website"
  value       = aws_s3_bucket.spa_website.bucket
}

output "spa_website_bucket_arn" {
  description = "ARN of the S3 bucket for the SPA website"
  value       = aws_s3_bucket.spa_website.arn
}

output "spa_website_bucket_regional_domain_name" {
  description = "Regional domain name of the S3 bucket"
  value       = aws_s3_bucket.spa_website.bucket_regional_domain_name
}
