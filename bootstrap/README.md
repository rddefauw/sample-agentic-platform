# Bootstrap
We've provided a series of bootstrap scripts and cloudformation templates to get an entire CI/CD pipeline and infrastructure spun up. The bootstrap scripts should be ran in this order:
* infra-boostrap.yaml
* github-bootstrap.yaml
* eks-bootstrap.sh

# 1 Infrastructure Bootstrap
We've provided a bootstrap template written in cloudformation to create the terraform state management files and automatically deploy the infrastructure using a custom resource. We've chosen to bootstrap from cloudformation for simplicity. CFN can be deployed locally or through the AWS cloudformation console. Optionally, you can deploy the terraform from your local machine or anywhere using the terraform plan && terraform apply. We recommend the bootstrap to persist TF state in the cloud. 

### What is deployed
This stack deploys: 
1. An S3 bucket to manage your terraform state
2. An AWS CodeBuild project to deploy the sample agentic platform terraform infrastructure
3. A Lambda acting as a custom resource that will lifecycle the terraform deployment. 
5. (Optional) A KMS key. 

**Warning**: When this stack is torn down, the terraform infrastructure will also be torn down. 

### Getting Started
To get started, you can run this cloudformation by (1) Deploying from your computer or (2) Deploy from the cloudformation console.

#### Pre-Reqs
1. An AWS account 
2. An IAM role (not user) you can use give access to the Amazon EKS cluster and has access to your project KMS key.
3. An IAM role (not user) for your CICD pipeline to deploy the terraform via code build. This role must have a trust relationship with codebuild.amazonaws.com and appropriate permissions to deploy infrastructure.

We've intentionally left out the CI/CD role creation in the bootstrap template to give flexibility to the implementor on how they want to configure that role. The role needs elevated priviledges to deploy the terraform infrastructure. You can use tools like AWS IAM Access Analyzer or projects like Role Vending Machine [here](https://github.com/aws-samples/role-vending-machine) to help you create a role with the appropriate permissions.

4. Create OpenSearch Service linked role
If this is a new account or you've never stood up opensearch, you need to create a service linked role before deploying the stack.

```bash
aws iam create-service-linked-role --aws-service-name opensearchservice.amazonaws.com
```
(If it already exists, that's fine - we just need it present)


#### Deploying from computer
To deploy from your computer, run the following command in the sample-agentic-platform/bootstrap directory. Make sure to replace your FederatedRoleName parameter with the role you're using. 
```bash
aws cloudformation create-stack \
  --stack-name agentptfm-bootstrap \
  --template-body file://infra-bootstrap.yaml \
  --parameters \
    ParameterKey=FederatedRoleName,ParameterValue=<YOUR ROLE NAME> \
    ParameterKey=CICDRoleName,ParameterValue=<YOUR CICD ROLE NAME> \
  --capabilities CAPABILITY_NAMED_IAM
```

> **Note**: The CICD role must have a trust relationship with the CodeBuild service. Make sure the role has the following trust policy:
> ```json
> {
>   "Version": "2012-10-17",
>   "Statement": [
>     {
>       "Effect": "Allow",
>       "Principal": {
>         "Service": "codebuild.amazonaws.com"
>       },
>       "Action": "sts:AssumeRole"
>     }
>   ]
> }
> ```
#### Deploying from the console
Navigate to the CloudFormation service in your aws console. Create a new cloudformation stack and upload bootstrap.yaml into the console to deploy. You will prompted to add the the correct role names for the FederatedRoleName and CICDRoleName parameters.

### Infrastructure Setup Complete
After ~20-30 minutes your infrastructure should be deployed!

# 2 Github Bootstrap
In this section you'll:
* Sign in / up on github.com
* Create a new repository
* Import this repository into your own (private repo)
* Run a bootstrap script to create IAM permissions for github to update containers in AWS
* Configure a repository secret & env variable for our CI pipeline.
* Deploy containers to ECR

To begin, login or sign in to github.com

### Create and Import repository
Next, you'll need to create a private github repository. Create or sign into github.com and follow the create respository instructions [here](https://docs.github.com/en/repositories/creating-and-managing-repositories/quickstart-for-repositories). Make sure that you make the repository private.

Once the respository is created, you can follow these instructions on importing this repository into your newly created one [here](https://docs.github.com/en/migrations/importing-source-code/using-github-importer/importing-a-repository-with-github-importer). You should see a big + sign on the top of your repo page. This will take you to github importer.


### Run Github Bootstrap
We'll be using Github Actions as our CI pipeline. Github will need permissions to deploy our containers to elastic container registry (ECR). To do this, we've provided another cloudformation template to set up those permissions. 

Similar to the infrastructure setup cfn template, you can either run it in the AWS console or locally. To run locally use this command
```bash
aws cloudformation create-stack \
  --stack-name github-bootstrap \
  --template-body file://bootstrap.yaml \
  --parameters \
    ParameterKey=GitHubOrg,ParameterValue=< YOUR ORG or YOUR PERSONAL GITHUB USER ID > \
    ParameterKey=GitHubRepo,ParameterValue=<NAME OF THE REPO YOU JUST CREATED> \
  --capabilities CAPABILITY_NAMED_IAM
```

When the script is done, you should have a github role ARN that we'll use to finish up setup. 

### Configure repository secrets. 
We'll need to configure out github repository secrets so that our pipeline can deploy to ECR. We'll need to add:
* AWS_ROLE_ARN as a repository secret (which you should have from the github bootstrap)
* AWS_REGION as an environment variable (whichever aws region you deployed from)

Follow these instructions on how to find this in the github website [here](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)

### Deploy a change
Lastly, we need to trigger the code pipeline. Navigate to .github/workflows/ecr-push.yml and uncomment the on: section at the top and delete the one that's currently live. You can do this via the github UI or via git commands. This will trigger your CI pipeline which will build your containers and push them to ECR repositories.

And that's it! We've completed the "CI" part of our "CI/CD" pipeline.


# 3 Bootstrapping EKS
Lastly, we'll need to setup our cluster with the components that don't change often like the load balancer controller, secrets operator, and storage configuration.

**Note:** If you are executing this script locally, make sure you're port forwarding through the bastion host like described in DEPLOYMENT.md. If you're already on the bastion host, you can run these directly.

```bash
# Make the script executable
chmod +x ./bootstrap/eks-bootstrap.sh 

# Deploy the clusters essentials via helm
. ./bootstrap/eks-bootstrap.sh
```

And that's it. 

# 4 (Optional) Enable LangFuse. 
Langfuse is an open source llm engineering platform that can be deployed in kubernetes. For this simple, it also provides an additional location to send traces to demonstrate the power of using open telemetry. Without changing your code, you can send your traces to any backend. 

To install langfuse, run the following commands below (Make sure your port forwarding if your deploying locally)

```bash
# Make the script executable
chmod +x ./bootstrap/langfuse-bootstrap.sh 

# Deploy the clusters essentials via helm
. ./bootstrap/langfuse-bootstrap.sh 
```

# Conclusion
After following this readme, you should have the stack deployed, github setup (if you want a CI), and your K8s cluster configured with all the essentials to start deploying your agentic systems. 