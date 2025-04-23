# IAM Role for AWS Load Balancer Controller
resource "aws_iam_role" "aws_load_balancer_controller" {
  name = "${local.name_prefix}aws-load-balancer-controller-role"

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
            "${replace(aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")}:aud": "sts.amazonaws.com",
            "${replace(aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")}:sub": "system:serviceaccount:kube-system:aws-load-balancer-controller"
          }
        }
      }
    ]
  })

  # Add the required principal tag for the managed policy to work
  tags = merge(
    local.common_tags,
    {
      "eks:eks-cluster-name" = aws_eks_cluster.main.name
    }
  )
}

# Attach the AWS Load Balancer Controller IAM policy to the role
resource "aws_iam_role_policy_attachment" "aws_load_balancer_controller" {
  policy_arn = aws_iam_policy.aws_load_balancer_controller_policy.arn
  role       = aws_iam_role.aws_load_balancer_controller.name
}

# Create the AWS Load Balancer Controller IAM policy
resource "aws_iam_policy" "aws_load_balancer_controller_policy" {
  name        = "${local.name_prefix}lab-policy"
  description = "IAM policy for AWS Load Balancer Controller"
  
  policy = file("${path.module}/policies/aws_load_balancer_controller_policy.json")
}