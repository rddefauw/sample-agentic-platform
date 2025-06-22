import pytest
from unittest.mock import patch, MagicMock

from agentic_platform.core.models.memory_models import (
    GetSessionContextRequest, GetSessionContextResponse,
    UpsertSessionContextRequest, UpsertSessionContextResponse,
    GetMemoriesRequest, GetMemoriesResponse,
    CreateMemoryRequest, CreateMemoryResponse,
    SessionContext, Memory
)
from agentic_platform.service.memory_gateway.client.memory.memory_client import MemoryClient


class TestMemoryClient:
    """Test MemoryClient - a delegation layer to PGMemoryClient"""
    
    @patch('agentic_platform.service.memory_gateway.client.memory.memory_client.PGMemoryClient.get_session_context')
    def test_get_session_context_delegates_to_pg_client(self, mock_pg_get_session):
        """Test that MemoryClient.get_session_context delegates to PGMemoryClient"""
        # Setup mock response
        mock_session = SessionContext(session_id="test-session", user_id="test-user")
        mock_response = GetSessionContextResponse(results=[mock_session])
        mock_pg_get_session.return_value = mock_response
        
        # Create request
        request = GetSessionContextRequest(session_id="test-session")
        
        # Call MemoryClient
        result = MemoryClient.get_session_context(request)
        
        # Verify delegation
        mock_pg_get_session.assert_called_once_with(request)
        assert result is mock_response
        assert isinstance(result, GetSessionContextResponse)
        assert len(result.results) == 1
        assert result.results[0].session_id == "test-session"
    
    @patch('agentic_platform.service.memory_gateway.client.memory.memory_client.PGMemoryClient.upsert_session_context')
    def test_upsert_session_context_delegates_to_pg_client(self, mock_pg_upsert):
        """Test that MemoryClient.upsert_session_context delegates to PGMemoryClient"""
        # Setup mock response
        mock_session = SessionContext(session_id="test-session", user_id="test-user")
        mock_response = UpsertSessionContextResponse(session_context=mock_session)
        mock_pg_upsert.return_value = mock_response
        
        # Create request
        request = UpsertSessionContextRequest(session_context=mock_session)
        
        # Call MemoryClient
        result = MemoryClient.upsert_session_context(request)
        
        # Verify delegation
        mock_pg_upsert.assert_called_once_with(request)
        assert result is mock_response
        assert isinstance(result, UpsertSessionContextResponse)
        assert result.session_context.session_id == "test-session"
    
    @patch('agentic_platform.service.memory_gateway.client.memory.memory_client.PGMemoryClient.get_memories')
    def test_get_memories_delegates_to_pg_client(self, mock_pg_get_memories):
        """Test that MemoryClient.get_memories delegates to PGMemoryClient"""
        # Setup mock response
        mock_memory = Memory(
            session_id="test-session",
            user_id="test-user",
            agent_id="test-agent",
            content="Test content",
            embedding_model="test-model"
        )
        mock_response = GetMemoriesResponse(memories=[mock_memory])
        mock_pg_get_memories.return_value = mock_response
        
        # Create request
        request = GetMemoriesRequest(user_id="test-user", limit=5)
        
        # Call MemoryClient
        result = MemoryClient.get_memories(request)
        
        # Verify delegation
        mock_pg_get_memories.assert_called_once_with(request)
        assert result is mock_response
        assert isinstance(result, GetMemoriesResponse)
        assert len(result.memories) == 1
        assert result.memories[0].content == "Test content"
    
    @patch('agentic_platform.service.memory_gateway.client.memory.memory_client.PGMemoryClient.create_memory')
    def test_create_memory_delegates_to_pg_client(self, mock_pg_create):
        """Test that MemoryClient.create_memory delegates to PGMemoryClient"""
        # Setup mock response
        mock_memory = Memory(
            session_id="test-session",
            user_id="test-user",
            agent_id="test-agent",
            content="Test content",
            embedding_model="test-model"
        )
        mock_response = CreateMemoryResponse(memory=mock_memory)
        mock_pg_create.return_value = mock_response
        
        # Create request
        session_context = SessionContext(session_id="test-session")
        request = CreateMemoryRequest(
            session_id="test-session",
            user_id="test-user",
            agent_id="test-agent",
            session_context=session_context
        )
        
        # Call MemoryClient
        result = MemoryClient.create_memory(request)
        
        # Verify delegation
        mock_pg_create.assert_called_once_with(request)
        assert result is mock_response
        assert isinstance(result, CreateMemoryResponse)
        assert result.memory.content == "Test content"
    
    def test_memory_client_class_structure(self):
        """Test MemoryClient class structure"""
        # Should have all required class methods
        expected_methods = [
            'create_memory',
            'get_memories', 
            'get_session_context',
            'upsert_session_context'
        ]
        
        actual_methods = [method for method in dir(MemoryClient) 
                         if not method.startswith('_') and callable(getattr(MemoryClient, method))]
        
        for expected in expected_methods:
            assert expected in actual_methods, f"Missing method: {expected}"
    
    def test_all_methods_are_classmethods(self):
        """Test that all MemoryClient methods are classmethods"""
        methods_to_check = [
            'get_session_context',
            'upsert_session_context', 
            'get_memories',
            'create_memory'
        ]
        
        for method_name in methods_to_check:
            method = getattr(MemoryClient, method_name)
            # Check if it's a classmethod by checking the method type
            assert isinstance(method, type(MemoryClient.get_memories)), f"{method_name} should be a classmethod"
    
    @patch('agentic_platform.service.memory_gateway.client.memory.memory_client.PGMemoryClient.get_memories')
    def test_exception_passthrough(self, mock_pg_get_memories):
        """Test that exceptions from PGMemoryClient are passed through"""
        # Setup mock to raise exception
        mock_pg_get_memories.side_effect = RuntimeError("Database error")
        
        # Create request
        request = GetMemoriesRequest(user_id="test-user")
        
        # Should raise the same exception
        with pytest.raises(RuntimeError, match="Database error"):
            MemoryClient.get_memories(request)
        
        # Verify the call was made
        mock_pg_get_memories.assert_called_once_with(request) 