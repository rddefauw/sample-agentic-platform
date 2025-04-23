import os
import boto3

def get_redis_password():
    if os.getenv('REDIS_PASSWORD'):
        return os.getenv('REDIS_PASSWORD')
    else:
        secret_manager = boto3.client('secretsmanager')
        secret_arn = os.getenv('REDIS_PASSWORD_SECRET_ARN')
        response = secret_manager.get_secret_value(SecretId=secret_arn)
        return response['SecretString']