import pytest
from unittest.mock import patch, MagicMock

from agentic_platform.core.models.memory_models import (
    UpsertSessionContextRequest, UpsertSessionContextResponse, SessionContext
)
from agentic_platform.service.memory_gateway.api.upsert_session_controller import UpsertSessionContextController


class TestUpsertSessionContextController:
    """Test UpsertSessionContextController - a simple delegation controller"""
    
    @patch('agentic_platform.service.memory_gateway.api.upsert_session_controller.MemoryClient.upsert_session_context')
    def test_upsert_session_context_delegates_to_memory_client(self, mock_upsert_session_context):
        """Test that controller properly delegates to MemoryClient.upsert_session_context"""
        # Setup mock session context
        mock_session_context = SessionContext(
            session_id="test-session",
            user_id="test-user", 
            agent_id="test-agent",
            system_prompt="Test system prompt",
            messages=[],
            session_metadata={}
        )
        
        # Setup mock response
        mock_response = UpsertSessionContextResponse(session_context=mock_session_context)
        mock_upsert_session_context.return_value = mock_response
        
        # Create request
        request = UpsertSessionContextRequest(session_context=mock_session_context)
        
        # Call controller
        result = UpsertSessionContextController.upsert_session_context(request)
        
        # Verify delegation
        mock_upsert_session_context.assert_called_once_with(request)
        assert result is mock_response
        assert isinstance(result, UpsertSessionContextResponse)
        assert result.session_context.session_id == "test-session"
    
    @patch('agentic_platform.service.memory_gateway.api.upsert_session_controller.MemoryClient.upsert_session_context')
    def test_upsert_session_context_passes_through_exceptions(self, mock_upsert_session_context):
        """Test that controller passes through exceptions from MemoryClient"""
        # Setup mock to raise exception
        mock_upsert_session_context.side_effect = ValueError("Database connection failed")
        
        # Create session context
        session_context = SessionContext(
            session_id="test-session",
            user_id="test-user",
            system_prompt="Test prompt",
            messages=[]
        )
        
        # Create request
        request = UpsertSessionContextRequest(session_context=session_context)
        
        # Should raise the same exception
        with pytest.raises(ValueError, match="Database connection failed"):
            UpsertSessionContextController.upsert_session_context(request)
        
        # Verify the call was made
        mock_upsert_session_context.assert_called_once_with(request)
    
    def test_controller_is_static_method(self):
        """Test that upsert_session_context is a static method"""
        # Should be able to call without instantiating
        assert hasattr(UpsertSessionContextController, 'upsert_session_context')
        assert callable(UpsertSessionContextController.upsert_session_context)
        
        # Method should not require self parameter
        import inspect
        sig = inspect.signature(UpsertSessionContextController.upsert_session_context)
        params = list(sig.parameters.keys())
        assert 'self' not in params
        assert 'request' in params
        assert len(params) == 1  # Only request parameter
    
    def test_controller_class_structure(self):
        """Test the controller class structure"""
        # Should be a simple class with only the static method
        methods = [method for method in dir(UpsertSessionContextController) 
                  if not method.startswith('_')]
        assert methods == ['upsert_session_context']
        
        # Should not be instantiable (no __init__ needed)
        controller = UpsertSessionContextController()
        assert controller is not None 