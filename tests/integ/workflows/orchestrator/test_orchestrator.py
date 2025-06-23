"""
Integration tests for Orchestrator workflow.

This module contains integration tests for the orchestrator workflow,
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


class TestOrchestratorWorkflow:
    """Integration tests for Orchestrator workflow with mocked external dependencies"""
    
    def test_orchestrator_happy_path_with_mocks(self):
        """Test orchestrator workflow happy path with mocked LLM and retrieval calls"""
        
        # Mock LLM responses for different stages of the workflow
        mock_llm_responses = [
            # Planning stage response
            LLMResponse(
                id="plan-response-1",
                text="Check OpenSearch cluster health\nVerify index configuration\nAnalyze query performance",
                usage=Usage(prompt_tokens=50, completion_tokens=30, total_tokens=80)
            ),
            # Investigation responses (one for each diagnostic step)
            LLMResponse(
                id="investigate-response-1", 
                text="Based on the retrieved context, the OpenSearch cluster health issue appears to be related to node connectivity. The cluster status shows yellow due to unassigned shards.",
                usage=Usage(prompt_tokens=100, completion_tokens=50, total_tokens=150)
            ),
            LLMResponse(
                id="investigate-response-2",
                text="The index configuration analysis reveals that the mapping settings are correct, but the refresh interval might be too frequent causing performance issues.",
                usage=Usage(prompt_tokens=90, completion_tokens=45, total_tokens=135)
            ),
            LLMResponse(
                id="investigate-response-3",
                text="Query performance analysis shows that complex aggregations are causing timeouts. Consider optimizing the query structure or increasing timeout values.",
                usage=Usage(prompt_tokens=110, completion_tokens=55, total_tokens=165)
            ),
            # Synthesis stage response
            LLMResponse(
                id="synthesis-response-1",
                text="## Diagnostic Summary\n\nBased on the investigation of your OpenSearch issues:\n\n1. **Cluster Health**: Yellow status due to unassigned shards - recommend checking node connectivity\n2. **Index Configuration**: Mapping is correct but refresh interval optimization needed\n3. **Query Performance**: Complex aggregations causing timeouts - optimize queries or increase timeouts\n\n**Recommended Actions**: Fix node connectivity, adjust refresh intervals, and optimize query structure.",
                usage=Usage(prompt_tokens=200, completion_tokens=100, total_tokens=300)
            )
        ]
        
        # Mock retrieval responses
        mock_retrieval_responses = [
            VectorSearchResponse(
                results=[
                    VectorSearchResult(
                        text="OpenSearch cluster health can be checked using the _cluster/health API. Yellow status indicates unassigned shards.",
                        score=0.95,
                        metadata={"source": "opensearch-docs"}
                    ),
                    VectorSearchResult(
                        text="Node connectivity issues often cause shard allocation problems in OpenSearch clusters.",
                        score=0.88,
                        metadata={"source": "troubleshooting-guide"}
                    )
                ]
            ),
            VectorSearchResponse(
                results=[
                    VectorSearchResult(
                        text="Index mapping configuration should be optimized for your data structure. Refresh intervals affect indexing performance.",
                        score=0.92,
                        metadata={"source": "performance-guide"}
                    ),
                    VectorSearchResult(
                        text="Frequent refresh operations can impact cluster performance significantly.",
                        score=0.85,
                        metadata={"source": "best-practices"}
                    )
                ]
            ),
            VectorSearchResponse(
                results=[
                    VectorSearchResult(
                        text="Complex aggregation queries in OpenSearch can cause timeouts. Consider using composite aggregations for better performance.",
                        score=0.90,
                        metadata={"source": "query-optimization"}
                    ),
                    VectorSearchResult(
                        text="Query timeout settings can be adjusted at the cluster level or per-request basis.",
                        score=0.87,
                        metadata={"source": "configuration-guide"}
                    )
                ]
            )
        ]
        
        try:
            from agentic_platform.workflow.orchestrator.orchestrator_controller import OrchestratorSearchWorkflowController
            from agentic_platform.core.models.api_models import AgenticRequest, AgenticResponse
            from agentic_platform.core.models.memory_models import Message
            
            # Create a sample request
            test_message = Message.from_text("user", "I'm having issues with my OpenSearch cluster performance")
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
                response = OrchestratorSearchWorkflowController.search(request)
                
                # Verify response structure
                assert isinstance(response, AgenticResponse), "Response should be AgenticResponse"
                assert response.message is not None, "Response should have a message"
                assert response.message.role == "assistant", "Response message should be from assistant"
                assert response.session_id == request.session_id, "Session ID should match"
                
                # Check that we got some text response
                response_text = response.text
                assert response_text is not None, "Response should have text content"
                assert len(response_text.strip()) > 0, "Response text should not be empty"
                
                # Verify the response contains expected content from our mocked synthesis
                assert "Diagnostic Summary" in response_text, "Response should contain diagnostic summary"
                assert "Cluster Health" in response_text, "Response should mention cluster health"
                assert "Query Performance" in response_text, "Response should mention query performance"
                
                # Verify that external dependencies were called
                assert mock_llm.call_count == 5, f"Expected 5 LLM calls (plan + 3 investigations + synthesis), got {mock_llm.call_count}"
                assert mock_retrieval.call_count == 3, f"Expected 3 retrieval calls (one per investigation), got {mock_retrieval.call_count}"
                
                print(f"✅ Orchestrator integration test passed!")
                print(f"   LLM calls: {mock_llm.call_count}")
                print(f"   Retrieval calls: {mock_retrieval.call_count}")
                print(f"   Response length: {len(response_text)} characters")
                
        except ImportError as e:
            pytest.skip(f"Orchestrator controller not available: {e}")
        except Exception as e:
            pytest.fail(f"Error testing orchestrator controller: {e}")
