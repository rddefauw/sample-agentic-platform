import pytest
from unittest.mock import patch, MagicMock
from typing import Optional, List

from agentic_platform.service.llm_gateway.client.usage_plan_client import UsagePlanClient
from agentic_platform.service.llm_gateway.models.usage_types import UsagePlan, UsagePlanEntityType


class TestUsagePlanClient:
    """Test UsagePlanClient - abstraction layer over the usage plan database"""
    
    @patch('agentic_platform.service.llm_gateway.client.usage_plan_client.UsagePlanDB.get_plan_by_id')
    def test_get_plan_by_id_success(self, mock_db_get):
        """Test successful plan retrieval by ID"""
        # Setup mock response
        mock_plan = UsagePlan(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["test-model"],
            active=True
        )
        mock_db_get.return_value = mock_plan
        
        # Call method
        result = UsagePlanClient.get_plan_by_id("test-entity", UsagePlanEntityType.USER)
        
        # Verify database call
        mock_db_get.assert_called_once_with("test-entity", UsagePlanEntityType.USER)
        
        # Verify result
        assert result is mock_plan
    
    @patch('agentic_platform.service.llm_gateway.client.usage_plan_client.UsagePlanDB.get_plan_by_id')
    def test_get_plan_by_id_not_found(self, mock_db_get):
        """Test plan retrieval when plan doesn't exist"""
        # Setup mock response - not found
        mock_db_get.return_value = None
        
        # Call method
        result = UsagePlanClient.get_plan_by_id("nonexistent", UsagePlanEntityType.API_KEY)
        
        # Verify database call
        mock_db_get.assert_called_once_with("nonexistent", UsagePlanEntityType.API_KEY)
        
        # Verify result
        assert result is None
    
    @patch('agentic_platform.service.llm_gateway.client.usage_plan_client.UsagePlanDB.create_plan')
    def test_create_usage_plan_success(self, mock_db_create):
        """Test successful usage plan creation"""
        # Setup mock response
        mock_db_create.return_value = True
        
        # Create plan
        plan = UsagePlan(
            entity_id="new-entity",
            entity_type=UsagePlanEntityType.SERVICE,
            model_permissions=["test-model"],
            tenant_id="test-tenant"
        )
        
        # Call method
        result = UsagePlanClient.create_usage_plan(plan)
        
        # Verify database call
        mock_db_create.assert_called_once_with(plan)
        
        # Verify result - returns the original plan
        assert result is plan
        assert result.entity_id == "new-entity"
        assert result.entity_type == UsagePlanEntityType.SERVICE
    
    @patch('agentic_platform.service.llm_gateway.client.usage_plan_client.UsagePlanDB.create_plan')
    def test_create_usage_plan_failure(self, mock_db_create):
        """Test usage plan creation failure"""
        # Setup mock response - failure
        mock_db_create.return_value = False
        
        # Create plan
        plan = UsagePlan(
            entity_id="failing-entity",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["test-model"]
        )
        
        # Call method - should still return the plan even if DB operation fails
        result = UsagePlanClient.create_usage_plan(plan)
        
        # Verify database call
        mock_db_create.assert_called_once_with(plan)
        
        # Verify result - still returns the plan (business logic requirement)
        assert result is plan
    
    @patch('agentic_platform.service.llm_gateway.client.usage_plan_client.UsagePlanDB.deactivate_plan')
    @pytest.mark.asyncio
    async def test_revoke_usage_plan_user_success(self, mock_db_deactivate):
        """Test successful usage plan revocation for USER entity"""
        # Setup mock response
        mock_db_deactivate.return_value = True
        
        # Call method
        result = await UsagePlanClient.revoke_usage_plan("test-user", UsagePlanEntityType.USER)
        
        # Verify database call - no hashing for USER
        mock_db_deactivate.assert_called_once_with(
            entity_id="test-user",
            entity_type=UsagePlanEntityType.USER
        )
        
        # Verify result
        assert result is True
    
    @patch('agentic_platform.service.llm_gateway.client.usage_plan_client.UsagePlanDB.deactivate_plan')
    @patch('agentic_platform.service.llm_gateway.client.usage_plan_client.UsagePlanDB.hash_key')
    @pytest.mark.asyncio
    async def test_revoke_usage_plan_api_key_success(self, mock_hash_key, mock_db_deactivate):
        """Test successful usage plan revocation for API_KEY entity"""
        # Setup mocks
        mock_hash_key.return_value = "hashed-api-key"
        mock_db_deactivate.return_value = True
        
        # Call method
        result = await UsagePlanClient.revoke_usage_plan("raw-api-key", UsagePlanEntityType.API_KEY)
        
        # Verify key was hashed
        mock_hash_key.assert_called_once_with("raw-api-key")
        
        # Verify database call with hashed key
        mock_db_deactivate.assert_called_once_with(
            entity_id="hashed-api-key",
            entity_type=UsagePlanEntityType.API_KEY
        )
        
        # Verify result
        assert result is True
    
    @patch('agentic_platform.service.llm_gateway.client.usage_plan_client.UsagePlanDB.deactivate_plan')
    @pytest.mark.asyncio
    async def test_revoke_usage_plan_failure(self, mock_db_deactivate):
        """Test usage plan revocation failure"""
        # Setup mock response - failure
        mock_db_deactivate.return_value = False
        
        # Call method
        result = await UsagePlanClient.revoke_usage_plan("test-tenant", UsagePlanEntityType.SERVICE)
        
        # Verify database call
        mock_db_deactivate.assert_called_once_with(
            entity_id="test-tenant",
                            entity_type=UsagePlanEntityType.SERVICE
        )
        
        # Verify result
        assert result is False
    
    @patch('agentic_platform.service.llm_gateway.client.usage_plan_client.UsagePlanDB.get_plan_by_id')
    def test_validate_plan_active_user(self, mock_db_get):
        """Test plan validation for active USER plan"""
        # Setup mock response - active plan
        mock_plan = UsagePlan(
            entity_id="test-user",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["test-model"],
            active=True
        )
        mock_db_get.return_value = mock_plan
        
        # Call method
        result = UsagePlanClient.validate_plan("test-user", UsagePlanEntityType.USER)
        
        # Verify database call - no hashing for USER
        mock_db_get.assert_called_once_with(
            entity_id="test-user",
            entity_type=UsagePlanEntityType.USER
        )
        
        # Verify result
        assert result is mock_plan
    
    @patch('agentic_platform.service.llm_gateway.client.usage_plan_client.UsagePlanDB.get_plan_by_id')
    @patch('agentic_platform.service.llm_gateway.client.usage_plan_client.UsagePlanDB.hash_key')
    def test_validate_plan_active_api_key(self, mock_hash_key, mock_db_get):
        """Test plan validation for active API_KEY plan"""
        # Setup mocks
        mock_hash_key.return_value = "hashed-api-key"
        mock_plan = UsagePlan(
            entity_id="hashed-api-key",
            entity_type=UsagePlanEntityType.API_KEY,
            model_permissions=["test-model"],
            active=True
        )
        mock_db_get.return_value = mock_plan
        
        # Call method
        result = UsagePlanClient.validate_plan("raw-api-key", UsagePlanEntityType.API_KEY)
        
        # Verify key was hashed
        mock_hash_key.assert_called_once_with("raw-api-key")
        
        # Verify database call with hashed key
        mock_db_get.assert_called_once_with(
            entity_id="hashed-api-key",
            entity_type=UsagePlanEntityType.API_KEY
        )
        
        # Verify result
        assert result is mock_plan
    
    @patch('agentic_platform.service.llm_gateway.client.usage_plan_client.UsagePlanDB.get_plan_by_id')
    def test_validate_plan_inactive_plan(self, mock_db_get):
        """Test plan validation for inactive plan"""
        # Setup mock response - inactive plan
        mock_plan = UsagePlan(
            entity_id="test-user",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["test-model"],
            active=False
        )
        mock_db_get.return_value = mock_plan
        
        # Call method
        result = UsagePlanClient.validate_plan("test-user", UsagePlanEntityType.USER)
        
        # Verify database call
        mock_db_get.assert_called_once()
        
        # Verify result - should return None for inactive plan
        assert result is None
    
    @patch('agentic_platform.service.llm_gateway.client.usage_plan_client.UsagePlanDB.get_plan_by_id')
    def test_validate_plan_not_found(self, mock_db_get):
        """Test plan validation when plan doesn't exist"""
        # Setup mock response - not found
        mock_db_get.return_value = None
        
        # Call method
        result = UsagePlanClient.validate_plan("nonexistent", UsagePlanEntityType.USER)
        
        # Verify database call
        mock_db_get.assert_called_once_with(
            entity_id="nonexistent",
            entity_type=UsagePlanEntityType.USER
        )
        
        # Verify result
        assert result is None
    
    @patch('agentic_platform.service.llm_gateway.client.usage_plan_client.UsagePlanDB.get_plans_by_tenant')
    def test_get_usage_keys_by_tenant_success(self, mock_db_get_by_tenant):
        """Test successful retrieval of usage keys by tenant"""
        # Setup mock response
        mock_plans = [
            UsagePlan(
                entity_id="entity1",
                entity_type=UsagePlanEntityType.API_KEY,
                model_permissions=["test-model"],
                tenant_id="test-tenant"
            ),
            UsagePlan(
                entity_id="entity2",
                entity_type=UsagePlanEntityType.USER,
                model_permissions=["test-model"],
                tenant_id="test-tenant"
            )
        ]
        mock_db_get_by_tenant.return_value = mock_plans
        
        # Call method
        result = UsagePlanClient.get_usage_keys_by_tenant("test-tenant")
        
        # Verify database call
        mock_db_get_by_tenant.assert_called_once_with("test-tenant")
        
        # Verify result
        assert result is mock_plans
        assert len(result) == 2
        assert all(plan.tenant_id == "test-tenant" for plan in result)
    
    @patch('agentic_platform.service.llm_gateway.client.usage_plan_client.UsagePlanDB.get_plans_by_tenant')
    def test_get_usage_keys_by_tenant_empty(self, mock_db_get_by_tenant):
        """Test retrieval of usage keys for tenant with no plans"""
        # Setup mock response - empty list
        mock_db_get_by_tenant.return_value = []
        
        # Call method
        result = UsagePlanClient.get_usage_keys_by_tenant("empty-tenant")
        
        # Verify database call
        mock_db_get_by_tenant.assert_called_once_with("empty-tenant")
        
        # Verify result
        assert result == []
        assert isinstance(result, list)
    
    def test_usage_plan_client_class_structure(self):
        """Test the UsagePlanClient class structure"""
        # Should have expected methods
        expected_methods = [
            'get_plan_by_id',
            'create_usage_plan',
            'revoke_usage_plan',
            'validate_plan',
            'get_usage_keys_by_tenant'
        ]
        
        for method in expected_methods:
            assert hasattr(UsagePlanClient, method)
            assert callable(getattr(UsagePlanClient, method))
    
    def test_revoke_usage_plan_is_async(self):
        """Test that revoke_usage_plan is async"""
        import inspect
        
        method = getattr(UsagePlanClient, 'revoke_usage_plan')
        assert inspect.iscoroutinefunction(method)
    
    def test_other_methods_are_sync(self):
        """Test that other methods are synchronous"""
        import inspect
        
        sync_methods = [
            'get_plan_by_id',
            'create_usage_plan',
            'validate_plan',
            'get_usage_keys_by_tenant'
        ]
        
        for method_name in sync_methods:
            method = getattr(UsagePlanClient, method_name)
            assert not inspect.iscoroutinefunction(method), f"{method_name} should be sync"
    
    def test_method_signatures(self):
        """Test method signatures are correct"""
        import inspect
        
        # Test get_plan_by_id signature
        sig = inspect.signature(UsagePlanClient.get_plan_by_id)
        params = list(sig.parameters.keys())
        assert 'entity_id' in params
        assert 'entity_type' in params
        
        # Test create_usage_plan signature
        sig = inspect.signature(UsagePlanClient.create_usage_plan)
        params = list(sig.parameters.keys())
        assert 'plan' in params
        
        # Test validate_plan signature
        sig = inspect.signature(UsagePlanClient.validate_plan)
        params = list(sig.parameters.keys())
        assert 'entity_id' in params
        assert 'entity_type' in params 