# Deploy Sample Agent Platform
Here's a guide for deploying the sample agentic platform into an Isengard account. **Warning**: This will deploy resources into your aws account through terraform and charges will apply.

**Important Notice:** This project deploys resources in your AWS environment using Terraform. You will incur costs for the AWS resources used. Please be aware of the pricing for services like EKS, Bedrock, OpenSearch, DynamoDB, Elasticache, S3, etc.. in your AWS region.

Required Permissions: You need elevated permissions, to deploy the Terraform stack.

## Bootstrap
Optionally, you can add a bootstrap to spin up an S3 bucket and DDB table to manage your terraform state.
If you have that available, you can uncomment the lines in main.tf. 

**INFO**: You will need a service linked role for opensearch for the terraform to execute. Run the following command
```bash
$ aws iam create-service-linked-role --aws-service-name opensearchservice.amazonaws.com
```
If it fails because it already exists, that's okay. We just need it present in the account.

## Create Infrastructure
The base of this infrastructure is Kubernetes on EKS. To get started, you need to deploy the stack. First create a terraform.tfvars file in the infrastructure/terraform directory like this:

```bash
########################################################
# Global Variables
########################################################

aws_region  = "us-west-2"
environment = "dev"
stack_name  = "agent-ptfm"

########################################################
# K8s console access role
########################################################

federated_role_name = "<YOUR ROLE TO ACCESS THE EKS CONSOLE>"

########################################################
# KMS Variables
########################################################

enable_kms_encryption = false  # Set to true if you want to enable KMS encryption
kms_deletion_window   = 7
kms_key_administrators = [
  # Add ARNs of IAM users/roles that should administer the KMS key
  # Example: "arn:aws:iam::123456789012:user/admin"
]
```

Once you have your variables set, we'll deploy the terraform stack into your environment. It will pick up your default aws credentials if deploying locally. Make sure you have elevated permissions to deploy the stack. 

**Note**: The stack will fail if you deploy with an IAM user. There is a bug in opensearch terraform module that will duplicate your IAM user in a permission and fail. IAM users (generally) should never be used and are not considered best practice. Instead assume a role that has elevated permissions. Instructions can be found [here](https://repost.aws/knowledge-center/iam-assume-role-cli).

Run the following commands.

```bash
# Terraform init
terraform init

# Terraform plan
terraform plan

# Terraform apply to deploy the stack
terraform apply
```

The entire stack takes about ~20 minutes to stand up everything.

## Running Postgres Migrations
To run the migrations from a local machine, we'll need to port forward to Aurora's writer instance before we can run alembic migrations. To do that run the following commands:

1 Find your management instance ID
```bash
# This will give you the management instance ID
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=*bastion-instance*" \
  --query "Reservations[].Instances[].InstanceId" \
  --output text
```

2. Find the master password (stored and rotated in SecretsManager)
```bash
# Get the cluster identifier
CLUSTER_ID=$(aws rds describe-db-clusters --query 'DBClusters[?contains(DBClusterIdentifier, `postgres`)].DBClusterIdentifier' --output text)

# Find the secret ARN for the master user
SECRET_ARN=$(aws rds describe-db-clusters --db-cluster-identifier $CLUSTER_ID --query 'DBClusters[0].MasterUserSecret.SecretArn' --output text)

aws secretsmanager get-secret-value --secret-id $SECRET_ARN --query 'SecretString' --output text
```

3. Create and update .env file in the project dir
```bash
ENVIRONMENT=local
PG_DATABASE=postgres
PG_USER=postgres
PG_READ_ONLY_USER=postgres
PG_PASSWORD=<ENTER HERE>
PG_READ_ONLY_PASSWORD=<ENTER HERE AGAIN>
PG_CONNECTION_URL=localhost
```

*Note*: If running the `alembic` step below fails because the `PG_DATABASE` variable is not set, use the `export VAR=value` format in the `env` file.


4. Start port forwarding to the aurora writer endpoint on port 5432
```bash
# Port forward through SSM to the writer endpoint
  aws ssm start-session \
  --target i-INSTANCEID \
  --document-name AWS-StartPortForwardingSessionToRemoteHost \
  --parameters 'portNumber=5432,localPortNumber=5432,host=<CLUSTER's WRITER ENDPOINT>'
```

5. Run Migrations
```bash
alembic upgrade head
```

6. Close the port forward
To make sure you don't accidently modify the aurora DB, close the connection. We'll be using the port forwarding in the next section to connect to our EKS cluster

## Deploying Helm Chart
This project uses Helm charts to deploy our agent endpoints to the EKS cluster. We've provided a number of build and deploy scripts to make things simpler. For local deployment you can run them individually on your machine as long as you have AWS access locally. In practice, deployment would look different. Either your CI/CD would run the builds for you, or you'd use a GitOps tool like ArgoCD or Flux.

### Running individually on your local machine
To get this running, we need to do a couple things. 

#### Accessing the EKS Cluster
Because the cluster is private (best practice), if you want to access it from either your local host or through the code-server running on the bastion host. In both cases, we'll have to use the bastion setup using AWS Systems Manager Agent (SSM Agent). Using SSM allows us to keep the bastion host in a private subnet but still connect to it using AWS IAM credentials.

1 Find your management instance ID
```bash
# This will give you the management instance ID
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=*bastion-instance*" \
  --query "Reservations[].Instances[].InstanceId" \
  --output text
```

2 Setup kubeproxy. 
Log into the bastion host using SSM to start kubectl proxy on port 8080

```bash
aws ssm start-session --target i-INSTANCEID

# Switch to ec2-user account
sudo su - ubuntu

# Spin kube proxy on the jump box.
$ nohup kubectl proxy --port=8080 --address='0.0.0.0' --accept-hosts='.*' > /tmp/proxy.log 2>&1 &
```
After you run nohup, you can close the session.

3 Start port forwarding to the kubectl proxy on the astion host.
```bash
# Port forward through SSM to the kubectl proxy running on the management 
$ aws ssm start-session \
  --target i-INSTANCEID \
  --document-name AWS-StartPortForwardingSession \
  --parameters '{"portNumber":["8080"],"localPortNumber":["8080"]}'
```

4 Configure kubectl to use the proxy (in a new terminal on your local machine)
```bash
# Add the new cluster and call it proxy
kubectl config set-cluster eks-proxy --server=http://localhost:8080

# Add the new user (empty in this case)
kubectl config set-credentials eks-proxy-user

# Add the new context
kubectl config set-context eks-proxy --cluster=eks-proxy --user=eks-proxy-user

# Switch to the new context
kubectl config use-context eks-proxy

# Now try your command
kubectl get nodes
```

6 Run the following command to push containers to ecr and deploy helm chart.
```bash
# Make all scripts in the deploy directory executable
chmod +x deploy/*.sh
chmod +x deploy/

# Run the core services deployment script
. ./deploy/deploy-core-services.sh

# Deploy all the agents.
. ./deploy/deploy-all-agents.sh
```

Optionally, you can deploy an individual agent by running
```bash
. ./deploy/deploy-agent <name>
```

Where name corresponds to the service name. Each agent has a corresponding dockerfile that's configured to setup and deploy the agent. If you'd like to add a new agent, create another dockerfile that builds your agent code from source, add it to the list of available services in build-container.sh under VALID_SERVICES and deploy it using the script above.

#### Testing an agent

If you deploy the `langgraph-chat` chart, you'll have the service running on your EKS cluster. To test it, you'll need a JWT token. We've provided a script to create new users and generate tokens.

```
uv run python script/create_test_user.py --user-pool-id <get from TF output> --email <email> --password "password"
```

Now generate a token:

```
uv run python script/get_auth_token.py --username 'user' --password 'password' --client-id <get from TF output>
```

You need to set up a proxy to get to the service port.

```
kubectl port-forward svc/langgraph-chat 8090:80
```

Now you can invoke the `chat` endpoint using curl or your favorite API client. 

* The IP address is `http://localhost:8090/chat`.
* Add a header called `Authorization` and set it to `Bearer <token>`.
* Set the body to a JSON document with a field called `message` that has your prompt.

#### Call the load balancer
The load balancer is internet facing. You can pull the DNS name from the load balancer and execute requests using the oAuth token generated above. We've provided some sample requests to help you get started

##### Call Retrieval Gateway
```javascript
POST <lb-domain>/retrieval-gateway/retrieve
{
    "vectorsearch_request": {
        "query": "Tell me something about open search"
    }
}
```

##### Call LLM Gateway
```javascript
POST <lb-domain>/llm-gateway/model/us.anthropic.claude-3-5-haiku-20241022-v1:0/converse
{
    "system": [{"text": "You are a helpful assistant."}],
    "messages": [{"role": "user", "content": [{"text": "Write a poem for me"}]}]
}
```

##### Call Memory Gateway
Note, if this fails, it's likely because you haven't run the migrations on the database described above.
```javascript
POST <lb-domain>/memory-gateway/memory-gateway/get-session-context
{
    "session_id": "e8f9a2d1-6b3c-4d7e-9f8e-1a2b3c4d5e6f"
}
```

##### LangGraph Chat
Note, if this fails, it's likely because you haven't run the migrations on the database described above.
```javascript
POST <lb-domain>/langgraph-chat/chat
{
    "message": "hello"
}
```

##### Pydantic AI Agent
Note, if this fails, it's likely because you haven't run the migrations on the database described above.
```javascript
POST <lb-domain>/pydanticai-agent/invoke
{
    "text": "hello"
}
```



## Deploy OTEL collectors
The otel collectors are CRDs from the ADOT EKS plugin defined in eks.tf terraform. They get deployed in the deploy-core-services.sh file. If you'd like to point them at a different source, there are instructions in the readme of the helm chart.

With the collectors provided, will see log and metrics entries in CloudWatch and traces in X-Ray.

# Run Code Locally

## Pre-Reqs:
* Have Docker installed
* Have the AWS CLI installed

To run code locally, we've provided a docker-compose.yaml file containing some of the dependencies like Valkey and Postgres. To use them you run the docker command in the project root. 
```bash
$ docker compose -f docker-compose.yaml up -d
```

To run the servers you can either (a) use the build-container script and run them locally, or (b) run the servers directly using uvicorn. We've provided a Makefile that can spin up the containers using uv.

```bash
make langgraph-chat
```

# Teardown
To tear down the project, you need to remove the delection protection on two resources, the Aurora DB and the database backup and ensure you load balancer (contolled by K8s is shut down). 

Run this on the bastion host or wherever you deployed helm from. Alternatively you can just delete it from the console. 
```bash
helm uninstall lb-controller
```

## Force deletion of backup
Under postgres.tf, add force_destroy=true
```bash
resource "aws_backup_vault" "postgres" {
  # Add This.
  force_destroy = true
  
  tags = local.common_tags
}
```

Under postgres.tf, switch deletion_protection = false
```bash
resource "aws_rds_cluster" "postgres" {
  # Change This
  deletion_protection = false
}
```

If you ran terraform destroy before making these changes and don't want to re-apply, you can apply those changes just to the backup and Aurora Postgres resources
```bash
terraform apply -target=aws_backup_vault.postgres -target=aws_rds_cluster.postgres
```

Afterwards, you will be able to tear down the resources. 