// AWS VPC Configuration
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}vpc"
    }
  )
}

// VPC Flow Logs Configuration
resource "aws_flow_log" "vpc_flow_log" {
  iam_role_arn    = aws_iam_role.vpc_flow_log_role.arn
  log_destination = aws_cloudwatch_log_group.vpc_flow_log_group.arn
  traffic_type    = "ALL"
  vpc_id          = aws_vpc.main.id
}

// CloudWatch Log Group for Flow Logs
resource "aws_cloudwatch_log_group" "vpc_flow_log_group" {
  // checkov:skip=CKV_AWS_158: KMS encryption is conditionally enabled based on var.enable_kms_encryption
  name              = "/aws/vpc/flow-logs/${local.name_prefix}vpc"
  retention_in_days = 365
  kms_key_id        = var.enable_kms_encryption ? aws_kms_key.main[0].arn : null

  tags = local.common_tags
}

// IAM Role for VPC Flow Logs
resource "aws_iam_role" "vpc_flow_log_role" {
  name = "${local.name_prefix}vpc-flow-log-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "vpc-flow-logs.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

// IAM Policy for VPC Flow Logs
resource "aws_iam_role_policy" "vpc_flow_log_policy" {
  name = "${local.name_prefix}vpc-flow-log-policy"
  role = aws_iam_role.vpc_flow_log_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Effect = "Allow"
        Resource = [
          aws_cloudwatch_log_group.vpc_flow_log_group.arn,
          "${aws_cloudwatch_log_group.vpc_flow_log_group.arn}:*"
        ]
      }
    ]
  })
}

// Public Subnets in different Availability Zones
resource "aws_subnet" "public_1" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${data.aws_region.current.name}a"
  map_public_ip_on_launch = false

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}public-subnet-1",
      "kubernetes.io/role/elb" = "1",
      "kubernetes.io/cluster/${local.name_prefix}eks" = "shared"
    }
  )
}

resource "aws_subnet" "public_2" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "${data.aws_region.current.name}b"
  map_public_ip_on_launch = false

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}public-subnet-2",
      "kubernetes.io/role/elb" = "1",
      "kubernetes.io/cluster/${local.name_prefix}eks" = "shared"
    }
  )
}

// Private Subnets in different Availability Zones
resource "aws_subnet" "private_1" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.11.0/24"
  availability_zone = "${data.aws_region.current.name}a"

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}private-subnet-1",
      "kubernetes.io/role/internal-elb" = "1",
      "kubernetes.io/cluster/${local.name_prefix}eks" = "shared"
    }
  )
}

resource "aws_subnet" "private_2" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.12.0/24"
  availability_zone = "${data.aws_region.current.name}b"

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}private-subnet-2",
      "kubernetes.io/role/internal-elb" = "1",
      "kubernetes.io/cluster/${local.name_prefix}eks" = "shared"
    }
  )
}

// Internet Gateway for public subnets
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}igw"
    }
  )
}

// Route Table for public subnets
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}public-route-table"
    }
  )
}

// Route Table for private subnets
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}private-route-table"
    }
  )
}

// Route Table Associations
resource "aws_route_table_association" "public_1" {
  subnet_id      = aws_subnet.public_1.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_2" {
  subnet_id      = aws_subnet.public_2.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private_1" {
  subnet_id      = aws_subnet.private_1.id
  route_table_id = aws_route_table.private_1.id
}

resource "aws_route_table_association" "private_2" {
  subnet_id      = aws_subnet.private_2.id
  route_table_id = aws_route_table.private_2.id
}

// Configure default security group to deny all traffic
resource "aws_default_security_group" "default" {
  vpc_id = aws_vpc.main.id

  // Empty ingress and egress blocks means no traffic is allowed
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}default-sg"
    }
  )
}

// Get current region data
data "aws_region" "current" {}

// Elastic IPs for NAT Gateways
resource "aws_eip" "nat_1" {
  domain = "vpc"
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}nat-eip-1"
    }
  )
}

resource "aws_eip" "nat_2" {
  domain = "vpc"
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}nat-eip-2"
    }
  )
}

// NAT Gateways in public subnets
resource "aws_nat_gateway" "nat_1" {
  allocation_id = aws_eip.nat_1.id
  subnet_id     = aws_subnet.public_1.id
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}nat-gateway-1"
    }
  )
  
  depends_on = [aws_internet_gateway.main]
}

resource "aws_nat_gateway" "nat_2" {
  allocation_id = aws_eip.nat_2.id
  subnet_id     = aws_subnet.public_2.id
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}nat-gateway-2"
    }
  )
  
  depends_on = [aws_internet_gateway.main]
}

// Separate route tables for each private subnet with routes to NAT Gateways
resource "aws_route_table" "private_1" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat_1.id
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}private-route-table-1"
    }
  )
}

resource "aws_route_table" "private_2" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat_2.id
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}private-route-table-2"
    }
  )
}
