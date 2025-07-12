#!/bin/bash

# set -e  # Exit on any error

echo "========================================="
echo "Deploying LiteLLM"
echo "========================================="

# Function to create litellm user and database
function create_litellm_db {
  echo "========================================="
  echo "Creating LiteLLM Database User"
  echo "========================================="

  # Get bastion instance ID
  echo "🔍 Finding bastion instance..."
  INSTANCE_ID=$(aws ec2 describe-instances \
    --filters "Name=tag:Name,Values=*bastion-instance*" "Name=instance-state-name,Values=running" \
    --query "Reservations[].Instances[].InstanceId" \
    --output text)

  if [ -z "$INSTANCE_ID" ]; then
      echo "❌ Error: Could not find running bastion instance"
      exit 1
  fi

  echo "✅ Found bastion instance: $INSTANCE_ID"

  # Get database information from Parameter Store
  echo "🔍 Getting database information from Parameter Store..."

  # Determine environment (default to 'dev' if not set)
  ENVIRONMENT=${ENVIRONMENT:-dev}
  PARAMETER_PATH="/agentic-platform/config/${ENVIRONMENT}"

  # Get all configuration from parameter store
  CONFIG_JSON=$(aws ssm get-parameter --name "$PARAMETER_PATH" --query 'Parameter.Value' --output text)

  if [ -z "$CONFIG_JSON" ]; then
      echo "❌ Error: Could not retrieve configuration from Parameter Store at path: $PARAMETER_PATH"
      exit 1
  fi

  # Extract database information from the JSON
  WRITER_ENDPOINT=$(echo $CONFIG_JSON | jq -r '.PG_WRITER_ENDPOINT')
  SECRET_ARN=$(echo $CONFIG_JSON | jq -r '.PG_PASSWORD_SECRET_ARN')
  DB_USERNAME=$(echo $CONFIG_JSON | jq -r '.POSTGRES_MASTER_USERNAME')
  CLUSTER_ID=$(echo $CONFIG_JSON | jq -r '.POSTGRES_CLUSTER_ID')
  PG_DATABASE=$(echo $CONFIG_JSON | jq -r '.PG_DATABASE')

  # Get the master password from Secrets Manager
  echo "🔍 Retrieving database credentials from Secrets Manager..."
  DB_CREDENTIALS=$(aws secretsmanager get-secret-value --secret-id $SECRET_ARN --query 'SecretString' --output text)
  DB_PASSWORD=$(echo $DB_CREDENTIALS | jq -r '.password')

  echo "✅ Database information retrieved from Parameter Store"
  echo "   Cluster: $CLUSTER_ID"
  echo "   Endpoint: $WRITER_ENDPOINT"
  echo "   Username: $DB_USERNAME"
  echo "   Database: $PG_DATABASE"

  # Get LiteLLM user password from Secrets Manager
  echo "🔍 Retrieving LiteLLM user password from Secrets Manager..."
  
  # Get AWS account and region
  AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
  AWS_REGION=$(aws configure get region)
  
  # Get the litellm secret ARN from Parameter Store
  PARAMETER_BASE_PATH="/agentic-platform/config"
  LITELLM_CONFIG=$(aws ssm get-parameter --name "${PARAMETER_BASE_PATH}/litellm" --query 'Parameter.Value' --output text 2>/dev/null || echo "{}")
  LITELLM_SECRET_ARN=$(echo $LITELLM_CONFIG | jq -r '.LITELLM_SECRET_ARN // empty')
  
  # If not found in Parameter Store, construct the ARN using the stack prefix
  if [ -z "$LITELLM_SECRET_ARN" ]; then
      STACK_PREFIX=$(echo $CONFIG_JSON | jq -r '.STACK_PREFIX // "agent-ptfm"')
      LITELLM_SECRET_ARN="arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT}:secret:${STACK_PREFIX}-litellm-secret"
      echo "🔍 Constructed LiteLLM secret ARN: $LITELLM_SECRET_ARN"
  fi
  
  # Try to get the secret
  echo "🔍 Retrieving secret from: $LITELLM_SECRET_ARN"
  LITELLM_CREDENTIALS=$(aws secretsmanager get-secret-value --secret-id "${LITELLM_SECRET_ARN}" --query 'SecretString' --output text 2>/dev/null || echo "{}")
  
  # Extract the password
  LITELLM_PASSWORD=$(echo $LITELLM_CREDENTIALS | jq -r '.POSTGRES_PASSWORD // empty')
  
  # If password not found, generate a random one
  if [ -z "$LITELLM_PASSWORD" ]; then
      echo "⚠️ Could not retrieve password from Secrets Manager, generating a random password"
      LITELLM_PASSWORD=$(openssl rand -base64 12)
  else
      echo "✅ LiteLLM user password retrieved from Secrets Manager"
  fi

  # Start port forwarding in background
  echo "🚀 Starting port forwarding to database..."
  aws ssm start-session \
    --target $INSTANCE_ID \
    --document-name AWS-StartPortForwardingSessionToRemoteHost \
    --parameters "portNumber=5432,localPortNumber=5432,host=$WRITER_ENDPOINT" &

  PORT_FORWARD_PID=$!

  # Function to cleanup on exit
  cleanup() {
      echo ""
      echo "🧹 Cleaning up..."
      if [ ! -z "$PORT_FORWARD_PID" ]; then
          kill $PORT_FORWARD_PID 2>/dev/null || true
      fi
      # Clear sensitive environment variables
      unset DB_PASSWORD
      unset LITELLM_PASSWORD
      echo "✅ Cleanup completed"
  }

  # Set trap to cleanup on script exit
  trap cleanup EXIT

  # Wait a moment for port forwarding to establish
  echo "⏳ Waiting for port forwarding to establish..."
  sleep 5

  # Test database connection
  echo "🔍 Testing database connection..."
  if ! timeout 10 bash -c 'until nc -z localhost 5432; do sleep 1; done'; then
      echo "❌ Error: Could not establish connection to database"
      exit 1
  fi

  echo "✅ Database connection established"

  # Check if psql is installed
  if ! command -v psql &> /dev/null; then
      echo "Please install PostgreSQL client manually and try again"
      exit 1
  fi

  # Create a temporary SQL file for user creation
  SQL_FILE=$(mktemp)
  cat > $SQL_FILE << EOF
  -- Check if litellm user exists
  DO \$\$
  BEGIN
      IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'litellm') THEN
          CREATE USER litellm WITH PASSWORD '$LITELLM_PASSWORD';
          RAISE NOTICE 'User litellm created';
      ELSE
          RAISE NOTICE 'User litellm already exists';
          -- Update password for existing user
          ALTER USER litellm WITH PASSWORD '$LITELLM_PASSWORD';
          RAISE NOTICE 'Password for user litellm updated';
      END IF;
  END
  \$\$;
EOF

  # Connect to the default database first to create user
  echo "🚀 Creating/updating litellm user..."
  PGPASSWORD=$DB_PASSWORD psql -h localhost -p 5432 -U $DB_USERNAME -d $PG_DATABASE -f $SQL_FILE

  # Check if litellm_db database exists
  echo "🔍 Checking if litellm_db database exists..."
  DB_EXISTS=$(PGPASSWORD=$DB_PASSWORD psql -h localhost -p 5432 -U $DB_USERNAME -d $PG_DATABASE -tAc "SELECT 1 FROM pg_database WHERE datname='litellm_db'")
  
  # Create database if it doesn't exist
  if [ -z "$DB_EXISTS" ]; then
      echo "🚀 Creating litellm_db database..."
      PGPASSWORD=$DB_PASSWORD psql -h localhost -p 5432 -U $DB_USERNAME -d $PG_DATABASE -c "CREATE DATABASE litellm_db;"
  else
      echo "✅ Database litellm_db already exists"
  fi

  # Grant privileges to the user
  echo "🚀 Granting database privileges to litellm user..."
  PGPASSWORD=$DB_PASSWORD psql -h localhost -p 5432 -U $DB_USERNAME -d $PG_DATABASE -c "GRANT ALL PRIVILEGES ON DATABASE litellm_db TO litellm;"

  # Now connect to the litellm_db database to grant schema permissions
  echo "🚀 Granting schema permissions in litellm_db database..."
  cat > $SQL_FILE << EOF
  -- Grant schema permissions
  GRANT USAGE ON SCHEMA public TO litellm;
  GRANT CREATE ON SCHEMA public TO litellm;
  GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO litellm;
  GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO litellm;
  GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO litellm;
  ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO litellm;
  ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO litellm;
  ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON FUNCTIONS TO litellm;
EOF

  # Execute SQL file on the litellm_db database
  PGPASSWORD=$DB_PASSWORD psql -h localhost -p 5432 -U $DB_USERNAME -d litellm_db -f $SQL_FILE || {
      echo "⚠️ Could not connect to litellm_db database. This might be normal if the database was just created."
      echo "⚠️ Waiting a moment for the database to be ready..."
      sleep 5
      echo "🔄 Retrying connection to litellm_db database..."
      PGPASSWORD=$DB_PASSWORD psql -h localhost -p 5432 -U $DB_USERNAME -d litellm_db -f $SQL_FILE
  }

  # Remove temporary SQL file
  rm $SQL_FILE

  echo ""
  echo "========================================="
  echo "✅ LiteLLM database user setup completed!"
  echo "========================================="
}

# Function to deploy LiteLLM to Kubernetes
function deploy_litellm {
  echo "========================================="
  echo "Deploying LiteLLM to Kubernetes"
  echo "========================================="

  # Create overlay file if it doesn't exist
  OVERLAY_FILE="k8s/helm/values/overlay/aws-overlay-values.yaml"
  if [ ! -f "$OVERLAY_FILE" ]; then
      mkdir -p k8s/helm/values/overlay
      
      AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
      AWS_REGION=$(aws configure get region)
      
      cat > "$OVERLAY_FILE" << EOF
aws:
  account: "$AWS_ACCOUNT"
  region: "$AWS_REGION"
  stackPrefix: "agent-ptfm"
EOF
  fi

  # Deploy with Helm
  echo "Deploying LiteLLM to Kubernetes with Helm..."
  helm upgrade --install litellm ./k8s/helm/charts/litellm \
    -f "$OVERLAY_FILE"

  echo "Deployment complete!"

  # Wait for deployment to be ready
  echo "Waiting for deployment to be ready..."
  # kubectl rollout status deployment/litellm -n default

  echo "========================================="
  echo "✅ LiteLLM deployment completed!"
  echo "========================================="

  # Show the service URL
  echo "LiteLLM service is available at:"
  kubectl get ingress litellm -n default -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
  echo ""
}

# Run the deployment
create_litellm_db
deploy_litellm

echo "========================================="
echo "✅ LiteLLM deployment completed successfully!"
echo "========================================="
