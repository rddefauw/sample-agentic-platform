import pytest
from unittest.mock import patch, MagicMock

from agentic_platform.core.models.memory_models import (
    GetMemoriesRequest, GetMemoriesResponse, Memory
)
from agentic_platform.service.memory_gateway.api.get_memory_controller import GetMemoriesController


class TestGetMemoriesController:
    """Test GetMemoriesController - a simple delegation controller"""
    
    @patch('agentic_platform.service.memory_gateway.api.get_memory_controller.MemoryClient.get_memories')
    def test_get_memories_delegates_to_memory_client(self, mock_get_memories):
        """Test that controller properly delegates to MemoryClient.get_memories"""
        # Setup mock response
        mock_memory = Memory(
            session_id="test-session",
            user_id="test-user", 
            agent_id="test-agent",
            content="Test memory content",
            embedding_model="test-model"
        )
        mock_response = GetMemoriesResponse(memories=[mock_memory])
        mock_get_memories.return_value = mock_response
        
        # Create request
        request = GetMemoriesRequest(
            user_id="test-user",
            session_id="test-session",
            limit=5
        )
        
        # Call controller
        result = GetMemoriesController.get_memories(request)
        
        # Verify delegation
        mock_get_memories.assert_called_once_with(request)
        assert result is mock_response
        assert isinstance(result, GetMemoriesResponse)
        assert len(result.memories) == 1
        assert result.memories[0].content == "Test memory content"
    
    @patch('agentic_platform.service.memory_gateway.api.get_memory_controller.MemoryClient.get_memories')
    def test_get_memories_passes_through_exceptions(self, mock_get_memories):
        """Test that controller passes through exceptions from MemoryClient"""
        # Setup mock to raise exception
        mock_get_memories.side_effect = ValueError("Database connection failed")
        
        # Create request
        request = GetMemoriesRequest(user_id="test-user")
        
        # Should raise the same exception
        with pytest.raises(ValueError, match="Database connection failed"):
            GetMemoriesController.get_memories(request)
        
        # Verify the call was made
        mock_get_memories.assert_called_once_with(request)
    
    def test_controller_is_static_method(self):
        """Test that get_memories is a static method"""
        # Should be able to call without instantiating
        assert hasattr(GetMemoriesController, 'get_memories')
        assert callable(GetMemoriesController.get_memories)
        
        # Method should not require self parameter
        import inspect
        sig = inspect.signature(GetMemoriesController.get_memories)
        params = list(sig.parameters.keys())
        assert 'self' not in params
        assert 'request' in params
        assert len(params) == 1  # Only request parameter
    
    def test_controller_class_structure(self):
        """Test the controller class structure"""
        # Should be a simple class with only the static method
        methods = [method for method in dir(GetMemoriesController) 
                  if not method.startswith('_')]
        assert methods == ['get_memories']
        
        # Should not be instantiable (no __init__ needed)
        controller = GetMemoriesController()
        assert controller is not None 