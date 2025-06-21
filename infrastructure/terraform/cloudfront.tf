
########################################################
# CloudFront Response Headers Policy
########################################################

resource "aws_cloudfront_response_headers_policy" "spa_website" {
  name = "${local.name_prefix}spa-website-headers-${local.suffix}"

  security_headers_config {
    strict_transport_security {
      access_control_max_age_sec = 31536000
      include_subdomains         = true
      preload                    = true
      override                   = true
    }

    content_type_options {
      override = false
    }

    frame_options {
      frame_option = "DENY"
      override     = false
    }

    referrer_policy {
      referrer_policy = "strict-origin-when-cross-origin"
      override        = false
    }
  }

  custom_headers_config {
    items {
      header   = "X-Permitted-Cross-Domain-Policies"
      value    = "none"
      override = false
    }
  }
}

########################################################
# CloudFront Origin Access Control
########################################################

resource "aws_cloudfront_origin_access_control" "spa_website" {
  name                              = "${local.name_prefix}spa-website-oac-${local.suffix}"
  description                       = "OAC for SPA website S3 bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

########################################################
# CloudFront Distribution
########################################################

resource "aws_cloudfront_distribution" "spa_website" {
  # checkov:skip=CKV2_AWS_42:Using CloudFront default certificate for sample application - custom SSL cert not required
  # checkov:skip=CKV_AWS_310:Origin failover not required for example S3 origin static website
  # checkov:skip=CKV_AWS_374:Geo restriction not required for example application - global access intended
  # checkov:skip=CKV_AWS_68:WAF intentionally disabled - regional stacks fail to deploy because WAF is global and requires us-east-1
  # checkov:skip=CKV2_AWS_47:WAF intentionally disabled - regional stacks fail to deploy because WAF is global and requires us-east-1
  # checkov:skip=CKV_AWS_86:Access logging not needed for sample UI - adds unnecessary complexity and cost

  origin {
    domain_name              = aws_s3_bucket.spa_website.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.spa_website.id
    origin_id                = "S3-${aws_s3_bucket.spa_website.bucket}"

    # Add origin shield for better performance and cost optimization
    origin_shield {
      enabled              = true
      origin_shield_region = "us-west-2"
    }
  }

  enabled             = true
  is_ipv6_enabled     = true
  comment             = "CloudFront distribution for SPA website - dev"
  default_root_object = "index.html"
  

  # Cache behavior for the default path
  default_cache_behavior {
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${aws_s3_bucket.spa_website.bucket}"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy   = "redirect-to-https"
    min_ttl                  = 0
    default_ttl              = 3600
    max_ttl                  = 86400
    compress                 = true
    response_headers_policy_id = aws_cloudfront_response_headers_policy.spa_website.id
  }

  # Cache behavior for static assets (CSS, JS, images)
  ordered_cache_behavior {
    path_pattern     = "/static/*"
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${aws_s3_bucket.spa_website.bucket}"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    min_ttl                    = 0
    default_ttl                = 86400
    max_ttl                    = 31536000
    compress                   = true
    viewer_protocol_policy     = "redirect-to-https"
    response_headers_policy_id = aws_cloudfront_response_headers_policy.spa_website.id
  }

  # Cache behavior for API calls (if your SPA makes API calls through CloudFront)
  ordered_cache_behavior {
    path_pattern     = "/api/*"
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${aws_s3_bucket.spa_website.bucket}"

    forwarded_values {
      query_string = true
      headers      = ["Authorization", "CloudFront-Forwarded-Proto"]
      cookies {
        forward = "all"
      }
    }

    min_ttl                    = 0
    default_ttl                = 0
    max_ttl                    = 0
    compress                   = true
    viewer_protocol_policy     = "redirect-to-https"
    response_headers_policy_id = aws_cloudfront_response_headers_policy.spa_website.id
  }

  price_class = "PriceClass_100"

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}spa-website-cf-${local.suffix}"
    Type = "CloudFrontDistribution"
  })

  viewer_certificate {
    cloudfront_default_certificate = true
    minimum_protocol_version       = "TLSv1.2_2021"
  }

  # Custom error responses for SPA routing
  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
  }

  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

}

########################################################
# CloudFront Outputs
########################################################

output "cloudfront_distribution_id" {
  description = "ID of the CloudFront distribution"
  value       = aws_cloudfront_distribution.spa_website.id
}

output "cloudfront_distribution_arn" {
  description = "ARN of the CloudFront distribution"
  value       = aws_cloudfront_distribution.spa_website.arn
}

output "cloudfront_domain_name" {
  description = "Domain name of the CloudFront distribution"
  value       = aws_cloudfront_distribution.spa_website.domain_name
}

output "spa_website_url" {
  description = "URL of the SPA website"
  value       = "https://${aws_cloudfront_distribution.spa_website.domain_name}"
}
