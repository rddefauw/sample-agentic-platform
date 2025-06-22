import pytest
from unittest.mock import patch, MagicMock, AsyncMock, Mock
from typing import List, Optional
from redis.exceptions import RedisClusterException
import json

from agentic_platform.service.llm_gateway.client.cache_client import RateLimiter
from agentic_platform.service.llm_gateway.models.usage_types import (
    UsagePlan, UsagePlanEntityType, RateLimitResult, RateLimits
)


class TestRateLimiter:
    """Test RateLimiter - Redis-based rate limiting client"""
    
    def test_get_rate_limit_keys_generation(self):
        """Test rate limit key generation for Redis"""
        # Mock time to get predictable keys
        with patch('agentic_platform.service.llm_gateway.client.cache_client.time.time', return_value=1234567890):
            # Window calculation: 1234567890 - (1234567890 % 60) = 1234567860
            expected_window = 1234567860
            
            usage_plan = UsagePlan(
                entity_id="test-entity",
                entity_type=UsagePlanEntityType.USER,
                model_permissions=["test-model"]
            )
            
            keys = RateLimiter._get_rate_limit_keys(usage_plan, "test-model")
            
            # Verify key format
            assert len(keys) == 2
            tenant_key, model_key = keys
            
            # Should contain entity info - first key is global, second includes model
            assert "test-entity" in tenant_key
            assert "USER" in tenant_key
            assert "test-entity" in model_key
            assert "test-model" in model_key
    
    def test_get_usage_plan_key_generation(self):
        """Test usage plan key generation for Redis"""
        entity_id = "test-entity"
        entity_type = UsagePlanEntityType.SERVICE
        
        key = RateLimiter._get_usage_plan_key(entity_id, entity_type)
        
        # Should contain entity details
        assert "test-entity" in key
        assert "SERVICE" in key or "UsagePlanEntityType.SERVICE" in key
    
    @patch('agentic_platform.service.llm_gateway.client.cache_client.RateLimiter.redis')
    @pytest.mark.asyncio
    async def test_cache_usage_plan_success(self, mock_redis):
        """Test successful usage plan caching"""
        mock_redis.setex = AsyncMock(return_value=True)
        
        usage_plan = UsagePlan(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["test-model"],
            tenant_id="test-tenant"
        )
        
        result = await RateLimiter.cache_usage_plan(usage_plan)
        
        # Verify Redis setex was called
        mock_redis.setex.assert_called_once()
        args = mock_redis.setex.call_args[0]
        assert "test-entity" in args[0]  # Key contains entity_id
        assert '"model_permissions":["test-model"]' in args[2]  # Value contains model_permissions (args[2] is the value)
        
        assert result is True
    
    @patch('agentic_platform.service.llm_gateway.client.cache_client.RateLimiter.redis')
    @pytest.mark.asyncio
    async def test_cache_usage_plan_failure(self, mock_redis):
        """Test usage plan caching failure"""
        mock_redis.setex = AsyncMock(side_effect=Exception("Redis connection failed"))
        
        usage_plan = UsagePlan(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["test-model"]
        )
        
        result = await RateLimiter.cache_usage_plan(usage_plan)
        
        assert result is False
    
    @patch('agentic_platform.service.llm_gateway.client.cache_client.RateLimiter.redis')
    @pytest.mark.asyncio
    async def test_get_usage_plan_from_cache_api_key_hashing(self, mock_redis):
        """Test API key hashing when retrieving from cache"""
        # Mock Redis response with hashed key
        mock_redis.get = AsyncMock(return_value='{"entity_id":"hashed-api-key","entity_type":"API_KEY","model_permissions":["test-model"]}')
        
        # Mock hash function
        with patch('agentic_platform.service.llm_gateway.client.cache_client.UsagePlanDB.hash_key', return_value="hashed-api-key"):
            result = await RateLimiter.get_usage_plan_from_cache("raw-api-key", UsagePlanEntityType.API_KEY)
            
            # Should return a UsagePlan
            assert isinstance(result, UsagePlan)
            assert result.entity_id == "hashed-api-key"
    
    @patch('agentic_platform.service.llm_gateway.client.cache_client.RateLimiter.redis')
    @pytest.mark.asyncio
    async def test_check_limit_allowed(self, mock_redis):
        """Test rate limit check when request is allowed"""
        # Mock Redis pipeline operations
        mock_pipe = Mock()
        mock_pipe.hmget.return_value = None  # Pipeline methods return None
        mock_pipe.execute = AsyncMock(return_value=[[10, 20, 1], [5, 10, 1]])  # Current usage below limits
        mock_redis.pipeline = Mock(return_value=mock_pipe)  # Make pipeline method sync
        
        usage_plan = UsagePlan(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["test-model"]
        )
        
        result = await RateLimiter.check_limit(usage_plan, "test-model", 5, 10)
        
        # Should be allowed
        assert isinstance(result, RateLimitResult)
        assert result.allowed is True
    
    @patch('agentic_platform.service.llm_gateway.client.cache_client.RateLimiter.redis')
    @pytest.mark.asyncio
    async def test_check_limit_blocked(self, mock_redis):
        """Test rate limit check when request is blocked"""
        # Mock Redis pipeline operations - high usage
        mock_pipe = Mock()
        mock_pipe.hmget.return_value = None  # Pipeline methods return None
        mock_pipe.execute = AsyncMock(return_value=[[1000, 2000, 100], [500, 1000, 50]])  # Usage above limits
        mock_redis.pipeline = Mock(return_value=mock_pipe)  # Make pipeline method sync
        
        usage_plan = UsagePlan(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["test-model"]
        )
        
        result = await RateLimiter.check_limit(usage_plan, "test-model", 5, 10)
        
        # Should be blocked
        assert isinstance(result, RateLimitResult)
        assert result.allowed is False
    
    @patch('agentic_platform.service.llm_gateway.client.cache_client.RateLimiter.redis')
    @pytest.mark.asyncio
    async def test_check_limit_empty_redis_response(self, mock_redis):
        """Test rate limit check with empty Redis response"""
        # Mock Redis pipeline operations - no current usage
        mock_pipe = Mock()
        mock_pipe.hmget.return_value = None  # Pipeline methods return None
        mock_pipe.execute = AsyncMock(return_value=[None, None])  # No existing usage
        mock_redis.pipeline = Mock(return_value=mock_pipe)  # Make pipeline method sync
        
        usage_plan = UsagePlan(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["test-model"]
        )
        
        result = await RateLimiter.check_limit(usage_plan, "test-model", 5, 10)
        
        # Should be allowed (first request)
        assert isinstance(result, RateLimitResult)
        assert result.allowed is True
    
    @patch('agentic_platform.service.llm_gateway.client.cache_client.RateLimiter.redis')
    @pytest.mark.asyncio
    async def test_record_usage_success(self, mock_redis):
        """Test successful usage recording"""
        # Mock Redis pipeline operations
        mock_pipe = Mock()
        mock_pipe.hincrby.return_value = None  # Pipeline methods return None
        mock_pipe.expire.return_value = None  # Pipeline methods return None
        mock_pipe.execute = AsyncMock(return_value=[1, 1, 1, 1, 1, 1, 1, 1])
        mock_redis.pipeline = Mock(return_value=mock_pipe)  # Make pipeline method sync
        
        usage_plan = UsagePlan(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["test-model"]
        )
        
        result = await RateLimiter.record_usage(usage_plan, "test-model", 100, 200)
        
        # Verify pipeline operations were called
        assert mock_pipe.hincrby.call_count >= 2  # Should increment both tenant and model usage
        assert result is True
    
    @patch('agentic_platform.service.llm_gateway.client.cache_client.RateLimiter.redis')
    @pytest.mark.asyncio
    async def test_record_usage_redis_error(self, mock_redis):
        """Test usage recording with Redis error"""
        # Mock Redis pipeline to raise exception
        mock_pipe = Mock()
        mock_pipe.hincrby.return_value = None  # Pipeline methods return None
        mock_pipe.expire.return_value = None  # Pipeline methods return None
        mock_pipe.execute = AsyncMock(side_effect=RedisClusterException("Redis connection failed"))
        mock_redis.pipeline = Mock(return_value=mock_pipe)  # Make pipeline method sync
        
        usage_plan = UsagePlan(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["test-model"]
        )
        
        result = await RateLimiter.record_usage(usage_plan, "test-model", 50, 75)
        
        # Should handle error gracefully
        assert result is False
    
    @patch('agentic_platform.service.llm_gateway.client.cache_client.RateLimiter.redis')
    @pytest.mark.asyncio
    async def test_record_usage_pipeline_operations(self, mock_redis):
        """Test that record_usage uses correct pipeline operations"""
        # Mock Redis pipeline
        mock_pipe = Mock()
        mock_pipe.hincrby.return_value = None  # Pipeline methods return None
        mock_pipe.expire.return_value = None  # Pipeline methods return None
        mock_pipe.execute = AsyncMock(return_value=[1, 1, 1, 1, 1, 1, 1, 1])
        mock_redis.pipeline = Mock(return_value=mock_pipe)  # Make pipeline method sync
        
        usage_plan = UsagePlan(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["test-model"]
        )
        
        await RateLimiter.record_usage(usage_plan, "test-model", 80, 120)
        
        # Verify hincrby was called with the correct values
        hincrby_calls = mock_pipe.hincrby.call_args_list
        assert len(hincrby_calls) >= 2  # Should have at least tenant and model increments
        
        # Verify expire was called to set TTL
        assert mock_pipe.expire.call_count >= 2
    
    def test_rate_limiter_class_structure(self):
        """Test the RateLimiter class structure"""
        # Should have all expected methods
        expected_methods = [
            '_get_rate_limit_keys',
            '_get_usage_plan_key',
            'cache_usage_plan',
            'get_usage_plan_from_cache',
            'check_limit',
            'record_usage'
        ]
        
        for method in expected_methods:
            assert hasattr(RateLimiter, method)
            # Most methods should be async
            method_obj = getattr(RateLimiter, method)
            if not method.startswith('_'):  # Private methods might not be async
                assert callable(method_obj)
    
    def test_rate_limiter_constants(self):
        """Test RateLimiter constants"""
        assert RateLimiter.WINDOW_SIZE == 60
        assert RateLimiter.USAGE_PLAN_CACHE_TTL == 60 * 60 * 24 * 1  # 1 day
    
    def test_async_methods(self):
        """Test that rate limiter methods are async"""
        import inspect
        
        async_methods = [
            'cache_usage_plan',
            'get_usage_plan_from_cache',
            'check_limit',
            'record_usage'
        ]
        
        for method_name in async_methods:
            method = getattr(RateLimiter, method_name)
            assert inspect.iscoroutinefunction(method), f"{method_name} should be async" 