import pytest
from unittest.mock import Mock, patch, AsyncMock
from agentic_platform.agent.pydanticai_agent.pyai_agent_controller import PyAIAgentController
from agentic_platform.core.models.api_models import AgenticRequest, AgenticResponse
from agentic_platform.core.models.memory_models import Message, TextContent


class TestPyAIAgentController:
    """Test PydanticAI Agent Controller"""
    
    @pytest.mark.asyncio
    @patch('agentic_platform.agent.pydanticai_agent.pyai_agent_controller.agent')
    async def test_invoke(self, mock_agent):
        """Test controller invoke method"""
        # Setup mock agent response
        mock_response = AgenticResponse(
            session_id="test-session",
            message=Message.from_text("assistant", "Controller test response"),
            metadata={"test": True}
        )
        mock_agent.invoke = AsyncMock(return_value=mock_response)
        
        # Create request
        request = AgenticRequest.from_text("Test message", session_id="test-session")
        
        # Call controller
        response = await PyAIAgentController.invoke(request)
        
        # Verify agent was called correctly
        mock_agent.invoke.assert_called_once_with(request)
        assert response == mock_response
        assert response.session_id == "test-session"
        assert response.text == "Controller test response"
    
    @pytest.mark.asyncio
    @patch('agentic_platform.agent.pydanticai_agent.pyai_agent_controller.agent')
    async def test_invoke_passes_through_agent_response(self, mock_agent):
        """Test that controller passes through agent response unchanged"""
        # Setup complex mock response
        message = Message(
            role="assistant",
            content=[
                TextContent(type="text", text="Complex async response"),
            ],
            tool_calls=[],
            tool_results=[]
        )
        mock_response = AgenticResponse(
            session_id="async-session",
            message=message,
            metadata={"model": "claude-3-sonnet", "async": True}
        )
        mock_agent.invoke = AsyncMock(return_value=mock_response)
        
        # Create request
        request = AgenticRequest.from_text("Async test", session_id="async-session")
        
        # Call controller
        response = await PyAIAgentController.invoke(request)
        
        # Verify exact passthrough
        assert response is mock_response
        assert response.session_id == "async-session"
        assert response.metadata["model"] == "claude-3-sonnet"
        assert response.metadata["async"] is True 