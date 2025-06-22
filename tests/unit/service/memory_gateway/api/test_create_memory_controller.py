import pytest
from unittest.mock import patch, MagicMock

from agentic_platform.core.models.memory_models import (
    CreateMemoryRequest, CreateMemoryResponse, Memory
)
from agentic_platform.service.memory_gateway.api.create_memory_controller import CreateMemoryController


class TestCreateMemoryController:
    """Test CreateMemoryController - a simple delegation controller"""
    
    @patch('agentic_platform.service.memory_gateway.api.create_memory_controller.MemoryClient.create_memory')
    def test_create_memory_delegates_to_memory_client(self, mock_create_memory):
        """Test that controller properly delegates to MemoryClient.create_memory"""
        # Setup mock response
        mock_memory = Memory(
            session_id="test-session",
            user_id="test-user", 
            agent_id="test-agent",
            content="Test memory content",
            embedding_model="test-model"
        )
        mock_response = CreateMemoryResponse(memory=mock_memory)
        mock_create_memory.return_value = mock_response
        
        # Create session context for the request
        from agentic_platform.core.models.memory_models import SessionContext
        session_context = SessionContext(
            session_id="test-session",
            user_id="test-user",
            messages=[]
        )
        
        # Create request
        request = CreateMemoryRequest(
            user_id="test-user",
            session_id="test-session",
            agent_id="test-agent",
            session_context=session_context
        )
        
        # Call controller
        result = CreateMemoryController.create_memory(request)
        
        # Verify delegation
        mock_create_memory.assert_called_once_with(request)
        assert result is mock_response
        assert isinstance(result, CreateMemoryResponse)
        assert result.memory.content == "Test memory content"
    
    @patch('agentic_platform.service.memory_gateway.api.create_memory_controller.MemoryClient.create_memory')
    def test_create_memory_passes_through_exceptions(self, mock_create_memory):
        """Test that controller passes through exceptions from MemoryClient"""
        # Setup mock to raise exception
        mock_create_memory.side_effect = ValueError("Database connection failed")
        
        # Create session context for the request
        from agentic_platform.core.models.memory_models import SessionContext
        session_context = SessionContext(
            session_id="test-session",
            user_id="test-user",
            messages=[]
        )
        
        # Create request
        request = CreateMemoryRequest(
            user_id="test-user",
            session_id="test-session",
            agent_id="test-agent",
            session_context=session_context
        )
        
        # Should raise the same exception
        with pytest.raises(ValueError, match="Database connection failed"):
            CreateMemoryController.create_memory(request)
        
        # Verify the call was made
        mock_create_memory.assert_called_once_with(request)
    
    def test_controller_is_static_method(self):
        """Test that create_memory is a static method"""
        # Should be able to call without instantiating
        assert hasattr(CreateMemoryController, 'create_memory')
        assert callable(CreateMemoryController.create_memory)
        
        # Method should not require self parameter
        import inspect
        sig = inspect.signature(CreateMemoryController.create_memory)
        params = list(sig.parameters.keys())
        assert 'self' not in params
        assert 'request' in params
        assert len(params) == 1  # Only request parameter
    
    def test_controller_class_structure(self):
        """Test the controller class structure"""
        # Should be a simple class with only the static method
        methods = [method for method in dir(CreateMemoryController) 
                  if not method.startswith('_')]
        assert methods == ['create_memory']
        
        # Should not be instantiable (no __init__ needed)
        controller = CreateMemoryController()
        assert controller is not None 