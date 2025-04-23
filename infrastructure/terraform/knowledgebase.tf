module "bedrock" {
  # checkov:skip=CKV_TF_1: AWS source and is trusted.
  source = "aws-ia/bedrock/aws" 
  version = "0.0.18"
  create_default_kb = true
  create_agent = false
  kb_embedding_model_arn = "arn:aws:bedrock:${var.aws_region}::foundation-model/amazon.titan-embed-text-v2:0"
}