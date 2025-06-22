import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException

from agentic_platform.service.llm_gateway.api.base_llm_controller import BaseLLMController
from agentic_platform.service.llm_gateway.models.usage_types import (
    RateLimitResult, UsageRecord, UsagePlan, UsagePlanEntityType, RateLimits
)


class TestBaseLLMController:
    """Test BaseLLMController - base class for LLM API controllers with rate limiting"""
    
    def test_estimate_tokens_basic_calculation(self):
        """Test token estimation with basic input"""
        input_text = "Hello world this is a test"  # 6 words
        expected_input = 6 * 1.33  # Approximately 8 tokens
        
        input_tokens, output_tokens = BaseLLMController._estimate_tokens(
            "test-model", input_text
        )
        
        assert input_tokens == expected_input
        assert output_tokens == 256  # Default max_output_tokens
    
    def test_estimate_tokens_with_custom_output(self):
        """Test token estimation with custom max output tokens"""
        input_text = "Short text"  # 2 words
        max_output = 500
        
        input_tokens, output_tokens = BaseLLMController._estimate_tokens(
            "test-model", input_text, max_output
        )
        
        assert input_tokens == 2 * 1.33
        assert output_tokens == max_output
    
    def test_estimate_tokens_empty_input(self):
        """Test token estimation with empty input"""
        input_tokens, output_tokens = BaseLLMController._estimate_tokens(
            "test-model", ""
        )
        
        assert input_tokens == 0
        assert output_tokens == 256
    
    def test_estimate_tokens_single_word(self):
        """Test token estimation with single word"""
        input_tokens, output_tokens = BaseLLMController._estimate_tokens(
            "test-model", "Hello"
        )
        
        assert input_tokens == 1.33
        assert output_tokens == 256
    
    @patch('agentic_platform.service.llm_gateway.api.base_llm_controller.GetUsagePlanController.get_usage_plan')
    @pytest.mark.asyncio
    async def test_get_plan_delegates_to_controller(self, mock_get_usage_plan):
        """Test that _get_plan delegates to GetUsagePlanController"""
        mock_plan = UsagePlan(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["test-model"]
        )
        mock_get_usage_plan.return_value = mock_plan
        
        result = await BaseLLMController._get_plan("test-entity", UsagePlanEntityType.USER)
        
        mock_get_usage_plan.assert_called_once_with("test-entity", UsagePlanEntityType.USER)
        assert result is mock_plan
    
    @patch('agentic_platform.service.llm_gateway.api.base_llm_controller.RateLimiter.check_limit')
    @pytest.mark.asyncio
    async def test_check_rate_limits_allowed(self, mock_check_limit):
        """Test rate limit check when request is allowed"""
        # Setup mock rate limit result
        mock_result = RateLimitResult(
            allowed=True,
            tenant_id="test-tenant",
            model_id="test-model",
            current_usage=RateLimits(),
            model_usage=RateLimits(),
            applied_limits=RateLimits(),
            model_limits=RateLimits()
        )
        mock_check_limit.return_value = mock_result
        
        # Create usage plan
        plan = UsagePlan(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["test-model"]
        )
        
        # Call method
        result = await BaseLLMController.check_rate_limits(plan, "test-model", "test input")
        
        # Verify RateLimiter was called with estimated tokens
        mock_check_limit.assert_called_once()
        args = mock_check_limit.call_args[0]
        assert args[0] is plan
        assert args[1] == "test-model"
        # Should estimate tokens from "test input" (2 words = 2.66 tokens)
        assert args[2] == 2 * 1.33  # input tokens
        assert args[3] == 256  # output tokens
        
        assert result is mock_result
    
    @patch('agentic_platform.service.llm_gateway.api.base_llm_controller.RateLimiter.check_limit')
    @pytest.mark.asyncio
    async def test_check_rate_limits_blocked_raises_http_exception(self, mock_check_limit):
        """Test rate limit check when request is blocked"""
        # Setup mock rate limit result - blocked
        mock_result = RateLimitResult(
            allowed=False,
            tenant_id="test-tenant",
            model_id="test-model",
            current_usage=RateLimits(),
            model_usage=RateLimits(),
            applied_limits=RateLimits(),
            model_limits=RateLimits()
        )
        mock_check_limit.return_value = mock_result
        
        plan = UsagePlan(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["test-model"]
        )
        
        # Should raise HTTPException with 429 status
        with pytest.raises(HTTPException) as exc_info:
            await BaseLLMController.check_rate_limits(plan, "test-model", "test input")
        
        assert exc_info.value.status_code == 429
        assert exc_info.value.detail == "Rate limit exceeded"
    
    @patch('agentic_platform.service.llm_gateway.api.base_llm_controller.RateLimiter.record_usage')
    @pytest.mark.asyncio
    async def test_record_usage_success(self, mock_record_usage):
        """Test successful usage recording"""
        mock_record_usage.return_value = True
        
        plan = UsagePlan(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["test-model"]
        )
        
        usage_record = UsageRecord(
            tenant_id="test-tenant",
            model="test-model",
            input_tokens=100,
            output_tokens=200
        )
        
        result = await BaseLLMController.record_usage(plan, "test-model", usage_record)
        
        mock_record_usage.assert_called_once_with(plan, "test-model", 100, 200)
        assert result is True
    
    @patch('agentic_platform.service.llm_gateway.api.base_llm_controller.RateLimiter.record_usage')
    @pytest.mark.asyncio
    async def test_record_usage_failure(self, mock_record_usage):
        """Test usage recording failure"""
        mock_record_usage.return_value = False
        
        plan = UsagePlan(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["test-model"]
        )
        
        usage_record = UsageRecord(
            tenant_id="test-tenant",
            model="test-model",
            input_tokens=50,
            output_tokens=75
        )
        
        result = await BaseLLMController.record_usage(plan, "test-model", usage_record)
        
        assert result is False
    
    @patch('agentic_platform.service.llm_gateway.api.base_llm_controller.UsageClient.record_usage')
    @pytest.mark.asyncio
    async def test_update_usage_record_success(self, mock_usage_client):
        """Test successful usage record update"""
        mock_usage_client.return_value = True
        
        usage_record = UsageRecord(
            tenant_id="test-tenant",
            model="test-model",
            input_tokens=150,
            output_tokens=300
        )
        
        result = await BaseLLMController.update_usage_record(usage_record)
        
        mock_usage_client.assert_called_once_with(usage_record)
        assert result is True
    
    @patch('agentic_platform.service.llm_gateway.api.base_llm_controller.UsageClient.record_usage')
    @pytest.mark.asyncio
    async def test_update_usage_record_failure(self, mock_usage_client):
        """Test usage record update failure"""
        mock_usage_client.return_value = False
        
        usage_record = UsageRecord(
            tenant_id="test-tenant",
            model="test-model",
            input_tokens=80,
            output_tokens=120
        )
        
        result = await BaseLLMController.update_usage_record(usage_record)
        
        assert result is False
    
    def test_base_controller_class_structure(self):
        """Test the base controller class structure"""
        # Should have all expected methods
        expected_methods = [
            '_estimate_tokens',
            '_get_plan', 
            'check_rate_limits',
            'record_usage',
            'update_usage_record'
        ]
        
        for method in expected_methods:
            assert hasattr(BaseLLMController, method)
            assert callable(getattr(BaseLLMController, method))
    
    def test_estimate_tokens_method_signature(self):
        """Test that _estimate_tokens has the expected parameters"""
        import inspect
        
        method = getattr(BaseLLMController, '_estimate_tokens')
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())
        
        # Should have model_id, input, max_output_tokens parameters
        assert 'model_id' in params
        assert 'input' in params
        assert 'max_output_tokens' in params
    
    def test_async_methods_are_async(self):
        """Test that async methods are properly marked as async"""
        import inspect
        
        async_methods = ['_get_plan', 'check_rate_limits', 'record_usage', 'update_usage_record']
        
        for method_name in async_methods:
            method = getattr(BaseLLMController, method_name)
            assert inspect.iscoroutinefunction(method), f"{method_name} should be async" 