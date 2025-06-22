import pytest
from unittest.mock import patch, AsyncMock

from agentic_platform.service.llm_gateway.api.revoke_usage_plan_controller import RevokeUsagePlanController
from agentic_platform.service.llm_gateway.models.gateway_api_types import (
    RevokeUsagePlanRequest, RevokeUsagePlanResponse
)
from agentic_platform.service.llm_gateway.models.usage_types import UsagePlanEntityType


class TestRevokeUsagePlanController:
    """Test RevokeUsagePlanController - handles usage plan revocation requests"""
    
    @patch('agentic_platform.service.llm_gateway.api.revoke_usage_plan_controller.UsagePlanClient.revoke_usage_plan')
    @pytest.mark.asyncio
    async def test_revoke_usage_plan_success(self, mock_client_revoke):
        """Test successful usage plan revocation"""
        # Setup mock response
        mock_client_revoke.return_value = True
        
        # Create request
        request = RevokeUsagePlanRequest(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.USER
        )
        
        # Call controller
        result = await RevokeUsagePlanController.revoke_usage_plan(request)
        
        # Verify client was called
        mock_client_revoke.assert_called_once_with("test-entity", UsagePlanEntityType.USER)
        
        # Verify response
        assert isinstance(result, RevokeUsagePlanResponse)
        assert result.success is True
    
    @patch('agentic_platform.service.llm_gateway.api.revoke_usage_plan_controller.UsagePlanClient.revoke_usage_plan')
    @pytest.mark.asyncio
    async def test_revoke_usage_plan_failure(self, mock_client_revoke):
        """Test usage plan revocation failure"""
        # Setup mock response - failure
        mock_client_revoke.return_value = False
        
        # Create request
        request = RevokeUsagePlanRequest(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.API_KEY
        )
        
        # Call controller
        result = await RevokeUsagePlanController.revoke_usage_plan(request)
        
        # Verify client was called
        mock_client_revoke.assert_called_once_with("test-entity", UsagePlanEntityType.API_KEY)
        
        # Verify response
        assert isinstance(result, RevokeUsagePlanResponse)
        assert result.success is False
    
    @patch('agentic_platform.service.llm_gateway.api.revoke_usage_plan_controller.UsagePlanClient.revoke_usage_plan')
    @pytest.mark.asyncio
    async def test_revoke_usage_plan_with_different_entity_types(self, mock_client_revoke):
        """Test revoking usage plans for different entity types"""
        entity_types = [
            UsagePlanEntityType.USER,
            UsagePlanEntityType.API_KEY,
            UsagePlanEntityType.SERVICE
        ]
        
        for entity_type in entity_types:
            # Reset mock
            mock_client_revoke.reset_mock()
            mock_client_revoke.return_value = True
            
            # Create request
            request = RevokeUsagePlanRequest(
                entity_id=f"test-{entity_type.value}",
                entity_type=entity_type
            )
            
            # Call controller
            result = await RevokeUsagePlanController.revoke_usage_plan(request)
            
            # Verify client was called
            mock_client_revoke.assert_called_once_with(f"test-{entity_type.value}", entity_type)
            
            # Verify response
            assert isinstance(result, RevokeUsagePlanResponse)
            assert result.success is True
    
    @patch('agentic_platform.service.llm_gateway.api.revoke_usage_plan_controller.UsagePlanClient.revoke_usage_plan')
    @pytest.mark.asyncio
    async def test_revoke_usage_plan_passes_through_exceptions(self, mock_client_revoke):
        """Test that controller passes through exceptions from UsagePlanClient"""
        # Setup client to raise exception
        mock_client_revoke.side_effect = Exception("Database connection failed")
        
        # Create request
        request = RevokeUsagePlanRequest(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.USER
        )
        
        # Should raise the same exception
        with pytest.raises(Exception, match="Database connection failed"):
            await RevokeUsagePlanController.revoke_usage_plan(request)
        
        # Verify the client was called
        mock_client_revoke.assert_called_once()
    
    def test_revoke_usage_plan_method_signature(self):
        """Test the revoke_usage_plan method signature"""
        import inspect
        
        method = getattr(RevokeUsagePlanController, 'revoke_usage_plan')
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())
        
        # Should have request parameter (staticmethod)
        assert 'request' in params
        
        # Should be an async method
        assert inspect.iscoroutinefunction(method)
    
    def test_revoke_usage_plan_response_structure(self):
        """Test that RevokeUsagePlanResponse has expected structure"""
        # Test successful response
        success_response = RevokeUsagePlanResponse(
            success=True
        )
        assert success_response.success is True
        
        # Test failure response
        failure_response = RevokeUsagePlanResponse(
            success=False
        )
        assert failure_response.success is False
    
    @patch('agentic_platform.service.llm_gateway.api.revoke_usage_plan_controller.UsagePlanClient.revoke_usage_plan')
    @pytest.mark.asyncio
    async def test_revoke_usage_plan_delegates_correctly(self, mock_client_revoke):
        """Test that controller properly delegates to UsagePlanClient"""
        # Setup mock
        mock_client_revoke.return_value = True
        
        # Create request
        request = RevokeUsagePlanRequest(
            entity_id="delegation-test",
            entity_type=UsagePlanEntityType.SERVICE
        )
        
        # Call controller
        await RevokeUsagePlanController.revoke_usage_plan(request)
        
        # Verify delegation
        mock_client_revoke.assert_called_once_with("delegation-test", UsagePlanEntityType.SERVICE)
    
    def test_controller_class_structure(self):
        """Test the controller class structure"""
        # Should have revoke_usage_plan method
        assert hasattr(RevokeUsagePlanController, 'revoke_usage_plan')
        assert callable(getattr(RevokeUsagePlanController, 'revoke_usage_plan')) 