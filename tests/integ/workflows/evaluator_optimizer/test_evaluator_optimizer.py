"""
Integration tests for Evaluator Optimizer workflow.

This module contains integration tests for the evaluator optimizer workflow,
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
from agentic_platform.core.models.vectordb_models import VectorSearchResponse, VectorSearchResult


class TestEvaluatorOptimizerWorkflow:
    """Integration tests for Evaluator Optimizer workflow with mocked external dependencies"""
    
    def test_evaluator_optimizer_happy_path_with_mocks(self):
        """Test evaluator optimizer workflow happy path with mocked LLM and retrieval calls"""
        
        # Mock LLM responses for the iterative workflow
        mock_llm_responses = [
            # Initial answer generation
            LLMResponse(
                id="generate-1",
                text="**Initial Solution for Customer Service Optimization:**\n\n1. **Implement a Ticketing System**: Use a centralized system to track all customer inquiries\n2. **Create Knowledge Base**: Develop comprehensive FAQs and documentation\n3. **Train Support Staff**: Provide regular training on products and communication skills\n4. **Set Response Time Goals**: Establish SLAs for different types of inquiries\n5. **Monitor Performance**: Track metrics like response time and customer satisfaction\n\nThis approach provides a solid foundation for improving customer service efficiency and quality.",
                usage=Usage(prompt_tokens=100, completion_tokens=80, total_tokens=180)
            ),
            # Evaluation of initial answer
            LLMResponse(
                id="evaluate-1",
                text="**Evaluation of Customer Service Solution:**\n\n**Strengths:**\n- Covers basic operational improvements\n- Includes measurable goals and monitoring\n- Addresses both efficiency and quality\n\n**Areas for Improvement:**\n- Missing automation opportunities (chatbots, AI)\n- No mention of customer feedback integration\n- Lacks personalization strategies\n- Could include omnichannel approach\n- No discussion of cost-benefit analysis\n\n**Overall Assessment:** Good foundation but needs enhancement with modern technologies and customer-centric features.",
                usage=Usage(prompt_tokens=120, completion_tokens=90, total_tokens=210)
            ),
            # Decision to improve
            LLMResponse(
                id="decision-1",
                text="IMPROVE - The solution needs enhancement with automation, personalization, and modern customer service technologies.",
                usage=Usage(prompt_tokens=60, completion_tokens=20, total_tokens=80)
            ),
            # Improved answer
            LLMResponse(
                id="improve-1",
                text="**Enhanced Customer Service Optimization Solution:**\n\n**Core Infrastructure:**\n1. **Advanced Ticketing System**: Implement AI-powered routing and prioritization\n2. **Comprehensive Knowledge Base**: Include searchable FAQs, video tutorials, and interactive guides\n3. **Staff Training Program**: Regular training plus AI-assisted coaching\n\n**Modern Enhancements:**\n4. **AI Chatbot Integration**: Handle routine inquiries 24/7 with seamless human handoff\n5. **Omnichannel Support**: Unified experience across email, chat, phone, and social media\n6. **Personalization Engine**: Tailor responses based on customer history and preferences\n7. **Proactive Support**: Identify and address issues before customers report them\n\n**Analytics & Optimization:**\n8. **Real-time Dashboards**: Monitor performance metrics and customer satisfaction\n9. **Feedback Loop Integration**: Continuously improve based on customer input\n10. **Cost-Benefit Analysis**: Regular ROI assessment of support initiatives\n\nThis enhanced approach combines operational excellence with cutting-edge technology for superior customer experience.",
                usage=Usage(prompt_tokens=150, completion_tokens=120, total_tokens=270)
            ),
            # Second evaluation
            LLMResponse(
                id="evaluate-2",
                text="**Final Evaluation:**\n\n**Strengths:**\n- Comprehensive coverage of modern customer service practices\n- Excellent integration of AI and automation\n- Strong focus on personalization and proactive support\n- Includes important analytics and feedback mechanisms\n- Addresses cost considerations\n\n**Assessment:** This is a well-rounded, modern customer service optimization strategy that addresses both operational efficiency and customer experience. The solution is ready for implementation.",
                usage=Usage(prompt_tokens=140, completion_tokens=70, total_tokens=210)
            ),
            # Decision to finalize
            LLMResponse(
                id="decision-2",
                text="DONE - The solution is comprehensive and ready for implementation.",
                usage=Usage(prompt_tokens=50, completion_tokens=15, total_tokens=65)
            )
        ]
        
        # Mock retrieval responses
        mock_retrieval_responses = [
            # For initial generation
            VectorSearchResponse(
                results=[
                    VectorSearchResult(
                        text="Customer service best practices include implementing ticketing systems, creating knowledge bases, training staff, and monitoring performance metrics.",
                        score=0.92,
                        metadata={"source": "customer-service-guide"}
                    ),
                    VectorSearchResult(
                        text="Effective customer service requires clear response time goals, regular staff training, and comprehensive documentation.",
                        score=0.88,
                        metadata={"source": "service-optimization"}
                    )
                ]
            ),
            # For improvement step
            VectorSearchResponse(
                results=[
                    VectorSearchResult(
                        text="Modern customer service leverages AI chatbots, omnichannel support, personalization engines, and proactive support strategies.",
                        score=0.95,
                        metadata={"source": "ai-customer-service"}
                    ),
                    VectorSearchResult(
                        text="Advanced customer service includes real-time analytics, feedback integration, and cost-benefit analysis for continuous improvement.",
                        score=0.90,
                        metadata={"source": "advanced-support-strategies"}
                    )
                ]
            )
        ]
        
        try:
            from agentic_platform.workflow.evaluator_optimizer.evo_controller import EvaluatorOptimizerWorkflowController
            from agentic_platform.core.models.api_models import AgenticRequest, AgenticResponse
            from agentic_platform.core.models.memory_models import Message
            
            # Create a sample request
            test_message = Message.from_text("user", "Evaluate and optimize this approach to solving customer service issues")
            request = AgenticRequest(
                message=test_message,
                session_id=str(uuid.uuid4()),
                stream=False
            )
            
            # Mock the external dependencies
            with patch('agentic_platform.core.client.llm_gateway.llm_gateway_client.LLMGatewayClient.chat_invoke') as mock_llm, \
                 patch('agentic_platform.core.client.retrieval_gateway.retrieval_gateway_client.RetrievalGatewayClient.retrieve') as mock_retrieval:
                
                # Set up the mock responses
                mock_llm.side_effect = mock_llm_responses
                mock_retrieval.side_effect = mock_retrieval_responses
                
                # Call the controller
                response = EvaluatorOptimizerWorkflowController.search(request)
                
                # Verify response structure
                assert isinstance(response, AgenticResponse), "Response should be AgenticResponse"
                assert response.message is not None, "Response should have a message"
                assert response.message.role == "assistant", "Response message should be from assistant"
                assert response.session_id == request.session_id, "Session ID should match"
                
                # Check that we got some text response
                response_text = response.text
                assert response_text is not None, "Response should have text content"
                assert len(response_text.strip()) > 0, "Response text should not be empty"
                
                # Verify the response contains expected content from our mocked improved answer
                assert "Enhanced Customer Service" in response_text, "Response should contain enhanced solution"
                assert "AI Chatbot Integration" in response_text, "Response should mention AI chatbots"
                assert "Omnichannel Support" in response_text, "Response should mention omnichannel"
                assert "Personalization Engine" in response_text, "Response should mention personalization"
                
                # Verify that external dependencies were called the expected number of times
                assert mock_llm.call_count >= 3, f"Expected at least 3 LLM calls (generate + evaluate + decision), got {mock_llm.call_count}"
                assert mock_retrieval.call_count == 2, f"Expected 2 retrieval calls (generate + improve), got {mock_retrieval.call_count}"
                
                print(f"✅ Evaluator Optimizer integration test passed!")
                print(f"   LLM calls: {mock_llm.call_count}")
                print(f"   Retrieval calls: {mock_retrieval.call_count}")
                print(f"   Completed iteration cycle with improvement")
                print(f"   Response length: {len(response_text)} characters")
                
        except ImportError as e:
            pytest.skip(f"Evaluator Optimizer controller not available: {e}")
        except Exception as e:
            pytest.fail(f"Error testing evaluator optimizer controller: {e}")
