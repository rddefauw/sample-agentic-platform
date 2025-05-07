# Bootstrap
We've provided a bootstrap template written in cloudformation to create the terraform state management files and automatically deploy the infrastructure using a custom resource. We've chosen to bootstrap from cloudformation for simplicity. CFN can be deployed locally or through the AWS cloudformation console. Terraform (optionally) can use a backend provider to persist state. This is generally considered best practice vs. deploying locally. CFN solves the chicken/egg problem of needing a backend provider for your backend by allowing AWS to manage your state through the CloudFormation service. 

## What is deployed
This stack deploys: 
1. An S3 bucket to manage your terraform state
2. An AWS CodeBuild project to deploy the sample agentic platform terraform infrastructure
3. A Lambda acting as a custom resource that will lifecycle the terraform deployment. 
5. (Optional) A KMS key. 

**Warning**: When this stack is torn down, the terraform infrastructure will also be torn down. 

## Getting Started
To get started, you can run this cloudformation by (1) Deploying from your computer or (2) Deploy from the cloudformation console.

### Pre-Reqs
1. An AWS account 
2. An IAM role (not user) you can use give access to the Amazon EKS cluster and has access to your project KMS key.
3. An IAM role (not user) for your CICD pipeline to deploy the terraform via code build. This role must have a trust relationship with codebuild.amazonaws.com and appropriate permissions to deploy infrastructure.

We've intentionally left out the CI/CD role creation in the bootstrap template to give flexibility to the implementor on how they want to configure that role. The role needs elevated priviledges to deploy the terraform infrastructure. You can use tools like AWS IAM Access Analyzer or projects like Role Vending Machine [here](https://github.com/aws-samples/role-vending-machine) to help you create a role with the appropriate permissions.


### Deploying from computer
To deploy from your computer, run the following command in the sample-agentic-platform/bootstrap directory. Make sure to replace your FederatedRoleName parameter with the role you're using. 
```bash
aws cloudformation create-stack \
  --stack-name agentptfm-bootstrap \
  --template-body file://bootstrap.yaml \
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
### Deploying from the console
Navigate to the CloudFormation service in your aws console. Create a new cloudformation stack and upload bootstrap.yaml into the console to deploy. You will prompted to add the the correct role names for the FederatedRoleName and CICDRoleName parameters.

