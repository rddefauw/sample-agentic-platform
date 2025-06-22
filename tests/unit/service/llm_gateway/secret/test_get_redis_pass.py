import pytest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError

from agentic_platform.service.llm_gateway.secret.get_redis_pass import get_redis_password


class TestGetRedisPassword:
    """Test get_redis_password function"""
    
    @patch('agentic_platform.service.llm_gateway.secret.get_redis_pass.os.getenv')
    def test_get_redis_password_direct_env_var(self, mock_getenv):
        """Test successful Redis password retrieval from direct env var"""
        # Setup environment variables - REDIS_PASSWORD takes priority
        mock_getenv.side_effect = lambda key: {
            'REDIS_PASSWORD': 'direct-password-123'
        }.get(key)
        
        # Call function
        result = get_redis_password()
        
        # Should return direct password
        assert result == 'direct-password-123'
    
    @patch('agentic_platform.service.llm_gateway.secret.get_redis_pass.boto3')
    @patch('agentic_platform.service.llm_gateway.secret.get_redis_pass.os.getenv')
    def test_get_redis_password_from_secrets_manager(self, mock_getenv, mock_boto3):
        """Test Redis password retrieval from secrets manager"""
        # Setup environment variables - no REDIS_PASSWORD, use secret ARN
        mock_getenv.side_effect = lambda key: {
            'REDIS_PASSWORD': None,
            'REDIS_PASSWORD_SECRET_ARN': 'arn:aws:secretsmanager:region:account:secret:redis-password'
        }.get(key)
        
        # Setup boto3 secrets manager client
        mock_secrets_client = MagicMock()
        mock_secrets_client.get_secret_value.return_value = {
            'SecretString': 'secret-password-456'
        }
        mock_boto3.client.return_value = mock_secrets_client
        
        # Call function
        result = get_redis_password()
        
        # Verify boto3 client creation
        mock_boto3.client.assert_called_once_with('secretsmanager')
        
        # Verify secret retrieval
        mock_secrets_client.get_secret_value.assert_called_once_with(
            SecretId='arn:aws:secretsmanager:region:account:secret:redis-password'
        )
        
        # Verify result
        assert result == 'secret-password-456'
    
    @patch('agentic_platform.service.llm_gateway.secret.get_redis_pass.boto3')
    @patch('agentic_platform.service.llm_gateway.secret.get_redis_pass.os.getenv')
    def test_get_redis_password_missing_env_vars(self, mock_getenv, mock_boto3):
        """Test Redis password retrieval with missing environment variables"""
        # Setup missing environment variables
        mock_getenv.return_value = None
        
        # Call function - should handle gracefully
        result = get_redis_password()
        
        # Should call boto3 with None SecretId
        mock_boto3.client.assert_called_once_with('secretsmanager')
    
    @patch('agentic_platform.service.llm_gateway.secret.get_redis_pass.boto3')
    @patch('agentic_platform.service.llm_gateway.secret.get_redis_pass.os.getenv')
    def test_get_redis_password_secrets_manager_error(self, mock_getenv, mock_boto3):
        """Test Redis password retrieval with secrets manager error"""
        # Setup environment variables
        mock_getenv.side_effect = lambda key: {
            'REDIS_PASSWORD': None,
            'REDIS_PASSWORD_SECRET_ARN': 'arn:aws:secretsmanager:region:account:secret:redis-password'
        }.get(key)
        
        # Setup boto3 secrets manager client to raise exception
        mock_secrets_client = MagicMock()
        mock_secrets_client.get_secret_value.side_effect = Exception("Secrets Manager service unavailable")
        mock_boto3.client.return_value = mock_secrets_client
        
        # Call function - should propagate exception
        with pytest.raises(Exception):
            get_redis_password()
    
    @patch('agentic_platform.service.llm_gateway.secret.get_redis_pass.boto3')
    @patch('agentic_platform.service.llm_gateway.secret.get_redis_pass.os.getenv')
    def test_get_redis_password_secret_not_found(self, mock_getenv, mock_boto3):
        """Test Redis password retrieval when secret doesn't exist"""
        # Setup environment variables
        mock_getenv.side_effect = lambda key: {
            'REDIS_PASSWORD': None,
            'REDIS_PASSWORD_SECRET_ARN': 'arn:aws:secretsmanager:region:account:secret:nonexistent'
        }.get(key)
        
        # Setup boto3 secrets manager client to raise ResourceNotFoundException
        mock_secrets_client = MagicMock()
        error_response = {
            'Error': {
                'Code': 'ResourceNotFoundException',
                'Message': 'Secrets Manager can\'t find the specified secret'
            }
        }
        mock_secrets_client.get_secret_value.side_effect = ClientError(error_response, 'GetSecretValue')
        mock_boto3.client.return_value = mock_secrets_client
        
        # Call function - should propagate exception
        with pytest.raises(ClientError):
            get_redis_password()
    
    @patch('agentic_platform.service.llm_gateway.secret.get_redis_pass.boto3')
    @patch('agentic_platform.service.llm_gateway.secret.get_redis_pass.os.getenv')
    def test_get_redis_password_access_denied(self, mock_getenv, mock_boto3):
        """Test Redis password retrieval with access denied error"""
        # Setup environment variables
        mock_getenv.side_effect = lambda key: {
            'REDIS_PASSWORD': None,
            'REDIS_PASSWORD_SECRET_ARN': 'arn:aws:secretsmanager:region:account:secret:restricted'
        }.get(key)
        
        # Setup boto3 secrets manager client to raise AccessDeniedException
        mock_secrets_client = MagicMock()
        error_response = {
            'Error': {
                'Code': 'AccessDeniedException',
                'Message': 'User is not authorized to access this resource'
            }
        }
        mock_secrets_client.get_secret_value.side_effect = ClientError(error_response, 'GetSecretValue')
        mock_boto3.client.return_value = mock_secrets_client
        
        # Call function - should propagate exception
        with pytest.raises(ClientError):
            get_redis_password()
    
    # Removed function existence test - if function didn't exist, import would fail
    
    @patch('agentic_platform.service.llm_gateway.secret.get_redis_pass.os.getenv')
    def test_get_redis_password_env_var_precedence(self, mock_getenv):
        """Test that REDIS_PASSWORD env var takes precedence"""
        # Setup environment variables with both set
        mock_getenv.side_effect = lambda key: {
            'REDIS_PASSWORD': 'direct-password',
            'REDIS_PASSWORD_SECRET_ARN': 'arn:aws:secretsmanager:region:account:secret:redis-password'
        }.get(key)
        
        # Call function
        result = get_redis_password()
        
        # Should return direct password, not use secrets manager
        assert result == 'direct-password' 