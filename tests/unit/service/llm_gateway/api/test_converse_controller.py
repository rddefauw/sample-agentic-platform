import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from agentic_platform.service.llm_gateway.api.converse_controller import ConverseController
from agentic_platform.service.llm_gateway.models.gateway_api_types import ConverseRequest, ConverseResponse
from agentic_platform.service.llm_gateway.models.usage_types import UsagePlan, UsagePlanEntityType


class TestConverseController:
    """Test ConverseController - handles LLM conversation requests with rate limiting"""
    
    @patch('agentic_platform.service.llm_gateway.api.converse_controller.BedrockClient.converse')
    @patch.object(ConverseController, 'check_rate_limits')
    @pytest.mark.asyncio
    async def test_converse_with_valid_request(self, mock_check_rate_limits, mock_bedrock_converse):
        """Test successful converse request with rate limiting"""
        # Setup mock rate limit check (should not raise)
        mock_check_rate_limits.return_value = AsyncMock()
        
        # Setup mock Bedrock response
        mock_response = ConverseResponse(
            output={'message': {'content': [{'text': 'Hello! How can I help you?'}]}},
            ResponseMetadata={'HTTPStatusCode': 200},
            usage={'inputTokens': 10, 'outputTokens': 15}
        )
        mock_bedrock_converse.return_value = mock_response
        
        # Create request
        request = ConverseRequest(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            messages=[
                {
                    "role": "user",
                    "content": [{"text": "Hello, how are you?"}]
                }
            ]
        )
        
        # Create usage plan
        usage_plan = UsagePlan(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["anthropic.claude-3-sonnet-20240229-v1:0"]
        )
        
        # Call controller
        result = await ConverseController.converse(request, usage_plan)
        
        # Verify rate limiting was checked
        mock_check_rate_limits.assert_called_once_with(
            usage_plan, 
            "anthropic.claude-3-sonnet-20240229-v1:0",
            "Hello, how are you?"
        )
        
        # Verify Bedrock client was called
        mock_bedrock_converse.assert_called_once_with(request)
        
        # Verify response
        assert result is mock_response
        assert isinstance(result, ConverseResponse)
    
    @patch('agentic_platform.service.llm_gateway.api.converse_controller.BedrockClient.converse')
    @patch.object(ConverseController, 'check_rate_limits')
    @pytest.mark.asyncio
    async def test_converse_extracts_user_message_correctly(self, mock_check_rate_limits, mock_bedrock_converse):
        """Test that user message is correctly extracted from complex message structure"""
        mock_check_rate_limits.return_value = AsyncMock()
        mock_bedrock_converse.return_value = ConverseResponse(output={})
        
        # Create request with complex message structure
        request = ConverseRequest(
            modelId="test-model",
            messages=[
                {
                    "role": "system",
                    "content": [{"text": "You are helpful"}]
                },
                {
                    "role": "user", 
                    "content": [{"text": "What is the weather?"}]
                },
                {
                    "role": "assistant",
                    "content": [{"text": "I need more info"}]
                },
                {
                    "role": "user",
                    "content": [{"text": "In New York"}]  # This should be extracted
                }
            ]
        )
        
        usage_plan = UsagePlan(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["test-model"]
        )
        
        # Call controller
        await ConverseController.converse(request, usage_plan)
        
        # Verify the last user message was extracted
        mock_check_rate_limits.assert_called_once_with(
            usage_plan,
            "test-model", 
            "In New York"
        )
    
    @patch('agentic_platform.service.llm_gateway.api.converse_controller.BedrockClient.converse')
    @patch.object(ConverseController, 'check_rate_limits')
    @pytest.mark.asyncio
    async def test_converse_handles_malformed_messages(self, mock_check_rate_limits, mock_bedrock_converse):
        """Test that malformed messages don't crash the controller"""
        mock_check_rate_limits.return_value = AsyncMock()
        mock_bedrock_converse.return_value = ConverseResponse(output={})
        
        # Create request with malformed message structure
        request = ConverseRequest(
            modelId="test-model",
            messages=[
                {
                    "role": "user",
                    "content": []  # Empty content
                }
            ]
        )
        
        usage_plan = UsagePlan(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["test-model"]
        )
        
        # Should not raise exception
        await ConverseController.converse(request, usage_plan)
        
        # Should pass empty string when message extraction fails
        mock_check_rate_limits.assert_called_once_with(
            usage_plan,
            "test-model",
            ""  # Empty string fallback
        )
    
    @patch.object(ConverseController, 'check_rate_limits')
    @pytest.mark.asyncio
    async def test_converse_rate_limit_exception_propagates(self, mock_check_rate_limits):
        """Test that rate limit exceptions are propagated"""
        # Setup rate limit check to raise exception
        mock_check_rate_limits.side_effect = ValueError("Rate limit exceeded")
        
        request = ConverseRequest(
            modelId="test-model",
            messages=[{"role": "user", "content": [{"text": "test"}]}]
        )
        usage_plan = UsagePlan(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["test-model"]
        )
        
        # Should raise the rate limit exception
        with pytest.raises(ValueError, match="Rate limit exceeded"):
            await ConverseController.converse(request, usage_plan)
    
    @patch('agentic_platform.service.llm_gateway.api.converse_controller.BedrockClient.converse')
    @patch.object(ConverseController, 'check_rate_limits')
    @pytest.mark.asyncio
    async def test_converse_bedrock_exception_propagates(self, mock_check_rate_limits, mock_bedrock_converse):
        """Test that Bedrock client exceptions are propagated"""
        mock_check_rate_limits.return_value = AsyncMock()
        
        # Setup Bedrock client to raise exception
        mock_bedrock_converse.side_effect = RuntimeError("Bedrock service unavailable")
        
        request = ConverseRequest(
            modelId="test-model",
            messages=[{"role": "user", "content": [{"text": "test"}]}]
        )
        usage_plan = UsagePlan(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["test-model"]
        )
        
        # Should raise the Bedrock exception
        with pytest.raises(RuntimeError, match="Bedrock service unavailable"):
            await ConverseController.converse(request, usage_plan)
    
    def test_converse_controller_inheritance(self):
        """Test that ConverseController inherits from BaseLLMController"""
        from agentic_platform.service.llm_gateway.api.base_llm_controller import BaseLLMController
        
        assert issubclass(ConverseController, BaseLLMController)
        
        # Should have access to base controller methods
        assert hasattr(ConverseController, 'check_rate_limits')
    
    def test_converse_method_signature(self):
        """Test the converse method signature"""
        import inspect
        
        sig = inspect.signature(ConverseController.converse)
        params = list(sig.parameters.keys())
        
        # Should have request, and usage_plan parameters (not cls if not classmethod)
        assert 'request' in params  
        assert 'usage_plan' in params
        
        # Should be an async method
        assert inspect.iscoroutinefunction(ConverseController.converse) 