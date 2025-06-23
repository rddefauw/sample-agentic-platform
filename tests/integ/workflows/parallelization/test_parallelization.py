"""
Integration tests for Parallelization workflow.

This module contains integration tests for the parallelization workflow,
testing the actual workflow controller functionality with mocked external dependencies.
"""

import pytest
import sys
import os
from typing import Dict, Any
import uuid
from unittest.mock import patch, MagicMock

# Add the source directory to the path so we can import the workflow modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..', 'src'))

from agentic_platform.core.models.llm_models import LLMResponse, Usage


class TestParallelizationWorkflow:
    """Integration tests for Parallelization workflow with mocked external dependencies"""
    
    def test_parallelization_happy_path_with_mocks(self):
        """Test parallelization workflow happy path with mocked LLM calls"""
        
        # Mock LLM responses for the 3 parallel solutions
        mock_llm_responses = [
            # Beginner solution
            LLMResponse(
                id="beginner-solution-1",
                text="**Beginner-Friendly Approach to Renewable Energy:**\n\nStart with solar panels on your home:\n1. Research local solar installers\n2. Get quotes from 3-5 companies\n3. Check for government incentives and rebates\n4. Consider financing options like solar loans\n5. Install panels on south-facing roof areas\n6. Monitor your energy production with apps\n\nThis approach is simple, well-supported, and provides immediate cost savings on electricity bills.",
                usage=Usage(prompt_tokens=60, completion_tokens=80, total_tokens=140)
            ),
            # Expert solution
            LLMResponse(
                id="expert-solution-1",
                text="**Expert-Level Renewable Energy Strategy:**\n\nImplement a comprehensive microgrid system:\n1. Conduct detailed energy audit and load analysis\n2. Design hybrid system: solar PV + wind + battery storage\n3. Install smart inverters with grid-tie capabilities\n4. Implement demand response automation\n5. Use predictive analytics for energy optimization\n6. Integrate with utility programs (net metering, time-of-use)\n7. Consider peer-to-peer energy trading platforms\n\nThis maximizes efficiency, resilience, and revenue generation opportunities.",
                usage=Usage(prompt_tokens=80, completion_tokens=100, total_tokens=180)
            ),
            # Cost solution
            LLMResponse(
                id="cost-solution-1",
                text="**Cost-Optimized Renewable Energy Solution:**\n\nFocus on highest ROI options:\n1. Start with energy efficiency improvements (LED lights, insulation)\n2. Install DIY solar kits for non-critical loads\n3. Join community solar programs (no upfront costs)\n4. Use refurbished or end-of-lease solar panels\n5. Take advantage of all available tax credits and rebates\n6. Consider solar water heating (faster payback than PV)\n7. Implement time-of-use electricity management\n\nThis approach minimizes upfront investment while maximizing long-term savings.",
                usage=Usage(prompt_tokens=70, completion_tokens=90, total_tokens=160)
            )
        ]
        
        try:
            from agentic_platform.workflow.parallelization.parallelization_controller import ParallelizationSearchWorkflowController
            from agentic_platform.core.models.api_models import AgenticRequest, AgenticResponse
            from agentic_platform.core.models.memory_models import Message
            
            # Create a sample request
            test_message = Message.from_text("user", "Analyze multiple aspects of renewable energy")
            request = AgenticRequest(
                message=test_message,
                session_id=str(uuid.uuid4()),
                stream=False
            )
            
            # Mock the external dependencies
            with patch('agentic_platform.core.client.llm_gateway.llm_gateway_client.LLMGatewayClient.chat_invoke') as mock_llm:
                
                # Set up the mock responses
                mock_llm.side_effect = mock_llm_responses
                
                # Call the controller
                response = ParallelizationSearchWorkflowController.search(request)
                
                # Verify response structure
                assert isinstance(response, AgenticResponse), "Response should be AgenticResponse"
                assert response.message is not None, "Response should have a message"
                assert response.message.role == "assistant", "Response message should be from assistant"
                assert response.session_id == request.session_id, "Session ID should match"
                
                # Check that we got some text response
                response_text = response.text
                assert response_text is not None, "Response should have text content"
                assert len(response_text.strip()) > 0, "Response text should not be empty"
                
                # Verify the response contains expected content from our mocked solutions
                assert "Solution Approaches" in response_text, "Response should contain solution approaches"
                assert "Beginner" in response_text, "Response should contain beginner solution"
                assert "Expert" in response_text, "Response should contain expert solution"
                assert "Cost" in response_text, "Response should contain cost solution"
                
                # Verify that external dependencies were called the expected number of times
                assert mock_llm.call_count == 3, f"Expected 3 LLM calls (3 parallel solutions), got {mock_llm.call_count}"
                
                print(f"✅ Parallelization integration test passed!")
                print(f"   LLM calls: {mock_llm.call_count}")
                print(f"   Response length: {len(response_text)} characters")
                
        except ImportError as e:
            pytest.skip(f"Parallelization controller not available: {e}")
        except Exception as e:
            pytest.fail(f"Error testing parallelization controller: {e}")
