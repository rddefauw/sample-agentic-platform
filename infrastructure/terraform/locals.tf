resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

locals {
  # Common naming pattern for all resources
  name_prefix = var.stack_name != "" ? "${var.stack_name}-" : ""
  
  # Common tags for all resources
  common_tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
    Suffix      = random_string.suffix.result
    Project     = "Agentic Platform Sample"
  }
}
