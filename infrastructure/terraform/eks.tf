# EKS Cluster IAM Role
resource "aws_iam_role" "eks_cluster_role" {
  name = "${local.name_prefix}eks-cluster-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "eks.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# Attach required policies to EKS Cluster Role
resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster_role.name
}

resource "aws_iam_role_policy_attachment" "eks_service_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSServicePolicy"
  role       = aws_iam_role.eks_cluster_role.name
}

# EKS Cluster Security Group
resource "aws_security_group" "eks_cluster_sg" {
  # checkov:skip=CKV_AWS_382: "EKS cluster requires outbound access for AWS API communication"
  name        = "${local.name_prefix}eks-cluster-sg"
  description = "Security group for EKS cluster control plane"
  vpc_id      = aws_vpc.main.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}eks-cluster-sg"
    }
  )
}

# EKS Cluster
resource "aws_eks_cluster" "main" {
  # checkov:skip=CKV_AWS_339: THis is the latest up to date version of EKS with ADOT support.
  name     = "${local.name_prefix}eks"
  role_arn = aws_iam_role.eks_cluster_role.arn
  version  = "1.31"

  vpc_config {
    subnet_ids              = [aws_subnet.private_1.id, aws_subnet.private_2.id]
    security_group_ids      = [aws_security_group.eks_cluster_sg.id]
    endpoint_private_access = true
    endpoint_public_access  = false
  }

  # Enable EKS cluster encryption with KMS only if enable_kms_encryption is true
  dynamic "encryption_config" {
    for_each = var.enable_kms_encryption ? [1] : []
    content {
      provider {
        key_arn = aws_kms_key.main[0].arn
      }
      resources = ["secrets"]
    }
  }

  # Enable control plane logging
  enabled_cluster_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]

  # Configure access entries authentication mode
  access_config {
    authentication_mode = "API"  # Updated to API-only mode for modern access management
  }

  # Ensure that IAM Role permissions are created before and deleted after EKS Cluster handling
  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy,
    aws_iam_role_policy_attachment.eks_service_policy,
    aws_cloudwatch_log_group.eks_cluster_logs
  ]

  tags = merge(
    local.common_tags,
    {
      Environment = var.environment  # Add Environment tag to match IAM policy conditions
    }
  )
}

# CloudWatch Log Group for EKS Cluster Logs
resource "aws_cloudwatch_log_group" "eks_cluster_logs" {
  # checkov:skip=CKV_AWS_158: KMS encryption is configurable via the enable_kms_encryption variable
  name              = "/aws/eks/${local.name_prefix}eks/cluster"
  retention_in_days = 365
  kms_key_id        = var.enable_kms_encryption ? aws_kms_key.main[0].arn : null

  tags = local.common_tags
}

# EKS Addons - Required for node groups to join the cluster
resource "aws_eks_addon" "vpc_cni" {
  cluster_name = aws_eks_cluster.main.name
  addon_name   = "vpc-cni"
  
  # Use the latest available version
  resolve_conflicts_on_update = "OVERWRITE"
  
  depends_on = [
    aws_eks_cluster.main
  ]
}

resource "aws_eks_addon" "coredns" {
  cluster_name = aws_eks_cluster.main.name
  addon_name   = "coredns"
  
  # Use the latest available version
  resolve_conflicts_on_update = "OVERWRITE"
  
  # CoreDNS requires nodes to be available
  depends_on = [
    aws_eks_cluster.main,
    aws_eks_node_group.main
  ]
}

resource "aws_eks_addon" "kube_proxy" {
  cluster_name = aws_eks_cluster.main.name
  addon_name   = "kube-proxy"
  
  # Use the latest available version
  resolve_conflicts_on_update = "OVERWRITE"
  
  depends_on = [
    aws_eks_cluster.main
  ]
}

# Add cert-manager addon (required for ADOT)
resource "aws_eks_addon" "cert_manager" {
  cluster_name      = aws_eks_cluster.main.name
  addon_name        = "cert-manager"
  addon_version     = "v1.17.1-eksbuild.1"  # Use the latest version available at the time
  
  resolve_conflicts_on_update = "OVERWRITE"
  
  depends_on = [
    aws_eks_cluster.main,
    aws_eks_node_group.main
  ]
  
  tags = local.common_tags
}

# Add AWS Distro for OpenTelemetry (ADOT) addon
resource "aws_eks_addon" "adot" {
  cluster_name      = aws_eks_cluster.main.name
  addon_name        = "adot"
  addon_version     = "v0.109.0-eksbuild.2"  # Specific version requested
  
  # Use PRESERVE to maintain any custom configurations
  resolve_conflicts_on_update = "PRESERVE"
  
  # ADOT requires cert-manager to be installed first
  depends_on = [
    aws_eks_cluster.main,
    aws_eks_node_group.main,
    aws_eks_addon.cert_manager  # Make sure cert-manager is installed first
  ]
  
  tags = local.common_tags
}

# Node Group IAM Role
resource "aws_iam_role" "eks_node_role" {
  name = "${local.name_prefix}eks-node-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# Attach required policies to Node Group Role
resource "aws_iam_role_policy_attachment" "eks_worker_node_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.eks_node_role.name
}

resource "aws_iam_role_policy_attachment" "eks_cni_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.eks_node_role.name
}

resource "aws_iam_role_policy_attachment" "eks_container_registry_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.eks_node_role.name
}

# Add SSM policy for troubleshooting
resource "aws_iam_role_policy_attachment" "eks_ssm_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
  role       = aws_iam_role.eks_node_role.name
}

# EKS Node Security Group
resource "aws_security_group" "eks_nodes_sg" {
  # checkov:skip=CKV_AWS_382: "EKS nodes require outbound access for container images and updates"
  name        = "${local.name_prefix}eks-nodes-sg"
  description = "Security group for EKS worker nodes"
  vpc_id      = aws_vpc.main.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}eks-nodes-sg"
    }
  )
}

# Allow worker nodes to communicate with the cluster
resource "aws_security_group_rule" "nodes_to_cluster" {
  description              = "Allow worker nodes to communicate with the cluster API Server"
  from_port                = 443
  protocol                 = "tcp"
  security_group_id        = aws_security_group.eks_cluster_sg.id
  source_security_group_id = aws_security_group.eks_nodes_sg.id
  to_port                  = 443
  type                     = "ingress"
}

# Allow cluster to communicate with worker nodes
resource "aws_security_group_rule" "cluster_to_nodes" {
  description              = "Allow cluster API Server to communicate with the worker nodes"
  from_port                = 1025
  protocol                 = "tcp"
  security_group_id        = aws_security_group.eks_nodes_sg.id
  source_security_group_id = aws_security_group.eks_cluster_sg.id
  to_port                  = 65535
  type                     = "ingress"
}

# Allow cluster to communicate with worker nodes on kubelet port
resource "aws_security_group_rule" "cluster_to_nodes_kubelet" {
  description              = "Allow cluster API Server to communicate with kubelet on worker nodes"
  from_port                = 10250
  protocol                 = "tcp"
  security_group_id        = aws_security_group.eks_nodes_sg.id
  source_security_group_id = aws_security_group.eks_cluster_sg.id
  to_port                  = 10250
  type                     = "ingress"
}

# Allow nodes to communicate with each other
resource "aws_security_group_rule" "nodes_internal" {
  description              = "Allow nodes to communicate with each other"
  from_port                = 0
  protocol                 = "-1"
  security_group_id        = aws_security_group.eks_nodes_sg.id
  source_security_group_id = aws_security_group.eks_nodes_sg.id
  to_port                  = 65535
  type                     = "ingress"
}

# Allow management instance to communicate with the EKS API server
# resource "aws_security_group_rule" "management_to_cluster" {
#   description              = "Allow management instance to communicate with the cluster API Server"
#   from_port                = 443
#   protocol                 = "tcp"
#   security_group_id        = aws_security_group.eks_cluster_sg.id
#   source_security_group_id = aws_security_group.management_sg.id
#   to_port                  = 443
#   type                     = "ingress"
# }

# # Allow cluster to communicate with the management instance
# resource "aws_security_group_rule" "cluster_to_management" {
#   description              = "Allow cluster API Server to communicate with the management instance"
#   from_port                = 1024
#   protocol                 = "tcp"
#   security_group_id        = aws_security_group.management_sg.id
#   source_security_group_id = aws_security_group.eks_cluster_sg.id
#   to_port                  = 65535
#   type                     = "ingress"
# }

# EKS Node Group
resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${local.name_prefix}node-group"
  node_role_arn   = aws_iam_role.eks_node_role.arn
  subnet_ids      = [aws_subnet.private_1.id, aws_subnet.private_2.id]
  
  # Use t3.medium for a small cluster
  instance_types = ["t3.medium"]
  
  scaling_config {
    desired_size = 3
    max_size     = 4
    min_size     = 2
  }

  # Enable node group update config
  update_config {
    max_unavailable = 1
  }

  # Use launch template for additional security configurations
  launch_template {
    id      = aws_launch_template.eks_nodes.id
    version = aws_launch_template.eks_nodes.latest_version
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_worker_node_policy,
    aws_iam_role_policy_attachment.eks_cni_policy,
    aws_iam_role_policy_attachment.eks_container_registry_policy,
    aws_eks_addon.vpc_cni,
    aws_eks_addon.kube_proxy
  ]

  tags = local.common_tags
}

# Launch template for EKS nodes with IMDSv2 and encryption
resource "aws_launch_template" "eks_nodes" {
  name = "${local.name_prefix}eks-node-template"

  # Enable IMDSv2
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"  # Require IMDSv2
    http_put_response_hop_limit = 1
  }

  # Enable EBS encryption
  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_size           = 20
      volume_type           = "gp3"
      delete_on_termination = true
      encrypted             = true
      kms_key_id            = var.enable_kms_encryption ? aws_kms_key.main[0].arn : null
    }
  }

  # Use the EKS node security group
  vpc_security_group_ids = [aws_security_group.eks_nodes_sg.id]

  tag_specifications {
    resource_type = "instance"
    tags = merge(
      local.common_tags,
      {
        Name = "${local.name_prefix}eks-node"
      }
    )
  }

  tags = local.common_tags
}

# Create EKS access entries for cluster access with access policies instead of system groups
resource "aws_eks_access_entry" "cluster_admin" {
  cluster_name  = aws_eks_cluster.main.name
  principal_arn = aws_iam_role.eks_cluster_role.arn
  
  depends_on = [aws_eks_cluster.main]
}

# Associate the cluster-admin access policy with the cluster role
resource "aws_eks_access_policy_association" "cluster_admin_policy" {
  cluster_name  = aws_eks_cluster.main.name
  principal_arn = aws_iam_role.eks_cluster_role.arn
  policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"
  
  # Add access scope block for cluster-wide access
  access_scope {
    type       = "cluster"
    namespaces = []  # Empty for cluster-wide access
  }
  
  depends_on = [aws_eks_access_entry.cluster_admin]
}

# # Access entry for the management instance role
# resource "aws_eks_access_entry" "management_instance" {
#   cluster_name  = aws_eks_cluster.main.name
#   principal_arn = aws_iam_role.management_role.arn
  
#   depends_on = [aws_eks_cluster.main]
# }

# # Associate the cluster-admin access policy with the management role
# resource "aws_eks_access_policy_association" "management_instance_policy" {
#   cluster_name  = aws_eks_cluster.main.name
#   principal_arn = aws_iam_role.management_role.arn
#   policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"
  
#   # Add access scope block for cluster-wide access
#   access_scope {
#     type       = "cluster"
#     namespaces = []  # Empty for cluster-wide access
#   }
  
#   depends_on = [aws_eks_access_entry.management_instance]
# }

# EKS Deployment Role for CI/CD
resource "aws_iam_role" "eks_deployment_role" {
  name = "${local.name_prefix}eks-deployment-role"

  # This assume role policy allows trusted entities to assume this role
  # It's designed to be agnostic to the CI/CD platform
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          # This allows other IAM roles/users in your account to assume this role
          # You'll need to add specific trusted principals based on your setup
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        # Optional condition to restrict which entities can assume the role
        Condition = {
          StringEquals = {
            "aws:PrincipalType": "AssumedRole"
          }
        }
      }
    ]
  })

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}eks-deployment-role"
      Purpose = "EKS deployment operations for CI/CD"
    }
  )
}

# Attach EKS cluster policy to the deployment role
resource "aws_iam_role_policy_attachment" "deployment_eks_cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_deployment_role.name
}

# Attach ECR full access policy to the deployment role
resource "aws_iam_role_policy_attachment" "deployment_ecr_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser"
  role       = aws_iam_role.eks_deployment_role.name
}

# Custom policy for additional permissions needed for deployments
resource "aws_iam_policy" "eks_deployment_custom_policy" {
  name        = "${local.name_prefix}eks-deployment-custom-policy"
  description = "Custom policy for EKS deployment operations"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          # Read-only permissions for EKS
          "eks:DescribeCluster",
          "eks:ListClusters",
          "eks:DescribeUpdate"
        ],
        Resource = [
          "arn:aws:eks:*:${data.aws_caller_identity.current.account_id}:cluster/${local.name_prefix}eks",
          "arn:aws:eks:*:${data.aws_caller_identity.current.account_id}:cluster/${local.name_prefix}eks/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          # Write permissions for EKS with conditions
          "eks:UpdateClusterConfig"
        ],
        Resource = [
          "arn:aws:eks:*:${data.aws_caller_identity.current.account_id}:cluster/${local.name_prefix}eks"
        ],
        Condition = {
          StringEquals = {
            "aws:ResourceTag/Environment": "${var.environment}"
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          # Read-only permissions for access entries
          "eks:ListAccessEntries",
          "eks:DescribeAccessEntry"
        ],
        Resource = [
          "arn:aws:eks:*:${data.aws_caller_identity.current.account_id}:cluster/${local.name_prefix}eks",
          "arn:aws:eks:*:${data.aws_caller_identity.current.account_id}:cluster/${local.name_prefix}eks/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          # Write permissions for access entries with conditions
          "eks:CreateAccessEntry",
          "eks:DeleteAccessEntry"
        ],
        Resource = [
          "arn:aws:eks:*:${data.aws_caller_identity.current.account_id}:cluster/${local.name_prefix}eks",
          "arn:aws:eks:*:${data.aws_caller_identity.current.account_id}:cluster/${local.name_prefix}eks/*"
        ],
        Condition = {
          StringEquals = {
            "aws:ResourceTag/Environment": "${var.environment}"
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          # Read-only permissions for kubectl operations
          "eks:ListFargateProfiles",
          "eks:DescribeFargateProfile",
          "eks:ListNodegroups",
          "eks:DescribeNodegroup",
          "eks:ListAddons",
          "eks:DescribeAddon",
          "eks:ListIdentityProviderConfigs",
          "eks:DescribeIdentityProviderConfig"
        ],
        Resource = [
          "arn:aws:eks:*:${data.aws_caller_identity.current.account_id}:cluster/${local.name_prefix}eks",
          "arn:aws:eks:*:${data.aws_caller_identity.current.account_id}:cluster/${local.name_prefix}eks/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          # CloudWatch Logs read permissions
          "logs:GetLogEvents",
          "logs:DescribeLogStreams"
        ],
        Resource = [
          "arn:aws:logs:*:${data.aws_caller_identity.current.account_id}:log-group:/aws/eks/${local.name_prefix}eks/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          # Log group listing needs to be at account level
          "logs:DescribeLogGroups"
        ],
        Resource = [
          "arn:aws:logs:*:${data.aws_caller_identity.current.account_id}:log-group:*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          # List operations that genuinely need account-wide scope
          "eks:ListClusters"
        ],
        Resource = "*"
      }
    ]
  })

  tags = local.common_tags
}

# Attach the custom policy to the deployment role
resource "aws_iam_role_policy_attachment" "deployment_custom_policy_attachment" {
  policy_arn = aws_iam_policy.eks_deployment_custom_policy.arn
  role       = aws_iam_role.eks_deployment_role.name
}

# Update the access entry for deployment role
resource "aws_eks_access_entry" "deployment_role" {
  cluster_name  = aws_eks_cluster.main.name
  principal_arn = aws_iam_role.eks_deployment_role.arn
  
  depends_on = [aws_eks_cluster.main]
}

# Associate the cluster-admin access policy with the deployment role
resource "aws_eks_access_policy_association" "deployment_role_policy" {
  cluster_name  = aws_eks_cluster.main.name
  principal_arn = aws_iam_role.eks_deployment_role.arn
  policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"
  
  # Add access scope block for cluster-wide access
  access_scope {
    type       = "cluster"
    namespaces = []  # Empty for cluster-wide access
  }
  
  depends_on = [aws_eks_access_entry.deployment_role]
}

# Add data source for current identity
data "aws_caller_identity" "current" {}

# Add EKS cluster outputs to outputs.tf

# Add access entry for federated role
resource "aws_eks_access_entry" "federated_admin" {
  count = var.federated_role_name != "" ? 1 : 0
  
  cluster_name  = aws_eks_cluster.main.name
  principal_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.federated_role_name}"
  
  depends_on = [aws_eks_cluster.main]
}

resource "aws_eks_access_policy_association" "federated_admin_policy" {
  count = var.federated_role_name != "" ? 1 : 0
  
  cluster_name  = aws_eks_cluster.main.name
  principal_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.federated_role_name}"
  policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"
  
  access_scope {
    type       = "cluster"
    namespaces = []
  }
  
  depends_on = [aws_eks_access_entry.federated_admin]
}

# OIDC Provider for EKS - moved from loadbalancer.tf
# This is a core EKS component used by many addons that need AWS IAM integration
resource "aws_iam_openid_connect_provider" "eks" {
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.eks.certificates[0].sha1_fingerprint]
  url             = aws_eks_cluster.main.identity[0].oidc[0].issuer

  tags = local.common_tags
}

# Get the TLS certificate for the EKS OIDC provider - moved from loadbalancer.tf
data "tls_certificate" "eks" {
  url = aws_eks_cluster.main.identity[0].oidc[0].issuer
}

# Access entry for the bastion instance role
resource "aws_eks_access_entry" "bastion" {
  cluster_name  = aws_eks_cluster.main.name
  principal_arn = aws_iam_role.bastion_role.arn
  
  depends_on = [aws_eks_cluster.main]
}

# Associate the cluster-admin access policy with the bastion role
resource "aws_eks_access_policy_association" "bastion_policy" {
  cluster_name  = aws_eks_cluster.main.name
  principal_arn = aws_iam_role.bastion_role.arn
  policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"
  
  # Add access scope block for cluster-wide access
  access_scope {
    type       = "cluster"
    namespaces = []  # Empty for cluster-wide access
  }
  
  depends_on = [aws_eks_access_entry.bastion]
}

# Allow bastion instance to communicate with the EKS API server
resource "aws_security_group_rule" "bastion_to_cluster" {
  description              = "Allow bastion instance to communicate with the cluster API Server"
  from_port                = 443
  protocol                 = "tcp"
  security_group_id        = aws_security_group.eks_cluster_sg.id
  source_security_group_id = aws_security_group.bastion_sg.id
  to_port                  = 443
  type                     = "ingress"
}

# Allow cluster to communicate with the bastion instance
resource "aws_security_group_rule" "cluster_to_bastion" {
  description              = "Allow cluster API Server to communicate with the bastion instance"
  from_port                = 1024
  protocol                 = "tcp"
  security_group_id        = aws_security_group.bastion_sg.id
  source_security_group_id = aws_security_group.eks_cluster_sg.id
  to_port                  = 65535
  type                     = "ingress"
}
