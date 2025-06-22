import pytest
from unittest.mock import patch, MagicMock

from agentic_platform.core.models.memory_models import (
    GetSessionContextRequest, GetSessionContextResponse, SessionContext
)
from agentic_platform.service.memory_gateway.api.get_session_controller import GetSessionContextController


class TestGetSessionContextController:
    """Test GetSessionContextController - a simple delegation controller"""
    
    @patch('agentic_platform.service.memory_gateway.api.get_session_controller.MemoryClient.get_session_context')
    def test_get_session_context_delegates_to_memory_client(self, mock_get_session_context):
        """Test that controller properly delegates to MemoryClient.get_session_context"""
        # Setup mock response
        mock_session_context = SessionContext(
            session_id="test-session",
            user_id="test-user", 
            agent_id="test-agent",
            system_prompt="Test system prompt",
            messages=[],
            session_metadata={}
        )
        mock_response = GetSessionContextResponse(results=[mock_session_context])
        mock_get_session_context.return_value = mock_response
        
        # Create request
        request = GetSessionContextRequest(
            user_id="test-user",
            session_id="test-session"
        )
        
        # Call controller
        result = GetSessionContextController.get_session_context(request)
        
        # Verify delegation
        mock_get_session_context.assert_called_once_with(request)
        assert result is mock_response
        assert isinstance(result, GetSessionContextResponse)
        assert len(result.results) == 1
        assert result.results[0].session_id == "test-session"
    
    @patch('agentic_platform.service.memory_gateway.api.get_session_controller.MemoryClient.get_session_context')
    def test_get_session_context_passes_through_exceptions(self, mock_get_session_context):
        """Test that controller passes through exceptions from MemoryClient"""
        # Setup mock to raise exception
        mock_get_session_context.side_effect = ValueError("Database connection failed")
        
        # Create request
        request = GetSessionContextRequest(user_id="test-user")
        
        # Should raise the same exception
        with pytest.raises(ValueError, match="Database connection failed"):
            GetSessionContextController.get_session_context(request)
        
        # Verify the call was made
        mock_get_session_context.assert_called_once_with(request)
    
    def test_controller_is_static_method(self):
        """Test that get_session_context is a static method"""
        # Should be able to call without instantiating
        assert hasattr(GetSessionContextController, 'get_session_context')
        assert callable(GetSessionContextController.get_session_context)
        
        # Method should not require self parameter
        import inspect
        sig = inspect.signature(GetSessionContextController.get_session_context)
        params = list(sig.parameters.keys())
        assert 'self' not in params
        assert 'request' in params
        assert len(params) == 1  # Only request parameter
    
    def test_controller_class_structure(self):
        """Test the controller class structure"""
        # Should be a simple class with only the static method
        methods = [method for method in dir(GetSessionContextController) 
                  if not method.startswith('_')]
        assert methods == ['get_session_context']
        
        # Should not be instantiable (no __init__ needed)
        controller = GetSessionContextController()
        assert controller is not None 