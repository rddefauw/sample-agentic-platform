# Backend configuration for state management. Uncomment if bootstrapping.
terraform {
  # Uncomment to use S3 as backend
  # backend "s3" {
  #   bucket         = "your-terraform-state-bucket"
  #   key            = "catalogs/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "terraform-state-lock"
  #   encrypt        = true
  # }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5" 
    }
     opensearch = {
      source  = "opensearch-project/opensearch"
      version = "= 2.2.0"
    }
    awscc = {
      source  = "hashicorp/awscc"
      version = "= 1.35.0"
    }
  }
  
  required_version = ">= 1.0.0"
}