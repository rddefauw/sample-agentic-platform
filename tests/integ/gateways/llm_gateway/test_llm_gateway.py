"""
Integration tests for LLM Gateway.

This module contains integration tests for the LLM Gateway service,
testing the controller functionality with mocked external dependencies.
"""

import pytest
import sys
import os
from typing import Dict, Any
import uuid
from unittest.mock import patch, MagicMock

# Add the source directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../', 'src'))

from agentic_platform.service.llm_gateway.models.gateway_api_types import ConverseRequest, ConverseResponse
from agentic_platform.service.llm_gateway.models.usage_types import UsagePlan, UsagePlanEntityType, RateLimits

class TestLLMGateway:
    """Integration tests for LLM Gateway controller with mocked external dependencies"""
    
    @pytest.mark.asyncio
    async def test_converse_happy_path(self):
        """Test the converse controller happy path"""
        
        # Create a mock response for the Bedrock client
        mock_response = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "text",
                            "text": "Hello! How can I help you today?"
                        }
                    ]
                },
                "stopReason": "end_turn",
                "usage": {
                    "inputTokens": 10,
                    "outputTokens": 8,
                    "totalTokens": 18
                }
            }
        }
        
        # Create a sample request
        request = ConverseRequest(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            messages=[
                {
                    "role": "user", 
                    "content": [{"text": "Hello, how are you?"}]
                }
            ],
            inferenceConfig={
                "maxTokens": 100,
                "temperature": 0.7
            }
        )
        
        # Create a sample usage plan
        usage_plan = UsagePlan(
            entity_id="test-user",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["anthropic.claude-3-sonnet-20240229-v1:0"],
            model_limits={
                "anthropic.claude-3-sonnet-20240229-v1:0": RateLimits(
                    requests_per_minute=10,
                    tokens_per_minute=1000
                )
            },
            default_limits=RateLimits(
                requests_per_minute=5,
                tokens_per_minute=500
            ),
            active=True
        )
        
        try:
            from agentic_platform.service.llm_gateway.api.converse_controller import ConverseController
            from agentic_platform.service.llm_gateway.client.bedrock_client import BedrockClient
            
            # Mock the Bedrock client
            with patch.object(BedrockClient, 'converse', return_value=mock_response) as mock_bedrock, \
                 patch('agentic_platform.service.llm_gateway.api.base_llm_controller.RateLimiter.check_limit') as mock_check_limit:
                
                # Set up the mock rate limiter to allow the request
                mock_check_limit.return_value = MagicMock(allowed=True)
                
                # Call the controller
                response = await ConverseController.converse(request, usage_plan)
                
                # Verify the response
                assert response == mock_response, "Response should match the mock response"
                
                # Verify that the Bedrock client was called with the correct request
                mock_bedrock.assert_called_once_with(request)
                
                print(f"✅ LLM Gateway converse test passed!")
                print(f"   Response contains output with message")
                
        except ImportError as e:
            pytest.skip(f"LLM Gateway controller not available: {e}")
        except Exception as e:
            pytest.fail(f"Error testing LLM Gateway controller: {e}")
    
    @pytest.mark.asyncio
    async def test_converse_with_custom_model(self):
        """Test the converse controller with a custom model ID"""
        
        # Create a mock response for the Bedrock client
        mock_response = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "text",
                            "text": "The capital of France is Paris."
                        }
                    ]
                },
                "stopReason": "end_turn",
                "usage": {
                    "inputTokens": 12,
                    "outputTokens": 10,
                    "totalTokens": 22
                }
            }
        }
        
        # Create a request with a specific model ID
        request = ConverseRequest(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            messages=[
                {
                    "role": "user", 
                    "content": [{"text": "What is the capital of France?"}]
                }
            ],
            inferenceConfig={
                "maxTokens": 100,
                "temperature": 0.0  # Use deterministic output for testing
            }
        )
        
        # Create a sample usage plan
        usage_plan = UsagePlan(
            entity_id="test-user",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["anthropic.claude-3-sonnet-20240229-v1:0"],
            model_limits={
                "anthropic.claude-3-sonnet-20240229-v1:0": RateLimits(
                    requests_per_minute=10,
                    tokens_per_minute=1000
                )
            },
            default_limits=RateLimits(
                requests_per_minute=5,
                tokens_per_minute=500
            ),
            active=True
        )
        
        try:
            from agentic_platform.service.llm_gateway.api.converse_controller import ConverseController
            from agentic_platform.service.llm_gateway.client.bedrock_client import BedrockClient
            
            # Mock the Bedrock client
            with patch.object(BedrockClient, 'converse', return_value=mock_response) as mock_bedrock, \
                 patch('agentic_platform.service.llm_gateway.api.base_llm_controller.RateLimiter.check_limit') as mock_check_limit:
                
                # Set up the mock rate limiter to allow the request
                mock_check_limit.return_value = MagicMock(allowed=True)
                
                # Call the controller
                response = await ConverseController.converse(request, usage_plan)
                
                # Verify the response
                assert response == mock_response, "Response should match the mock response"
                
                # Verify that the Bedrock client was called with the correct model ID
                mock_bedrock.assert_called_once()
                call_args = mock_bedrock.call_args[0][0]
                assert call_args.modelId == "anthropic.claude-3-sonnet-20240229-v1:0", "Model ID should match the request"
                
                # The response should contain "Paris" somewhere in the message
                message = response["output"]["message"]["content"][0]["text"]
                assert "Paris" in message, f"Expected 'Paris' in response message, got: {message}"
                
                print(f"✅ LLM Gateway converse with custom model test passed!")
                print(f"   Response contains expected answer about Paris")
                
        except ImportError as e:
            pytest.skip(f"LLM Gateway controller not available: {e}")
        except Exception as e:
            pytest.fail(f"Error testing LLM Gateway controller: {e}")
    
    @pytest.mark.asyncio
    async def test_converse_with_system_prompt(self):
        """Test the converse controller with a system prompt"""
        
        # Create a mock response for the Bedrock client
        mock_response = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "text",
                            "text": "Quantum computing uses quantum mechanics principles like superposition and entanglement to perform calculations. Unlike classical computers using bits (0 or 1), quantum computers use qubits that can exist in multiple states simultaneously, potentially solving certain problems much faster."
                        }
                    ]
                },
                "stopReason": "end_turn",
                "usage": {
                    "inputTokens": 25,
                    "outputTokens": 40,
                    "totalTokens": 65
                }
            }
        }
        
        # Create a request with a system prompt
        request = ConverseRequest(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            messages=[
                {
                    "role": "system",
                    "content": [{"text": "You are a helpful assistant that responds in a concise manner."}]
                },
                {
                    "role": "user", 
                    "content": [{"text": "Tell me about quantum computing"}]
                }
            ],
            inferenceConfig={
                "maxTokens": 150,
                "temperature": 0.7
            }
        )
        
        # Create a sample usage plan
        usage_plan = UsagePlan(
            entity_id="test-user",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["anthropic.claude-3-sonnet-20240229-v1:0"],
            model_limits={
                "anthropic.claude-3-sonnet-20240229-v1:0": RateLimits(
                    requests_per_minute=10,
                    tokens_per_minute=1000
                )
            },
            default_limits=RateLimits(
                requests_per_minute=5,
                tokens_per_minute=500
            ),
            active=True
        )
        
        try:
            from agentic_platform.service.llm_gateway.api.converse_controller import ConverseController
            from agentic_platform.service.llm_gateway.client.bedrock_client import BedrockClient
            
            # Mock the Bedrock client
            with patch.object(BedrockClient, 'converse', return_value=mock_response) as mock_bedrock, \
                 patch('agentic_platform.service.llm_gateway.api.base_llm_controller.RateLimiter.check_limit') as mock_check_limit:
                
                # Set up the mock rate limiter to allow the request
                mock_check_limit.return_value = MagicMock(allowed=True)
                
                # Call the controller
                response = await ConverseController.converse(request, usage_plan)
                
                # Verify the response
                assert response == mock_response, "Response should match the mock response"
                
                # Verify that the Bedrock client was called with the correct messages
                mock_bedrock.assert_called_once()
                call_args = mock_bedrock.call_args[0][0]
                assert len(call_args.messages) == 2, "Should have two messages (system and user)"
                assert call_args.messages[0]["role"] == "system", "First message should be system"
                assert call_args.messages[1]["role"] == "user", "Second message should be user"
                
                # Check that we got a response
                message = response["output"]["message"]["content"][0]["text"]
                assert len(message) > 0, "Response message should not be empty"
                assert "quantum" in message.lower(), "Response should mention quantum computing"
                
                print(f"✅ LLM Gateway converse with system prompt test passed!")
                print(f"   Response contains non-empty message about quantum computing")
                
        except ImportError as e:
            pytest.skip(f"LLM Gateway controller not available: {e}")
        except Exception as e:
            pytest.fail(f"Error testing LLM Gateway controller: {e}")
