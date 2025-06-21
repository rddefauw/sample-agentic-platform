# IAM role for the code server instance
resource "aws_iam_role" "bastion_role" {
  name = "${local.name_prefix}bastion-role"

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

# Attach policies to the code server instance role
resource "aws_iam_role_policy_attachment" "bastion_ssm" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
  role       = aws_iam_role.bastion_role.name
}

# Create a custom policy for EKS management with strict permissions
resource "aws_iam_policy" "eks_bastion_policy" {
  name        = "${local.name_prefix}eks-bastion-policy"
  description = "Policy for managing specific EKS cluster with least privilege"
  
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      # Specific actions for the target cluster - no wildcards
      {
        Effect = "Allow",
        Action = [
          "eks:AccessKubernetesApi",
          "eks:DescribeCluster",
          "eks:DescribeNodegroup",
          "eks:DescribeUpdate",
          "eks:ListNodegroups",
          "eks:ListUpdates",
          "eks:UpdateClusterConfig",
          "eks:UpdateClusterVersion",
          "eks:UpdateNodegroupConfig",
          "eks:UpdateNodegroupVersion"
        ],
        Resource = aws_eks_cluster.main.arn
      },
      # Nodegroup specific permissions
      {
        Effect = "Allow",
        Action = [
          "eks:DescribeNodegroup",
          "eks:ListNodegroups",
          "eks:UpdateNodegroupConfig",
          "eks:UpdateNodegroupVersion"
        ],
        Resource = "${aws_eks_cluster.main.arn}/nodegroup/*"
      },
      # Fargate profile permissions if needed
      {
        Effect = "Allow",
        Action = [
          "eks:DescribeFargateProfile",
          "eks:ListFargateProfiles"
        ],
        Resource = "${aws_eks_cluster.main.arn}/fargateprofile/*"
      },
      # Minimal list permissions - required for basic operations
      {
        Effect = "Allow",
        Action = [
          "eks:ListClusters"
        ],
        Resource = "*"
      }
    ]
  })
  
  tags = local.common_tags
}

# Attach the custom policy to the code server role
resource "aws_iam_role_policy_attachment" "bastion_eks_policy" {
  policy_arn = aws_iam_policy.eks_bastion_policy.arn
  role       = aws_iam_role.bastion_role.name
}

# Instance profile for the code server instance
resource "aws_iam_instance_profile" "bastion_profile" {
  name = "${local.name_prefix}bastion-profile"
  role = aws_iam_role.bastion_role.name
}

# Security group for the code server instance
resource "aws_security_group" "bastion_sg" {
  # checkov:skip=CKV_AWS_382: "Code server instance requires outbound access for AWS API communication and package updates"
  name        = "${local.name_prefix}bastion-sg"
  description = "Security group for EKS code server instance"
  vpc_id      = aws_vpc.main.id

  # Allow all outbound traffic
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
      Name = "${local.name_prefix}bastion-sg"
    }
  )
}

# Find the latest Ubuntu 22.04 LTS AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical's owner ID

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Code server instance
resource "aws_instance" "bastion" {
  ami                    = data.aws_ami.ubuntu.id  # Use Ubuntu instead of Amazon Linux
  instance_type          = "t3.large"
  subnet_id              = aws_subnet.private_1.id
  vpc_security_group_ids = [aws_security_group.bastion_sg.id]
  iam_instance_profile   = aws_iam_instance_profile.bastion_profile.name
  
  # Keep all your security settings
  ebs_optimized = true
  monitoring    = true
  
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  lifecycle {
     create_before_destroy = true
   }
  
  # Updated user data for Ubuntu with code-server and kubectl proxy
  user_data_replace_on_change = true
  user_data = <<-EOF
    #!/bin/bash
    
    # Update package lists
    apt-get update

    # Install build-essential, clang, and libomp-dev for c++ build of chromaDB.
    apt-get install -y build-essential clang libomp-dev
    
    # Install required packages
    apt-get install -y unzip curl jq git python3-pip python3-venv python3-dev

    # Install NVM
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

    # Install Node.js v23.9.0 (same as your laptop)
    nvm install 23.9.0
    nvm use 23.9.0
    nvm alias default 23.9.0

    # Make available system-wide
    ln -sf "$NVM_DIR/versions/node/v23.9.0/bin/node" /usr/local/bin/node
    ln -sf "$NVM_DIR/versions/node/v23.9.0/bin/npm" /usr/local/bin/npm
    ln -sf "$NVM_DIR/versions/node/v23.9.0/bin/npx" /usr/local/bin/npx

    # Verify
    /usr/local/bin/node --version

    # Set compiler environment variables in ubuntu user's profile
    cat >> /home/ubuntu/.profile << 'PROFILEEOF'
    # Set compiler environment variables for C++ builds
    export CC=clang
    export CXX=clang++
    export CFLAGS="-fPIC -O3"
    export CXXFLAGS="-fPIC -O3 -std=c++14"
    PROFILEEOF

    # Install Docker
    apt-get install -y docker.io
    # Allow ubuntu user to use docker without sudo
    usermod -aG docker ubuntu

    # Install Helm
    snap install helm --classic


    # Install kubectl
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
    chmod +x kubectl
    mv kubectl /usr/local/bin/
    
    # Install AWS CLI v2
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    ./aws/install
    
    # Configure kubectl for the EKS cluster
    aws eks update-kubeconfig --name ${aws_eks_cluster.main.name} --region ${data.aws_region.current.name}
    
    # Create ubuntu user home dir and set permissions
    mkdir -p /home/ubuntu/.kube
    cp /root/.kube/config /home/ubuntu/.kube/
    chown -R ubuntu:ubuntu /home/ubuntu/.kube
    
    # Install code-server (VS Code in the browser)
    su - ubuntu -c "curl -fsSL https://code-server.dev/install.sh | sh"

    # Install uv
    su - ubuntu -c "curl -LsSf https://astral.sh/uv/install.sh | sh"

    # Add uv environment to .bashrc for auto-loading
    su - ubuntu -c 'echo "source \$HOME/.local/bin/env" >> $HOME/.bashrc'
    

    # Git clone the sample repository
    su - ubuntu -c "git clone https://github.com/aws-samples/sample-agentic-platform.git"
    # Create a simple script to run code-server and kubectl proxy
    cat > /home/ubuntu/start-code-server.sh << 'EOL'
    #!/bin/bash
    nohup code-server --port 8888 --auth none > /home/ubuntu/code-server.log 2>&1 &
    nohup kubectl proxy --port=8080 --address='0.0.0.0' --accept-hosts='.*' > /tmp/proxy.log 2>&1 &
    EOL
    
    chmod +x /home/ubuntu/start-code-server.sh
    chown ubuntu:ubuntu /home/ubuntu/start-code-server.sh
    
    # Auto-start code-server when system boots
    echo "@reboot ubuntu /home/ubuntu/start-code-server.sh" | tee -a /etc/crontab
    
    # Start code-server right away
    su - ubuntu -c "/home/ubuntu/start-code-server.sh"
  EOF

  root_block_device {
    volume_size           = 20
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}bastion-instance"
    }
  )
}

# Output the instance ID for easy reference
output "bastion_instance_id" {
  value       = aws_instance.bastion.id
  description = "ID of the bastion instance for SSM access"
}

# IAM policy for RDS IAM authentication
resource "aws_iam_policy" "rds_cs_connect_policy" {
  name        = "${local.name_prefix}rds-cs-connect-policy"
  description = "Policy to allow IAM authentication to RDS"
  
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [ # nosemgrep: no-iam-resource-exposure
          "rds-db:connect"
        ],
        Resource = [
          "arn:aws:rds-db:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:dbuser:${aws_rds_cluster.postgres.cluster_resource_id}/*"
        ]
      }
    ]
  })
  
  tags = local.common_tags
}

# Attach the RDS connect policy to the code server instance role
resource "aws_iam_role_policy_attachment" "bastion_rds_connect" {
  policy_arn = aws_iam_policy.rds_cs_connect_policy.arn
  role       = aws_iam_role.bastion_role.name
}

# Bedrock policy for code server
resource "aws_iam_policy" "bedrock_bastion_policy" {
  name        = "${local.name_prefix}bedrock-bastion-policy"
  description = "Policy to allow invoking Bedrock models from code server"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
          "bedrock:Retrieve",
          "bedrock:RetrieveAndGenerate",
          "bedrock:ListKnowledgeBases",
          "bedrock:GetKnowledgeBase"
        ]
        Resource = [
          # Allow access to all models in the account across all regions
          "arn:aws:bedrock:*:${data.aws_caller_identity.current.account_id}:model/*",
          # Allow access to all inference profiles in the account across all regions
          "arn:aws:bedrock:*:${data.aws_caller_identity.current.account_id}:inference-profile/*",
          # Allow access to AWS foundation models
          "arn:aws:bedrock:*::foundation-model/*",
          # Allow operations on all knowledge bases in the account across all regions
          "arn:aws:bedrock:*:${data.aws_caller_identity.current.account_id}:knowledge-base/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:ListFoundationModels",
          "bedrock:GetFoundationModel",
          "bedrock:ListKnowledgeBases"
        ]
        Resource = [
          # These are read-only list operations that require * resource
          "arn:aws:bedrock:*:${data.aws_caller_identity.current.account_id}:*"
        ]
      }
    ]
  })

  tags = local.common_tags
}

# Attach the Bedrock policy to the code server role
resource "aws_iam_role_policy_attachment" "bastion_bedrock_attachment" {
  policy_arn = aws_iam_policy.bedrock_bastion_policy.arn
  role       = aws_iam_role.bastion_role.name
}

# Enhanced Secrets Manager policy for code server
resource "aws_iam_policy" "secrets_manager_bastion_policy" {
  name        = "${local.name_prefix}secrets-manager-bastion-policy"
  description = "Policy to allow access to required secrets from code server"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ],
        Resource = [
          # RDS master password secret
          aws_rds_cluster.postgres.master_user_secret[0].secret_arn,
          # Redis auth secret
          aws_secretsmanager_secret.redis_auth.arn,
          # M2M credentials secret - reference the actual secret resource
          aws_secretsmanager_secret.m2m_credentials.arn  # Replace with your actual secret resource name
        ]
      }
    ]
  })

  tags = local.common_tags
}

# Attach the Secrets Manager policy to the code server role
resource "aws_iam_role_policy_attachment" "bastion_secrets_manager_attachment" {
  policy_arn = aws_iam_policy.secrets_manager_bastion_policy.arn
  role       = aws_iam_role.bastion_role.name
}

# Redis access policy for code server
resource "aws_iam_policy" "redis_bastion_policy" {
  name        = "${local.name_prefix}redis-bastion-policy"
  description = "Policy to allow access to Redis rate limiting cluster from code server"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "elasticache:Connect",
          "elasticache:DescribeReplicationGroups",
          "elasticache:DescribeCacheClusters"
        ],
        Resource = [
          aws_elasticache_replication_group.redis_ratelimit.arn,
          "arn:aws:elasticache:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*"
        ]
      }
    ]
  })

  tags = local.common_tags
}

# Attach the Redis policy to the code server role
resource "aws_iam_role_policy_attachment" "bastion_redis_attachment" {
  policy_arn = aws_iam_policy.redis_bastion_policy.arn
  role       = aws_iam_role.bastion_role.name
}

# DynamoDB policy for code server (for the usage_plans and usage_logs tables)
resource "aws_iam_policy" "dynamodb_bastion_policy" {
  name        = "${local.name_prefix}dynamodb-bastion-policy"
  description = "Policy to allow access to DynamoDB tables used by LLM Gateway"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.usage_plans.arn,
          aws_dynamodb_table.usage_logs.arn,
          "${aws_dynamodb_table.usage_logs.arn}/index/*"
        ]
      }
    ]
  })

  tags = local.common_tags
}

# Attach the DynamoDB policy to the code server role
resource "aws_iam_role_policy_attachment" "bastion_dynamodb_attachment" {
  policy_arn = aws_iam_policy.dynamodb_bastion_policy.arn
  role       = aws_iam_role.bastion_role.name
}

# ECR policy for the bastion host with least privilege
resource "aws_iam_policy" "ecr_bastion_policy" {
  name        = "${local.name_prefix}ecr-bastion-policy"
  description = "Policy to allow limited ECR operations from bastion host"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # Auth token is account-wide, can't be restricted to specific repositories
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken"
        ]
        Resource = "*"
      },
      # Specific permissions for repositories with the agentic-platform prefix
      {
        Effect = "Allow"
        Action = [
          "ecr:DescribeRepositories",
          "ecr:CreateRepository",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:GetRepositoryPolicy",
          "ecr:ListImages",
          "ecr:BatchGetImage"
        ]
        Resource = "arn:aws:ecr:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:repository/agentic-platform-*"
      },
      # Push image permissions, more sensitive so restricting to specific repositories
      {
        Effect = "Allow"
        Action = [
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload",
          "ecr:PutImage"
        ]
        Resource = "arn:aws:ecr:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:repository/agentic-platform-*"
      }
    ]
  })

  tags = local.common_tags
}

# Attach the ECR policy to the bastion role
resource "aws_iam_role_policy_attachment" "bastion_ecr_attachment" {
  policy_arn = aws_iam_policy.ecr_bastion_policy.arn
  role       = aws_iam_role.bastion_role.name
}

# Attach AWS managed ELB read-only policy to the code server role
resource "aws_iam_role_policy_attachment" "bastion_elb_readonly_attachment" {
  policy_arn = "arn:aws:iam::aws:policy/ElasticLoadBalancingReadOnly"
  role       = aws_iam_role.bastion_role.name
}
