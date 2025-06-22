import pytest
from unittest.mock import Mock, patch
from agentic_platform.agent.diy_agent.diy_agent_controller import DIYAgentController
from agentic_platform.core.models.api_models import AgenticRequest, AgenticResponse
from agentic_platform.core.models.memory_models import Message, TextContent


class TestDIYAgentController:
    """Test DIY Agent Controller"""
    
    @patch('agentic_platform.agent.diy_agent.diy_agent_controller.agent')
    def test_invoke(self, mock_agent):
        """Test controller invoke method"""
        # Setup mock agent response
        mock_response = AgenticResponse(
            session_id="test-session",
            message=Message.from_text("assistant", "Controller test response"),
            metadata={"test": True}
        )
        mock_agent.invoke.return_value = mock_response
        
        # Create request
        request = AgenticRequest.from_text("Test message", session_id="test-session")
        
        # Call controller
        response = DIYAgentController.invoke(request)
        
        # Verify agent was called correctly
        mock_agent.invoke.assert_called_once_with(request)
        assert response == mock_response
        assert response.session_id == "test-session"
        assert response.text == "Controller test response"
    
    @patch('agentic_platform.agent.diy_agent.diy_agent_controller.agent')
    def test_invoke_passes_through_agent_response(self, mock_agent):
        """Test that controller passes through agent response unchanged"""
        # Setup complex mock response
        message = Message(
            role="assistant",
            content=[
                TextContent(type="text", text="Complex response"),
            ],
            tool_calls=[],
            tool_results=[]
        )
        mock_response = AgenticResponse(
            session_id="complex-session",
            message=message,
            metadata={"model": "test-model", "tokens": 100}
        )
        mock_agent.invoke.return_value = mock_response
        
        # Create request
        request = AgenticRequest.from_text("Complex test", session_id="complex-session")
        
        # Call controller
        response = DIYAgentController.invoke(request)
        
        # Verify exact passthrough
        assert response is mock_response
        assert response.session_id == "complex-session"
        assert response.metadata["model"] == "test-model"
        assert response.metadata["tokens"] == 100 