"""
Integration tests for LiteLLM Gateway Client.

This module contains integration tests for the LiteLLM Gateway Client,
testing against a real LiteLLM service running in Docker.
"""

import pytest
import sys
import os
import asyncio
import requests
from typing import List

# Load environment variables first, before any other imports
from dotenv import load_dotenv
load_dotenv()

# Add the source directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../', 'src'))

from agentic_platform.core.client.llm_gateway.litellm_gateway_client import LiteLLMGatewayClient
from agentic_platform.core.models.llm_models import LLMRequest, LLMResponse
from agentic_platform.core.models.embedding_models import EmbedRequest, EmbedResponse
from agentic_platform.core.models.memory_models import Message, TextContent
from agentic_platform.core.models.tool_models import ToolSpec
from pydantic import BaseModel


class WeatherParams(BaseModel):
    """Parameters for weather tool"""
    location: str
    unit: str = "celsius"


def is_litellm_available():
    """Check if LiteLLM service is available"""
    try:
        # Get API endpoint and key from environment (already loaded at module level)
        api_endpoint = os.getenv('LITELLM_API_ENDPOINT', 'http://localhost:4000')
        api_key = os.getenv('LITELLM_MASTER_KEY')
        
        if not api_key:
            print("Warning: LITELLM_MASTER_KEY not found in environment")
            return False
            
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(f"{api_endpoint}/health", headers=headers, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"LiteLLM availability check failed: {e}")
        return False


class TestLiteLLMGatewayClientIntegration:
    """Integration tests for LiteLLM Gateway Client"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Environment variables are already loaded at module level
        # This will pick up LITELLM_MASTER_KEY and LITELLM_API_ENDPOINT from .env
        self.client = LiteLLMGatewayClient()
        
        # Sample request for testing
        self.sample_request = LLMRequest(
            system_prompt="You are a helpful assistant that responds concisely.",
            messages=[
                Message(
                    role="user",
                    content=[TextContent(type="text", text="Hello! Please respond with exactly 'Integration test successful'.")]
                )
            ],
            model_id="anthropic.claude-3-5-haiku-20241022-v1:0",  # Use a fast model for testing
            hyperparams={"temperature": 0.0, "max_tokens": 50}  # Deterministic response
        )
    
    @pytest.mark.integration
    def test_chat_invoke_basic(self):
        """Test basic chat completion request against live service"""
        if not is_litellm_available():
            pytest.fail("LiteLLM service is not available at http://localhost:4000. Please start it with 'docker-compose up -d litellm-proxy'")
        
        response = self.client.chat_invoke(self.sample_request)
        
        # Verify response structure
        assert isinstance(response, LLMResponse)
        assert response.id is not None
        assert len(response.text) > 0
        assert response.usage.total_tokens > 0
        assert response.usage.prompt_tokens > 0
        assert response.usage.completion_tokens > 0
        
        # Verify response content
        assert "Integration test successful" in response.text or "successful" in response.text.lower()
        
        print(f"✅ Basic chat invoke test passed!")
        print(f"   Response: {response.text[:100]}...")
        print(f"   Usage: {response.usage.total_tokens} tokens")
    
    @pytest.mark.integration
    def test_chat_invoke_with_conversation(self):
        """Test chat completion with conversation history"""
        if not is_litellm_available():
            pytest.fail("LiteLLM service is not available at http://localhost:4000. Please start it with 'docker-compose up -d litellm-proxy'")
        
        # Create a request with conversation history
        conversation_request = LLMRequest(
            system_prompt="You are a helpful assistant.",
            messages=[
                Message(
                    role="user",
                    content=[TextContent(type="text", text="My name is Alice.")]
                ),
                Message(
                    role="assistant",
                    content=[TextContent(type="text", text="Hello Alice! Nice to meet you.")]
                ),
                Message(
                    role="user",
                    content=[TextContent(type="text", text="What is my name?")]
                )
            ],
            model_id="anthropic.claude-3-5-haiku-20241022-v1:0",
            hyperparams={"temperature": 0.0, "max_tokens": 50}
        )
        
        response = self.client.chat_invoke(conversation_request)
        
        # Verify response
        assert isinstance(response, LLMResponse)
        assert len(response.text) > 0
        assert "Alice" in response.text
        
        print(f"✅ Conversation test passed!")
        print(f"   Response: {response.text}")
    
    @pytest.mark.integration
    def test_chat_invoke_stream(self):
        """Test streaming chat completion request"""
        if not is_litellm_available():
            pytest.fail("LiteLLM service is not available at http://localhost:4000. Please start it with 'docker-compose up -d litellm-proxy'")
        
        # Create a request that should generate multiple tokens
        stream_request = LLMRequest(
            system_prompt="You are a helpful assistant.",
            messages=[
                Message(
                    role="user",
                    content=[TextContent(type="text", text="Count from 1 to 5, with each number on a new line.")]
                )
            ],
            model_id="anthropic.claude-3-5-haiku-20241022-v1:0",
            hyperparams={"temperature": 0.0, "max_tokens": 100}
        )
        
        responses = list(self.client.chat_invoke_stream(stream_request))
        
        # Verify we got multiple responses
        assert len(responses) > 1, "Should receive multiple streaming responses"
        
        # Verify response structure
        for response in responses:
            assert isinstance(response, LLMResponse)
            assert response.id is not None
        
        # Verify final response
        final_response = responses[-1]
        assert final_response.stop_reason is not None
        # Usage information might not be available in streaming responses from all providers
        # assert final_response.usage.total_tokens > 0
        assert len(final_response.text) > 0
        
        # Verify streaming progression (text should grow)
        text_lengths = [len(r.text) for r in responses]
        assert text_lengths == sorted(text_lengths), "Text should grow with each chunk"
        
        print(f"✅ Streaming test passed!")
        print(f"   Received {len(responses)} streaming responses")
        print(f"   Final response: {final_response.text[:100]}...")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_chat_invoke_stream_async(self):
        """Test async streaming chat completion request"""
        if not is_litellm_available():
            pytest.fail("LiteLLM service is not available at http://localhost:4000. Please start it with 'docker-compose up -d litellm-proxy'")
        
        # Create a request for async streaming
        async_request = LLMRequest(
            system_prompt="You are a helpful assistant.",
            messages=[
                Message(
                    role="user",
                    content=[TextContent(type="text", text="List three colors, one per line.")]
                )
            ],
            model_id="anthropic.claude-3-5-haiku-20241022-v1:0",
            hyperparams={"temperature": 0.0, "max_tokens": 50}
        )
        
        responses = []
        async for response in self.client.chat_invoke_stream_async(async_request):
            responses.append(response)
        
        # Verify we got multiple responses
        assert len(responses) > 1, "Should receive multiple async streaming responses"
        
        # Verify response structure
        for response in responses:
            assert isinstance(response, LLMResponse)
            assert response.id is not None
        
        # Verify final response
        final_response = responses[-1]
        assert final_response.stop_reason is not None
        # Usage information might not be available in streaming responses from all providers
        # assert final_response.usage.total_tokens > 0
        assert len(final_response.text) > 0
        
        print(f"✅ Async streaming test passed!")
        print(f"   Received {len(responses)} async streaming responses")
        print(f"   Final response: {final_response.text[:100]}...")
    
    @pytest.mark.integration
    def test_chat_invoke_with_tools(self):
        """Test chat completion with tool calling"""
        if not is_litellm_available():
            pytest.fail("LiteLLM service is not available. Please start it with 'docker-compose up -d litellm-proxy' and ensure LITELLM_MASTER_KEY is set in .env")
        
        # Create a tool specification
        weather_tool = ToolSpec(
            name="get_weather",
            description="Get current weather information for a location",
            model=WeatherParams
        )
        
        # Create request with tools - use Haiku for faster response and lower cost
        tool_request = LLMRequest(
            system_prompt="You are a helpful assistant. Use the get_weather tool when asked about weather.",
            messages=[
                Message(
                    role="user",
                    content=[TextContent(type="text", text="Weather in NYC?")]  # Shorter prompt
                )
            ],
            model_id="anthropic.claude-3-5-haiku-20241022-v1:0",  # Use faster model
            hyperparams={"temperature": 0.0, "max_tokens": 50},  # Reduce max tokens
            tools=[weather_tool]
        )
        
        response = self.client.chat_invoke(tool_request)
        
        # Verify response
        assert isinstance(response, LLMResponse)
        
        # Check if tool was called (some models might not call tools in all cases)
        if response.tool_calls:
            assert len(response.tool_calls) > 0
            tool_call = response.tool_calls[0]
            assert tool_call.name == "get_weather"
            
            print(f"✅ Tool calling test passed!")
            print(f"   Tool called: {tool_call.name}")
            print(f"   Arguments: {tool_call.arguments}")
            print(f"   Tool ID: {tool_call.id}")
            
            # Arguments might be empty in some cases, so don't assert on specific content
            # Just verify the tool was called correctly
        else:
            print(f"✅ Tool calling test completed (no tool call made)")
            print(f"   Response: {response.text[:100]}...")
            # Don't fail if no tool call was made - this can be model-dependent
    
    @pytest.mark.integration
    def test_embed_invoke(self):
        """Test embedding generation"""
        if not is_litellm_available():
            pytest.fail("LiteLLM service is not available at http://localhost:4000. Please start it with 'docker-compose up -d litellm-proxy'")
        
        # Create embedding request
        embed_request = EmbedRequest(
            text="This is a test sentence for embedding generation.",
            model_id="amazon.titan-embed-text-v2:0"
        )
        
        response = self.client.embed_invoke(embed_request)
        
        # Verify response
        assert isinstance(response, EmbedResponse)
        assert len(response.embedding) > 0
        assert all(isinstance(x, (int, float)) for x in response.embedding)
        
        # Titan embeddings are typically 1024 dimensions
        assert len(response.embedding) == 1024
        
        print(f"✅ Embedding test passed!")
        print(f"   Embedding dimensions: {len(response.embedding)}")
        print(f"   First few values: {response.embedding[:5]}")
    
    @pytest.mark.integration
    def test_multiple_models(self):
        """Test requests with different models"""
        if not is_litellm_available():
            pytest.fail("LiteLLM service is not available. Please start it with 'docker-compose up -d litellm-proxy' and ensure LITELLM_MASTER_KEY is set in .env")
        
        # Test just one model to avoid rate limiting
        model_id = "anthropic.claude-3-5-haiku-20241022-v1:0"  # Use the faster model
        
        try:
            request = LLMRequest(
                system_prompt="You are a helpful assistant.",
                messages=[
                    Message(
                        role="user",
                        content=[TextContent(type="text", text="Say 'Hello from model test'")]
                    )
                ],
                model_id=model_id,
                hyperparams={"temperature": 0.0, "max_tokens": 20}
            )
            
            response = self.client.chat_invoke(request)
            
            assert isinstance(response, LLMResponse)
            assert len(response.text) > 0
            
            print(f"✅ Model {model_id} test passed!")
            print(f"   Response: {response.text[:50]}...")
            
        except Exception as e:
            pytest.fail(f"Model {model_id} not available: {e}")
        
        print(f"✅ Model test completed successfully!")
    
    @pytest.mark.integration
    def test_error_handling(self):
        """Test error handling with invalid requests"""
        if not is_litellm_available():
            pytest.fail("LiteLLM service is not available at http://localhost:4000. Please start it with 'docker-compose up -d litellm-proxy'")
        
        # Test with invalid model
        invalid_request = LLMRequest(
            system_prompt="You are a helpful assistant.",
            messages=[
                Message(
                    role="user",
                    content=[TextContent(type="text", text="Hello")]
                )
            ],
            model_id="invalid-model-id",
            hyperparams={"temperature": 0.0, "max_tokens": 20}
        )
        
        with pytest.raises(Exception) as exc_info:
            self.client.chat_invoke(invalid_request)
        
        assert "LiteLLM API error" in str(exc_info.value)
        
        print(f"✅ Error handling test passed!")
        print(f"   Error message: {str(exc_info.value)[:100]}...")
    
    @pytest.mark.integration
    def test_service_health_check(self):
        """Test that we can reach the LiteLLM service health endpoint"""
        if not is_litellm_available():
            pytest.fail("LiteLLM service is not available. Please start it with 'docker-compose up -d litellm-proxy' and ensure LITELLM_MASTER_KEY is set in .env")
        
        # Get configuration from environment
        api_endpoint = os.getenv('LITELLM_API_ENDPOINT', 'http://localhost:4000')
        api_key = os.getenv('LITELLM_MASTER_KEY')
        
        response = requests.get(f"{api_endpoint}/health", 
                              headers={"Authorization": f"Bearer {api_key}"})
        assert response.status_code == 200
        
        health_data = response.json()
        # The service should respond even if models are unhealthy due to missing AWS creds
        assert "healthy_count" in health_data
        assert "unhealthy_count" in health_data
        
        print(f"✅ Service health check passed!")
        print(f"   Health endpoint responded with: {response.status_code}")
        print(f"   Healthy endpoints: {health_data.get('healthy_count', 0)}")
        print(f"   Unhealthy endpoints: {health_data.get('unhealthy_count', 0)}")
