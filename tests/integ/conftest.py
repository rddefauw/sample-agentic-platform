import pytest
import asyncio
import httpx
from typing import Dict, Any
from fastapi.testclient import TestClient

# Test configuration - assume services are running locally
SERVICE_PORTS = {
    "llm_gateway": 4000,
    "memory_gateway": 4001,
    "retrieval_gateway": 4002,
}

class IntegrationTestClient:
    """Simple HTTP client for integration tests"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    async def get(self, path: str, **kwargs) -> httpx.Response:
        """Make GET request"""
        async with httpx.AsyncClient() as client:
            return await client.get(f"{self.base_url}{path}", **kwargs)
    
    async def post(self, path: str, **kwargs) -> httpx.Response:
        """Make POST request"""
        async with httpx.AsyncClient() as client:
            return await client.post(f"{self.base_url}{path}", **kwargs)

# Service client fixtures
@pytest.fixture
def llm_gateway_client():
    """Client for LLM Gateway service"""
    return IntegrationTestClient(f"http://localhost:{SERVICE_PORTS['llm_gateway']}")

@pytest.fixture
def memory_gateway_client():
    """Client for Memory Gateway service"""
    return IntegrationTestClient(f"http://localhost:{SERVICE_PORTS['memory_gateway']}")

@pytest.fixture
def retrieval_gateway_client():
    """Client for Retrieval Gateway service"""
    return IntegrationTestClient(f"http://localhost:{SERVICE_PORTS['retrieval_gateway']}")

# Test data fixtures
@pytest.fixture
def sample_converse_request():
    """Sample converse request for LLM Gateway"""
    return {
        "messages": [
            {
                "role": "user", 
                "content": [{"text": "Hello, how are you?"}]
            }
        ],
        "inferenceConfig": {
            "maxTokens": 100,
            "temperature": 0.7
        }
    }

@pytest.fixture
def sample_create_memory_request():
    """Sample create memory request for Memory Gateway"""
    return {
        "session_id": "550e8400-e29b-41d4-a716-446655440000",
        "user_id": "550e8400-e29b-41d4-a716-446655440001", 
        "agent_id": "550e8400-e29b-41d4-a716-446655440002",
        "session_context": {
            "session_id": "550e8400-e29b-41d4-a716-446655440000",
            "user_id": "550e8400-e29b-41d4-a716-446655440001",
            "agent_id": "550e8400-e29b-41d4-a716-446655440002",
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": "This is a test memory"}],
                    "tool_calls": [],
                    "tool_results": [],
                    "timestamp": 1640995200.0
                }
            ],
            "system_prompt": "You are a helpful assistant",
            "session_metadata": {"test": True}
        }
    }

@pytest.fixture
def sample_retrieve_request():
    """Sample retrieve request for Retrieval Gateway"""
    return {
        "vectorsearch_request": {
            "query": "test query for retrieval",
            "limit": 5,
            "search_type": "SEMANTIC"
        }
    }

@pytest.fixture
def sample_agent_request():
    """Sample request for agent endpoints"""
    return {
        "messages": [
            {
                "role": "user",
                "content": [{"text": "Hello, this is a test message"}]
            }
        ],
        "session_id": "test-session-123",
        "stream": False,
        "context": {"test": True},
        "include_thinking": False
    }

# Event loop fixture for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
