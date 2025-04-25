resource "random_string" "suffix" {
  length  = 3
  special = false
  upper   = false
}

locals {
  # Common naming pattern for all resources
  name_prefix = var.stack_name != "" ? "${var.stack_name}-" : ""

  suffix = random_string.suffix.result
  
  # Common tags for all resources
  common_tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
    Suffix      = local.suffix
    Project     = "Agentic Platform Sample"
  }
}
