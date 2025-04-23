# AWS Provider configuration
provider "aws" {
  region = var.aws_region
}

# Kubernetes provider configuration for EKS
provider "kubernetes" {
  host                   = aws_eks_cluster.main.endpoint
  cluster_ca_certificate = base64decode(aws_eks_cluster.main.certificate_authority[0].data)
  
  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    args        = ["eks", "get-token", "--cluster-name", aws_eks_cluster.main.name]
    command     = "aws"
  }
}

provider "opensearch" {
  url         = module.bedrock.default_collection.collection_endpoint 
  healthcheck = false
}

provider "awscc" {
  region = var.aws_region
}