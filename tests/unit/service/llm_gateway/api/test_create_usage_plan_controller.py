import pytest
from unittest.mock import patch, MagicMock

from agentic_platform.service.llm_gateway.api.create_usage_plan_controller import CreateUsagePlanController
from agentic_platform.service.llm_gateway.models.gateway_api_types import (
    CreateUsagePlanRequest, CreateUsagePlanResponse
)
from agentic_platform.service.llm_gateway.models.usage_types import UsagePlan, UsagePlanEntityType


class TestCreateUsagePlanController:
    """Test CreateUsagePlanController - handles usage plan creation requests"""
    
    @patch('agentic_platform.service.llm_gateway.api.create_usage_plan_controller.UsagePlanClient.create_usage_plan')
    def test_create_usage_plan_with_tenant_id(self, mock_client_create):
        """Test creating usage plan with provided tenant_id"""
        # Setup mock response
        mock_plan = UsagePlan(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["test-model"],
            tenant_id="custom-tenant"
        )
        mock_client_create.return_value = mock_plan
        
        # Create request
        request = CreateUsagePlanRequest(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["test-model"],
            tenant_id="custom-tenant"
        )
        
        # Call controller
        result = CreateUsagePlanController.create(request)
        
        # Verify client was called with proper UsagePlan
        mock_client_create.assert_called_once()
        created_plan = mock_client_create.call_args[0][0]
        assert isinstance(created_plan, UsagePlan)
        assert created_plan.entity_id == "test-entity"
        assert created_plan.tenant_id == "custom-tenant"
        
        # Verify response
        assert isinstance(result, CreateUsagePlanResponse)
        assert result.plan is mock_plan
    
    @patch('agentic_platform.service.llm_gateway.api.create_usage_plan_controller.UsagePlanClient.create_usage_plan')
    def test_create_usage_plan_without_tenant_id_defaults_to_system(self, mock_client_create):
        """Test creating usage plan without tenant_id defaults to 'SYSTEM'"""
        # Setup mock response
        mock_plan = UsagePlan(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.API_KEY,
            model_permissions=["test-model"],
            tenant_id="SYSTEM"
        )
        mock_client_create.return_value = mock_plan
        
        # Create request without tenant_id
        request = CreateUsagePlanRequest(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.API_KEY,
            model_permissions=["test-model"]
            # No tenant_id provided
        )
        
        # Call controller
        result = CreateUsagePlanController.create(request)
        
        # Verify client was called with 'SYSTEM' tenant_id
        mock_client_create.assert_called_once()
        created_plan = mock_client_create.call_args[0][0]
        assert created_plan.tenant_id == "SYSTEM"
        
        # Verify response
        assert isinstance(result, CreateUsagePlanResponse)
        assert result.plan is mock_plan
    
    @patch('agentic_platform.service.llm_gateway.api.create_usage_plan_controller.UsagePlanClient.create_usage_plan')
    def test_create_usage_plan_with_empty_tenant_id_defaults_to_system(self, mock_client_create):
        """Test creating usage plan with empty tenant_id defaults to 'SYSTEM'"""
        # Setup mock response
        mock_plan = UsagePlan(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["test-model"],
            tenant_id="SYSTEM"
        )
        mock_client_create.return_value = mock_plan
        
        # Create request with empty tenant_id
        request = CreateUsagePlanRequest(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["test-model"],
            tenant_id=""  # Empty string
        )
        
        # Call controller
        result = CreateUsagePlanController.create(request)
        
        # Verify client was called with 'SYSTEM' tenant_id
        mock_client_create.assert_called_once()
        created_plan = mock_client_create.call_args[0][0]
        assert created_plan.tenant_id == "SYSTEM"
        
        # Verify response
        assert isinstance(result, CreateUsagePlanResponse)
        assert result.plan is mock_plan
    
    @patch('agentic_platform.service.llm_gateway.api.create_usage_plan_controller.UsagePlanClient.create_usage_plan')
    def test_create_usage_plan_passes_through_client_exceptions(self, mock_client_create):
        """Test that controller passes through exceptions from UsagePlanClient"""
        # Setup client to raise exception
        mock_client_create.side_effect = ValueError("Database connection failed")
        
        # Create request
        request = CreateUsagePlanRequest(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["test-model"]
        )
        
        # Should raise the same exception
        with pytest.raises(ValueError, match="Database connection failed"):
            CreateUsagePlanController.create(request)
        
        # Verify the client was called
        mock_client_create.assert_called_once()
    
    @patch('agentic_platform.service.llm_gateway.api.create_usage_plan_controller.UsagePlanClient.create_usage_plan')
    def test_create_usage_plan_with_all_entity_types(self, mock_client_create):
        """Test creating usage plans for different entity types"""
        entity_types = [
            UsagePlanEntityType.USER,
            UsagePlanEntityType.API_KEY,
            UsagePlanEntityType.SERVICE
        ]
        
        for entity_type in entity_types:
            # Reset mock
            mock_client_create.reset_mock()
            
            # Setup mock response
            mock_plan = UsagePlan(
                entity_id=f"test-{entity_type.value}",
                entity_type=entity_type,
                model_permissions=["test-model"],
                tenant_id="test-tenant"
            )
            mock_client_create.return_value = mock_plan
            
            # Create request
            request = CreateUsagePlanRequest(
                entity_id=f"test-{entity_type.value}",
                entity_type=entity_type,
                model_permissions=["test-model"],
                tenant_id="test-tenant"
            )
            
            # Call controller
            result = CreateUsagePlanController.create(request)
            
            # Verify client was called
            mock_client_create.assert_called_once()
            created_plan = mock_client_create.call_args[0][0]
            assert created_plan.entity_type == entity_type
            
            # Verify response
            assert isinstance(result, CreateUsagePlanResponse)
            assert result.plan.entity_type == entity_type
    
    def test_create_method_signature(self):
        """Test the create method signature"""
        import inspect
        
        method = getattr(CreateUsagePlanController, 'create')
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())
        
        # Should have request parameter (not cls if not classmethod)
        assert 'request' in params
    
    def test_controller_class_structure(self):
        """Test the controller class structure"""
        # Should have only the create method
        methods = [method for method in dir(CreateUsagePlanController) 
                  if not method.startswith('_')]
        assert 'create' in methods
        
        # Should be callable
        assert callable(CreateUsagePlanController.create)
    
    @patch('agentic_platform.service.llm_gateway.api.create_usage_plan_controller.UsagePlanClient.create_usage_plan')
    def test_create_usage_plan_applies_model_defaults(self, mock_client_create):
        """Test that UsagePlan model defaults are applied during validation"""
        # Setup mock response
        mock_plan = UsagePlan(
            entity_id="defaults-test",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["test-model"]
        )
        mock_client_create.return_value = mock_plan
        
        # Create request with minimal data
        request = CreateUsagePlanRequest(
            entity_id="defaults-test",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["test-model"]
        )
        
        # Call controller
        result = CreateUsagePlanController.create(request)
        
        # Verify defaults were applied
        mock_client_create.assert_called_once()
        created_plan = mock_client_create.call_args[0][0]
        assert created_plan.tenant_id == "SYSTEM"  # Default value
        assert created_plan.active is True  # Default value
        
        # Verify response
        assert isinstance(result, CreateUsagePlanResponse)
        assert result.plan is mock_plan
    
    @patch('agentic_platform.service.llm_gateway.api.create_usage_plan_controller.UsagePlanClient.create_usage_plan')
    def test_create_usage_plan_preserves_request_data(self, mock_client_create):
        """Test that data from request is properly preserved in UsagePlan"""
        # Setup mock response
        mock_plan = UsagePlan(
            entity_id="preserve-test",
            entity_type=UsagePlanEntityType.SERVICE,
            model_permissions=["model1", "model2"],
            tenant_id="preserve-tenant"
        )
        mock_client_create.return_value = mock_plan
        
        # Create request with full data
        request = CreateUsagePlanRequest(
            entity_id="preserve-test",
            entity_type=UsagePlanEntityType.SERVICE,
            model_permissions=["model1", "model2"],
            tenant_id="preserve-tenant",
            active=False
        )
        
        # Call controller
        result = CreateUsagePlanController.create(request)
        
        # Verify all request data was preserved
        mock_client_create.assert_called_once()
        created_plan = mock_client_create.call_args[0][0]
        assert created_plan.entity_id == "preserve-test"
        assert created_plan.entity_type == UsagePlanEntityType.SERVICE
        assert created_plan.model_permissions == ["model1", "model2"]
        assert created_plan.tenant_id == "preserve-tenant"
        assert created_plan.active is False
        
        # Verify response
        assert isinstance(result, CreateUsagePlanResponse)
        assert result.plan is mock_plan 