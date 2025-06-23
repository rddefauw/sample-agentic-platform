import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Optional

from agentic_platform.service.llm_gateway.api.get_usage_plan_controller import GetUsagePlanController
from agentic_platform.service.llm_gateway.models.usage_types import UsagePlan, UsagePlanEntityType
from agentic_platform.service.llm_gateway.models.gateway_api_types import CreateUsagePlanRequest


class TestGetUsagePlanController:
    """Test GetUsagePlanController - handles usage plan retrieval with caching"""
    
    @patch('agentic_platform.service.llm_gateway.api.get_usage_plan_controller.RateLimiter.get_usage_plan_from_cache')
    @pytest.mark.asyncio
    async def test_get_usage_plan_returns_cached_plan(self, mock_cache_get):
        """Test getting usage plan from cache when available"""
        # Setup cached plan
        cached_plan = UsagePlan(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["test-model"]
        )
        mock_cache_get.return_value = cached_plan
        
        # Call method
        result = await GetUsagePlanController.get_usage_plan("test-entity", UsagePlanEntityType.USER)
        
        # Verify cache was checked
        mock_cache_get.assert_called_once_with("test-entity", UsagePlanEntityType.USER)
        
        # Verify cached plan was returned
        assert result is cached_plan
    
    @patch('agentic_platform.service.llm_gateway.api.get_usage_plan_controller.RateLimiter.cache_usage_plan')
    @patch('agentic_platform.service.llm_gateway.api.get_usage_plan_controller.UsagePlanClient.get_plan_by_id')
    @patch('agentic_platform.service.llm_gateway.api.get_usage_plan_controller.RateLimiter.get_usage_plan_from_cache')
    @pytest.mark.asyncio
    async def test_get_usage_plan_fallback_to_database(self, mock_cache_get, mock_db_get, mock_cache_set):
        """Test getting usage plan from database when not in cache"""
        # Setup cache miss
        mock_cache_get.return_value = None
        
        # Setup database response
        db_plan = UsagePlan(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["test-model"]
        )
        mock_db_get.return_value = db_plan
        mock_cache_set.return_value = True
        
        # Call method
        result = await GetUsagePlanController.get_usage_plan("test-entity", UsagePlanEntityType.USER)
        
        # Verify cache was checked first
        mock_cache_get.assert_called_once_with("test-entity", UsagePlanEntityType.USER)
        
        # Verify database was queried
        mock_db_get.assert_called_once_with("test-entity", UsagePlanEntityType.USER)
        
        # Verify plan was cached
        mock_cache_set.assert_called_once_with(db_plan)
        
        # Verify database plan was returned
        assert result is db_plan
    
    @patch('agentic_platform.service.llm_gateway.api.get_usage_plan_controller.UsagePlanDB.hash_key')
    @patch('agentic_platform.service.llm_gateway.api.get_usage_plan_controller.RateLimiter.get_usage_plan_from_cache')
    @pytest.mark.asyncio
    async def test_get_usage_plan_hashes_api_key(self, mock_cache_get, mock_hash_key):
        """Test that API keys are hashed before lookup"""
        # Setup hash function
        mock_hash_key.return_value = "hashed-api-key"
        mock_cache_get.return_value = None
        
        # Call method with API_KEY entity type
        await GetUsagePlanController.get_usage_plan("raw-api-key", UsagePlanEntityType.API_KEY)
        
        # Verify key was hashed (may be called more than once in the implementation)
        assert mock_hash_key.call_count >= 1
        assert "raw-api-key" in [call[0][0] for call in mock_hash_key.call_args_list]
        
        # Verify cache was checked with hashed key
        mock_cache_get.assert_called_once_with("hashed-api-key", UsagePlanEntityType.API_KEY)
    
    @patch('agentic_platform.service.llm_gateway.api.get_usage_plan_controller.UsagePlanClient.get_plan_by_id')
    @patch('agentic_platform.service.llm_gateway.api.get_usage_plan_controller.RateLimiter.get_usage_plan_from_cache')
    @pytest.mark.asyncio
    async def test_get_usage_plan_returns_none_when_not_found(self, mock_cache_get, mock_db_get):
        """Test returning None when usage plan not found anywhere"""
        # Setup cache miss
        mock_cache_get.return_value = None
        
        # Setup database miss
        mock_db_get.return_value = None
        
        # Call method
        result = await GetUsagePlanController.get_usage_plan("nonexistent", UsagePlanEntityType.USER)
        
        # Verify both cache and database were checked
        mock_cache_get.assert_called_once()
        mock_db_get.assert_called_once()
        
        # Verify None was returned
        assert result is None
    
    @patch('agentic_platform.service.llm_gateway.api.get_usage_plan_controller.CreateUsagePlanController.create')
    @patch.object(GetUsagePlanController, 'get_usage_plan')
    @pytest.mark.asyncio
    async def test_get_or_create_usage_plan_returns_existing(self, mock_get_plan, mock_create):
        """Test get_or_create returns existing plan when found"""
        # Setup existing plan
        existing_plan = UsagePlan(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["test-model"]
        )
        mock_get_plan.return_value = existing_plan
        
        # Call method
        result = await GetUsagePlanController.get_or_create_usage_plan("test-entity", UsagePlanEntityType.USER)
        
        # Verify get_usage_plan was called
        mock_get_plan.assert_called_once_with("test-entity", UsagePlanEntityType.USER)
        
        # Verify create was not called
        mock_create.assert_not_called()
        
        # Verify existing plan was returned
        assert result is existing_plan
    
    @patch('agentic_platform.service.llm_gateway.api.get_usage_plan_controller.CreateUsagePlanController.create')
    @patch.object(GetUsagePlanController, 'get_usage_plan')
    @pytest.mark.asyncio
    async def test_get_or_create_usage_plan_creates_new_when_not_found(self, mock_get_plan, mock_create):
        """Test get_or_create creates new plan when not found"""
        # Setup plan not found
        mock_get_plan.return_value = None
        
        # Setup created plan
        created_plan = UsagePlan(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.SERVICE,
            model_permissions=["test-model"]
        )
        # Mock CreateUsagePlanController.create to return a response object
        mock_response = MagicMock()
        mock_response.plan = created_plan
        mock_create.return_value = mock_response
        
        # Call method
        result = await GetUsagePlanController.get_or_create_usage_plan("test-entity", UsagePlanEntityType.SERVICE)
        
        # Verify get_usage_plan was called first
        mock_get_plan.assert_called_once_with("test-entity", UsagePlanEntityType.SERVICE)
        
        # Verify create was called with correct request
        mock_create.assert_called_once()
        create_request = mock_create.call_args[0][0]
        assert isinstance(create_request, CreateUsagePlanRequest)
        assert create_request.entity_id == "test-entity"
        assert create_request.entity_type == UsagePlanEntityType.SERVICE
        assert create_request.model_permissions == ['*']
        
        # Verify created plan was returned
        assert result is mock_response.plan
    
    @patch('agentic_platform.service.llm_gateway.api.get_usage_plan_controller.RateLimiter.get_usage_plan_from_cache')
    @pytest.mark.asyncio
    async def test_get_usage_plan_with_different_entity_types(self, mock_cache_get):
        """Test getting usage plans for different entity types"""
        entity_types = [
            UsagePlanEntityType.USER,
            UsagePlanEntityType.API_KEY,
            UsagePlanEntityType.SERVICE
        ]
        
        for entity_type in entity_types:
            # Reset mock
            mock_cache_get.reset_mock()
            mock_cache_get.return_value = None
            
            # Call method
            await GetUsagePlanController.get_usage_plan(f"test-{entity_type.value}", entity_type)
            
            # Verify cache was checked
            mock_cache_get.assert_called_once()
    
    def test_get_usage_plan_method_signature(self):
        """Test the get_usage_plan method signature"""
        import inspect
        
        method = getattr(GetUsagePlanController, 'get_usage_plan')
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())
        
        # Should have entity_id, entity_type parameters (not cls if not classmethod)
        assert 'entity_id' in params
        assert 'entity_type' in params
        
        # Should be an async method
        assert inspect.iscoroutinefunction(method)
    
    def test_get_or_create_usage_plan_method_signature(self):
        """Test the get_or_create_usage_plan method signature"""
        import inspect
        
        method = getattr(GetUsagePlanController, 'get_or_create_usage_plan')
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())
        
        # Should have entity_id, entity_type parameters (not cls if not classmethod)
        assert 'entity_id' in params
        assert 'entity_type' in params
        
        # Should be an async method
        assert inspect.iscoroutinefunction(method)
    
    def test_controller_class_structure(self):
        """Test the controller class structure"""
        # Should have expected methods
        expected_methods = ['get_usage_plan', 'get_or_create_usage_plan']
        
        for method in expected_methods:
            assert hasattr(GetUsagePlanController, method)
            assert callable(getattr(GetUsagePlanController, method))
