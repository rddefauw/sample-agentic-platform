import pytest
import asyncio
import os
import sys
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from typing import Dict, Any, Optional
import json
from datetime import datetime

# Mock database and external dependencies at the module level to avoid import issues
os.environ['PG_DATABASE'] = 'test_db'
os.environ['PG_CONNECTION_URL'] = 'localhost:5432'
os.environ['PG_USER'] = 'test_user'
os.environ['PG_READ_ONLY_USER'] = 'test_readonly'
os.environ['PG_PASSWORD'] = 'test_password'
os.environ['PG_READ_ONLY_PASSWORD'] = 'test_readonly_password'
os.environ['ENVIRONMENT'] = 'local'
os.environ['DYNAMODB_USAGE_PLANS_TABLE'] = 'test-usage-plans'
os.environ['DYNAMODB_USAGE_LOGS_TABLE'] = 'test-usage-logs'
os.environ['REDIS_PASSWORD_PARAMETER_NAME'] = '/test/redis/password'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['AWS_ACCESS_KEY_ID'] = 'test-key'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'test-secret'
os.environ['REDIS_URL'] = 'redis://localhost:6379'
os.environ['REDIS_HOST'] = 'localhost'
os.environ['REDIS_PORT'] = '6379'
os.environ['REDIS_PASSWORD'] = 'test-password'
os.environ['OPENSEARCH_ENDPOINT'] = 'https://test-opensearch.com'
os.environ['OPENSEARCH_USERNAME'] = 'test-user'
os.environ['OPENSEARCH_PASSWORD'] = 'test-password'
os.environ['KNOWLEDGE_BASE_ID'] = 'test-kb-123'
os.environ['JWT_SECRET_KEY'] = 'test-jwt-secret-key-for-testing-only'
os.environ['COGNITO_USER_POOL_ID'] = 'test-pool-id'
os.environ['COGNITO_CLIENT_ID'] = 'test-client-id'

# Mock modules at import time
sys.modules['psycopg2'] = MagicMock()
sys.modules['psycopg2.extras'] = MagicMock()
sys.modules['pgvector'] = MagicMock()
sys.modules['pgvector.sqlalchemy'] = MagicMock()

# Mock database dependencies before any imports
@pytest.fixture(autouse=True)
def mock_database_dependencies():
    """Mock all database dependencies to avoid import issues"""
    # Set required environment variables
    test_env = {
        'PG_DATABASE': 'test_db',
        'PG_CONNECTION_URL': 'localhost:5432',
        'PG_USER': 'test_user',
        'PG_READ_ONLY_USER': 'test_readonly',
        'PG_PASSWORD': 'test_password',
        'PG_READ_ONLY_PASSWORD': 'test_readonly_password',
        'ENVIRONMENT': 'local',
        # DynamoDB settings
        'DYNAMODB_USAGE_PLANS_TABLE': 'test-usage-plans',
        'DYNAMODB_USAGE_LOGS_TABLE': 'test-usage-logs',
        'REDIS_PASSWORD_PARAMETER_NAME': '/test/redis/password',
        'AWS_DEFAULT_REGION': 'us-east-1',
        'AWS_ACCESS_KEY_ID': 'test-key',
        'AWS_SECRET_ACCESS_KEY': 'test-secret',
        # Redis settings
        'REDIS_URL': 'redis://localhost:6379',
        'REDIS_HOST': 'localhost',
        'REDIS_PORT': '6379',
        'REDIS_PASSWORD': 'test-password',
        # OpenSearch settings
        'OPENSEARCH_ENDPOINT': 'https://test-opensearch.com',
        'OPENSEARCH_USERNAME': 'test-user',
        'OPENSEARCH_PASSWORD': 'test-password',
        # Knowledge base settings
        'KNOWLEDGE_BASE_ID': 'test-kb-123',
        # Auth settings
        'JWT_SECRET_KEY': 'test-jwt-secret-key-for-testing-only',
        'COGNITO_USER_POOL_ID': 'test-pool-id',
        'COGNITO_CLIENT_ID': 'test-client-id'
    }
    
    # Mock PostgreSQL engine creation
    with patch('sqlalchemy.create_engine') as mock_create_engine, \
         patch('boto3.resource') as mock_boto3_resource, \
         patch('boto3.client') as mock_boto3_client:
        
        # Configure SQLAlchemy mock
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_create_engine.return_value = mock_engine
        
        # Configure the mocks
        mock_table = MagicMock()
        mock_table.get_item.return_value = {'Item': {}}
        mock_table.put_item.return_value = {}
        mock_table.update_item.return_value = {}
        mock_table.query.return_value = {'Items': []}
        
        mock_dynamodb = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3_resource.return_value = mock_dynamodb
        
        mock_boto3_client.return_value = MagicMock()
        
        yield

# Mock SQLAlchemy and database components
@pytest.fixture(autouse=True)
def mock_sqlalchemy_components():
    """Mock SQLAlchemy components to avoid database connections"""
    mock_engine = MagicMock()
    mock_session = MagicMock()
    mock_sessionmaker = MagicMock(return_value=mock_session)
    
    with patch('sqlalchemy.create_engine', return_value=mock_engine), \
         patch('sqlalchemy.orm.sessionmaker', return_value=mock_sessionmaker), \
         patch('sqlalchemy.orm.Session', return_value=mock_session):
        yield

# Mock AWS/DynamoDB components
@pytest.fixture(autouse=True)
def mock_aws_components():
    """Mock AWS components to avoid connection issues"""
    # Mock DynamoDB table
    mock_table = MagicMock()
    mock_table.get_item.return_value = {'Item': {}}
    mock_table.put_item.return_value = {}
    mock_table.update_item.return_value = {}
    mock_table.query.return_value = {'Items': []}
    
    # Mock DynamoDB resource
    mock_dynamodb = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    
    # Mock Bedrock client
    mock_bedrock = MagicMock()
    mock_bedrock.converse.return_value = {
        'output': {
            'message': {
                'role': 'assistant',
                'content': [{'text': 'Test response'}]
            }
        },
        'usage': {'inputTokens': 10, 'outputTokens': 20}
    }
    
    # Mock Redis client
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    
    with patch('boto3.resource', return_value=mock_dynamodb), \
         patch('boto3.client') as mock_boto_client, \
         patch('redis.Redis', return_value=mock_redis):
        # Configure boto3.client to return appropriate mocks
        def client_side_effect(service_name, **kwargs):
            if service_name == 'bedrock-runtime':
                return mock_bedrock
            return MagicMock()
        
        mock_boto_client.side_effect = client_side_effect
        yield

# Test fixtures for common models and data
@pytest.fixture
def sample_agent_request():
    """Sample AgenticRequest for testing"""
    from agentic_platform.core.models.memory_models import Message
    
    return {
        "messages": [Message.from_text("user", "Hello, test message").model_dump()],
        "session_id": "test-session-123",
        "stream": False,
        "context": {"key": "value"},
        "include_thinking": True
    }

@pytest.fixture
def sample_memory():
    """Sample Memory object for testing"""
    return {
        "memory_id": "test-memory-123",
        "session_id": "test-session-123",
        "user_id": "test-user-123",
        "agent_id": "test-agent-123",
        "content": "Test memory content",
        "embedding_model": "test-embedding-model",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "embedding": [0.1, 0.2, 0.3],
        "similarity": 0.85
    }

@pytest.fixture
def sample_session_context():
    """Sample SessionContext for testing"""
    return {
        "session_id": "test-session-123",
        "user_id": "test-user-123",
        "agent_id": "test-agent-123",
        "messages": [],
        "system_prompt": "You are a helpful assistant",
        "session_metadata": {"test": "metadata"}
    }

@pytest.fixture
def sample_converse_request():
    """Sample ConverseRequest for testing"""
    return {
        "modelId": "anthropic.claude-3-haiku-20240307-v1:0",
        "messages": [
            {
                "role": "user",
                "content": [{"text": "Hello, how are you?"}]
            }
        ],
        "inferenceConfig": {
            "maxTokens": 1000,
            "temperature": 0.7
        }
    }

@pytest.fixture
def sample_usage_plan():
    """Sample UsagePlan for testing"""
    return {
        "entity_id": "test-entity-123",
        "entity_type": "USER",
        "rate_limit": 10,
        "daily_limit": 1000,
        "monthly_limit": 30000
    }

@pytest.fixture
def mock_bedrock_client():
    """Mock BedrockClient for testing"""
    mock = MagicMock()
    mock.converse.return_value = {
        "output": {
            "message": {
                "role": "assistant",
                "content": [{"text": "Test response"}]
            }
        },
        "usage": {
            "inputTokens": 10,
            "outputTokens": 20
        }
    }
    return mock

@pytest.fixture
def mock_memory_client():
    """Mock MemoryClient for testing"""
    mock = MagicMock()
    return mock

@pytest.fixture
def mock_retrieval_client():
    """Mock RetrievalClient for testing"""
    mock = MagicMock()
    return mock

@pytest.fixture
def mock_auth_user():
    """Mock authenticated user for testing"""
    return {
        "type": "user",
        "user": {
            "user_id": "test-user-123",
            "username": "testuser"
        }
    }

@pytest.fixture
def mock_auth_service():
    """Mock authenticated service for testing"""
    return {
        "type": "service",
        "service": {
            "service_id": "test-service-123",
            "service_name": "test-service"
        }
    }

# Event loop fixture for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Utility functions for testing
def assert_response_structure(response: Dict, expected_keys: list):
    """Assert that response has expected structure"""
    for key in expected_keys:
        assert key in response, f"Key '{key}' missing from response"

def create_mock_request(state: Optional[Dict] = None):
    """Create a mock FastAPI request with optional state"""
    mock_request = Mock()
    mock_request.state = Mock()
    if state:
        for key, value in state.items():
            setattr(mock_request.state, key, value)
    return mock_request 