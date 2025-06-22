import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import List

from agentic_platform.agent.diy_agent.diy_agent import DIYAgent
from agentic_platform.core.models.api_models import AgenticRequest, AgenticResponse
from agentic_platform.core.models.memory_models import (
    Message, TextContent, SessionContext, ToolResult,
    UpsertSessionContextRequest, GetSessionContextRequest, GetSessionContextResponse
)
from agentic_platform.core.models.llm_models import LLMResponse, ToolCall
from agentic_platform.core.models.tool_models import ToolSpec
from pydantic import BaseModel


class MockToolInput(BaseModel):
    query: str


def mock_tool_function(input_data: MockToolInput) -> ToolResult:
    """Mock tool function for testing"""
    return ToolResult(
        content=[TextContent(type="text", text=f"Mock result for: {input_data.query}")],
        isError=False
    )


@pytest.fixture
def mock_tool_spec():
    """Create a mock tool spec"""
    return ToolSpec(
        name="mock_tool",
        description="A mock tool for testing",
        model=MockToolInput,
        function=mock_tool_function
    )


@pytest.fixture
def diy_agent_with_tools(mock_tool_spec):
    """Create DIY agent with mock tools"""
    with patch('agentic_platform.agent.diy_agent.diy_agent.tool_spec') as mock_tool_spec_decorator:
        mock_tool_spec_decorator.return_value = mock_tool_spec
        agent = DIYAgent(tools=[mock_tool_function])
        return agent


@pytest.fixture
def mock_memory_client():
    """Mock the memory gateway client"""
    with patch('agentic_platform.agent.diy_agent.diy_agent.memory_client') as mock_client:
        yield mock_client


@pytest.fixture
def mock_llm_gateway_client():
    """Mock the LLM gateway client"""
    with patch('agentic_platform.agent.diy_agent.diy_agent.LLMGatewayClient') as mock_client:
        yield mock_client


class TestDIYAgent:
    """Test DIY Agent functionality with new agent types"""
    
    def test_agent_initialization(self, mock_tool_spec):
        """Test that DIY agent initializes correctly with tools"""
        with patch('agentic_platform.agent.diy_agent.diy_agent.tool_spec') as mock_decorator:
            mock_decorator.return_value = mock_tool_spec
            agent = DIYAgent(tools=[mock_tool_function])
            
            assert len(agent.tools) == 1
            assert agent.tools[0].name == "mock_tool"
            assert isinstance(agent.conversation, SessionContext)
    
    def test_invoke_with_new_session(self, diy_agent_with_tools, mock_memory_client, mock_llm_gateway_client):
        """Test invoking agent with a new session"""
        # Setup mocks
        mock_memory_client.get_session_context.return_value = GetSessionContextResponse(results=[])
        mock_llm_gateway_client.chat_invoke.return_value = LLMResponse(
            text="Hello! How can I help you?",
            stop_reason="stop",
            tool_calls=[]
        )
        
        # Create request
        request = AgenticRequest.from_text("Hello", session_id="new-session-123")
        
        # Invoke agent
        response = diy_agent_with_tools.invoke(request)
        
        # Verify response structure
        assert isinstance(response, AgenticResponse)
        assert response.session_id == "new-session-123"
        assert isinstance(response.message, Message)
        assert response.message.role == "assistant"
        assert response.text == "Hello! How can I help you?"
        assert "model" in response.metadata
    
    def test_invoke_with_existing_session(self, diy_agent_with_tools, mock_memory_client, mock_llm_gateway_client):
        """Test invoking agent with an existing session"""
        # Setup existing session
        existing_session = SessionContext(
            session_id="existing-session-456",
            messages=[Message.from_text("user", "Previous message")]
        )
        mock_memory_client.get_session_context.return_value = GetSessionContextResponse(
            results=[existing_session]
        )
        mock_llm_gateway_client.chat_invoke.return_value = LLMResponse(
            text="I remember our previous conversation.",
            stop_reason="stop",
            tool_calls=[]
        )
        
        # Create request
        request = AgenticRequest.from_text("Continue our chat", session_id="existing-session-456")
        
        # Invoke agent
        response = diy_agent_with_tools.invoke(request)
        
        # Verify session was loaded
        mock_memory_client.get_session_context.assert_called_once()
        assert response.session_id == "existing-session-456"
        assert response.text == "I remember our previous conversation."
    
    def test_invoke_with_tool_use(self, diy_agent_with_tools, mock_memory_client, mock_llm_gateway_client):
        """Test agent handling tool calls"""
        # Setup mocks
        mock_memory_client.get_session_context.return_value = GetSessionContextResponse(results=[])
        
        # First response: tool use
        tool_call_response = LLMResponse(
            text="",
            stop_reason="tool_use",
            tool_calls=[ToolCall(name="mock_tool", arguments={"query": "test"}, id="call_123")]
        )
        
        # Second response: final answer
        final_response = LLMResponse(
            text="Based on the tool result: Mock result for: test",
            stop_reason="stop",
            tool_calls=[]
        )
        
        mock_llm_gateway_client.chat_invoke.side_effect = [tool_call_response, final_response]
        
        # Create request
        request = AgenticRequest.from_text("Use a tool to help me", session_id="tool-session")
        
        # Invoke agent
        response = diy_agent_with_tools.invoke(request)
        
        # Verify tool execution
        assert mock_llm_gateway_client.chat_invoke.call_count == 2
        assert response.text == "Based on the tool result: Mock result for: test"
        assert "stop_reason" in response.metadata
        assert response.metadata["stop_reason"] == "stop"
    
    def test_invoke_with_multi_turn_messages(self, diy_agent_with_tools, mock_memory_client, mock_llm_gateway_client):
        """Test agent with multi-turn conversation in request"""
        # Setup mocks
        mock_memory_client.get_session_context.return_value = GetSessionContextResponse(results=[])
        mock_llm_gateway_client.chat_invoke.return_value = LLMResponse(
            text="I understand the context from our conversation.",
            stop_reason="stop",
            tool_calls=[]
        )
        
        # Create request with latest user message
        latest_message = Message.from_text("user", "Actually, what about tomorrow?")
        request = AgenticRequest(message=latest_message, session_id="multi-turn-session")
        
        # Invoke agent
        response = diy_agent_with_tools.invoke(request)
        
        # Verify all messages were added to conversation
        assert response.session_id == "multi-turn-session"
        assert response.text == "I understand the context from our conversation."
    
    def test_invoke_saves_conversation(self, diy_agent_with_tools, mock_memory_client, mock_llm_gateway_client):
        """Test that conversation is saved after agent invocation"""
        # Setup mocks
        mock_memory_client.get_session_context.return_value = GetSessionContextResponse(results=[])
        mock_llm_gateway_client.chat_invoke.return_value = LLMResponse(
            text="Response saved to memory.",
            stop_reason="stop",
            tool_calls=[]
        )
        
        # Create request
        request = AgenticRequest.from_text("Save this conversation", session_id="save-session")
        
        # Invoke agent
        response = diy_agent_with_tools.invoke(request)
        
        # Verify conversation was saved
        mock_memory_client.upsert_session_context.assert_called_once()
        call_args = mock_memory_client.upsert_session_context.call_args[0][0]
        assert isinstance(call_args, UpsertSessionContextRequest)
        assert call_args.session_context.session_id == "save-session"
    
    def test_call_llm_creates_proper_message(self, diy_agent_with_tools, mock_llm_gateway_client):
        """Test that call_llm creates proper Message objects"""
        # Setup mock
        mock_llm_gateway_client.chat_invoke.return_value = LLMResponse(
            text="Test response",
            stop_reason="stop",
            tool_calls=[ToolCall(name="test_tool", arguments={}, id="test_id")]
        )
        
        # Call LLM
        response = diy_agent_with_tools.call_llm()
        
        # Verify message was added with proper content structure
        last_message = diy_agent_with_tools.conversation.messages[-1]
        assert last_message.role == "assistant"
        assert len(last_message.content) == 1
        assert isinstance(last_message.content[0], TextContent)
        assert last_message.content[0].text == "Test response"
        assert len(last_message.tool_calls) == 1
    
    def test_execute_tools(self, diy_agent_with_tools):
        """Test tool execution functionality"""
        # Create mock LLM response with tool calls
        llm_response = LLMResponse(
            text="",
            stop_reason="tool_use",
            tool_calls=[ToolCall(name="mock_tool", arguments={"query": "test query"}, id="tool_123")]
        )
        
        # Execute tools
        tool_results = diy_agent_with_tools.execute_tools(llm_response)
        
        # Verify tool execution
        assert len(tool_results) == 1
        assert tool_results[0].id == "tool_123"
        assert tool_results[0].isError is False
        assert len(tool_results[0].content) == 1
        assert "Mock result for: test query" in tool_results[0].content[0].text
        
        # Verify tool result was added to conversation
        last_message = diy_agent_with_tools.conversation.messages[-1]
        assert last_message.role == "user"
        assert len(last_message.tool_results) == 1
    
    def test_agent_handles_empty_response(self, diy_agent_with_tools, mock_memory_client, mock_llm_gateway_client):
        """Test agent handles case where LLM returns empty response"""
        # Setup mocks
        mock_memory_client.get_session_context.return_value = GetSessionContextResponse(results=[])
        mock_llm_gateway_client.chat_invoke.return_value = LLMResponse(
            text="",
            stop_reason="stop",
            tool_calls=[]
        )
        
        # Create request
        request = AgenticRequest.from_text("Empty response test")
        
        # Invoke agent
        response = diy_agent_with_tools.invoke(request)
        
        # Verify response handles empty text gracefully
        assert isinstance(response, AgenticResponse)
        assert response.message.role == "assistant"
        # Should have empty content array for empty text
        assert response.message.content == []
    
    def test_agent_handles_no_assistant_messages(self, diy_agent_with_tools, mock_memory_client, mock_llm_gateway_client):
        """Test agent fallback when no assistant messages are found"""
        # Setup mocks - simulate scenario where agent gets empty response
        mock_memory_client.get_session_context.return_value = GetSessionContextResponse(results=[])
        mock_llm_gateway_client.chat_invoke.return_value = LLMResponse(
            text="",
            stop_reason="error",
            tool_calls=[]
        )
        
        # Create request
        request = AgenticRequest.from_text("No assistant message test")
        
        # Invoke agent
        response = diy_agent_with_tools.invoke(request)
        
        # Verify response handles empty content - agent will create an assistant message with empty content
        assert response.message.role == "assistant"
        assert response.message.content == []  # Empty content list for empty text
        assert response.metadata["stop_reason"] == "error"
