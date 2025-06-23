"""
Integration tests for Routing workflow.

This module contains integration tests for the routing workflow,
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


class TestRoutingWorkflow:
    """Integration tests for Routing workflow with mocked external dependencies"""
    
    def test_routing_happy_path_with_mocks(self):
        """Test routing workflow happy path with mocked LLM and retrieval calls"""
        
        # Mock LLM responses for classification + handler
        mock_llm_responses = [
            # Classification response
            LLMResponse(
                id="classify-1",
                text="INSTALL",
                usage=Usage(prompt_tokens=40, completion_tokens=10, total_tokens=50)
            ),
            # Installation handler response
            LLMResponse(
                id="install-handler-1",
                text="**OpenSearch Installation Guide**\n\nTo install OpenSearch, follow these steps:\n\n1. **Download OpenSearch**: Visit the official OpenSearch website and download the appropriate version for your operating system.\n\n2. **System Requirements**: Ensure your system meets the minimum requirements:\n   - Java 11 or higher\n   - At least 4GB RAM\n   - Sufficient disk space\n\n3. **Installation Steps**:\n   - Extract the downloaded archive\n   - Navigate to the OpenSearch directory\n   - Run `./opensearch-tar-install.sh` (Linux/Mac) or `opensearch.bat` (Windows)\n\n4. **Configuration**: Edit `opensearch.yml` to configure:\n   - Cluster name\n   - Node name\n   - Network settings\n   - Security settings\n\n5. **Start OpenSearch**: Use the startup script to launch OpenSearch\n\n6. **Verify Installation**: Check that OpenSearch is running by accessing `http://localhost:9200`\n\nFor production deployments, consider using Docker or package managers for easier management.",
                usage=Usage(prompt_tokens=80, completion_tokens=120, total_tokens=200)
            )
        ]
        
        # Mock retrieval response for the installation handler
        mock_retrieval_response = VectorSearchResponse(
            results=[
                VectorSearchResult(
                    text="OpenSearch installation requires Java 11 or higher and can be installed using tar archives, Docker, or package managers. The default port is 9200.",
                    score=0.92,
                    metadata={"source": "opensearch-installation-guide"}
                ),
                VectorSearchResult(
                    text="After installation, configure opensearch.yml file with cluster settings, network configuration, and security options before starting the service.",
                    score=0.88,
                    metadata={"source": "opensearch-configuration-docs"}
                )
            ]
        )
        
        try:
            from agentic_platform.workflow.routing.routing_controller import RoutingSearchWorkflowController
            from agentic_platform.core.models.api_models import AgenticRequest, AgenticResponse
            from agentic_platform.core.models.memory_models import Message
            
            # Create a sample request for installation
            test_message = Message.from_text("user", "How do I install OpenSearch on my server?")
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
                mock_retrieval.return_value = mock_retrieval_response
                
                # Call the controller
                response = RoutingSearchWorkflowController.search(request)
                
                # Verify response structure
                assert isinstance(response, AgenticResponse), "Response should be AgenticResponse"
                assert response.message is not None, "Response should have a message"
                assert response.message.role == "assistant", "Response message should be from assistant"
                assert response.session_id == request.session_id, "Session ID should match"
                
                # Check that we got some text response
                response_text = response.text
                assert response_text is not None, "Response should have text content"
                assert len(response_text.strip()) > 0, "Response text should not be empty"
                
                # Verify the response contains expected content from our mocked installation handler
                assert "Installation Guide" in response_text, "Response should contain installation guide"
                assert "Download OpenSearch" in response_text, "Response should contain download instructions"
                assert "System Requirements" in response_text, "Response should contain system requirements"
                assert "Java 11" in response_text, "Response should mention Java requirements"
                
                # Verify that external dependencies were called the expected number of times
                assert mock_llm.call_count == 2, f"Expected 2 LLM calls (classify + handler), got {mock_llm.call_count}"
                assert mock_retrieval.call_count == 1, f"Expected 1 retrieval call (for handler), got {mock_retrieval.call_count}"
                
                print(f"✅ Routing integration test passed!")
                print(f"   LLM calls: {mock_llm.call_count}")
                print(f"   Retrieval calls: {mock_retrieval.call_count}")
                print(f"   Routed to: INSTALL category")
                print(f"   Response length: {len(response_text)} characters")
                
        except ImportError as e:
            pytest.skip(f"Routing controller not available: {e}")
        except Exception as e:
            pytest.fail(f"Error testing routing controller: {e}")
