"""
Integration tests for Prompt Chaining workflow.

This module contains integration tests for the prompt chaining workflow,
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


class TestPromptChainingWorkflow:
    """Integration tests for Prompt Chaining workflow with mocked external dependencies"""
    
    def test_prompt_chaining_happy_path_with_mocks(self):
        """Test prompt chaining workflow happy path with mocked LLM and retrieval calls"""
        
        # Mock LLM responses for the 4 sequential steps
        mock_llm_responses = [
            # Step 1: Extract concepts
            LLMResponse(
                id="extract-concepts-1",
                text="Key concepts for quantum computing:\n1. Quantum bits (qubits)\n2. Superposition principle\n3. Quantum entanglement\n4. Quantum gates and circuits\n5. Quantum algorithms (Shor's, Grover's)\n6. Quantum decoherence",
                usage=Usage(prompt_tokens=80, completion_tokens=60, total_tokens=140)
            ),
            # Step 2: Simplify explanation
            LLMResponse(
                id="simplify-explanation-1",
                text="Quantum computing simplified:\n\n**Qubits**: Unlike regular computer bits that are either 0 or 1, qubits can be both at the same time (superposition).\n\n**Entanglement**: Qubits can be mysteriously connected - changing one instantly affects the other.\n\n**Quantum Gates**: These are like logic gates in regular computers but work with quantum properties.\n\n**Algorithms**: Special recipes that take advantage of quantum weirdness to solve problems faster.",
                usage=Usage(prompt_tokens=120, completion_tokens=80, total_tokens=200)
            ),
            # Step 3: Generate examples
            LLMResponse(
                id="generate-examples-1",
                text="Practical examples:\n\n1. **Cryptography**: Shor's algorithm could break current encryption by factoring large numbers exponentially faster.\n\n2. **Drug Discovery**: Simulate molecular interactions to find new medicines.\n\n3. **Financial Modeling**: Optimize portfolios and risk analysis.\n\n4. **Weather Prediction**: Process vast amounts of atmospheric data simultaneously.\n\n5. **Machine Learning**: Train AI models much faster than classical computers.",
                usage=Usage(prompt_tokens=150, completion_tokens=100, total_tokens=250)
            ),
            # Step 4: Format output
            LLMResponse(
                id="format-output-1",
                text="# Quantum Computing Explained\n\n## Core Concepts\nQuantum computing leverages quantum mechanical phenomena like superposition and entanglement to process information in fundamentally new ways.\n\n### Key Components:\n- **Qubits**: Quantum bits that can exist in multiple states simultaneously\n- **Entanglement**: Quantum connections between particles\n- **Quantum Gates**: Operations that manipulate qubit states\n- **Quantum Algorithms**: Specialized procedures for quantum advantage\n\n## Simplified Understanding\nThink of classical bits as coins that are either heads or tails. Qubits are like spinning coins that are both heads AND tails until you look at them.\n\n## Real-World Applications\n1. **Cryptography & Security**: Breaking and creating unbreakable codes\n2. **Drug Discovery**: Modeling complex molecular interactions\n3. **Financial Analysis**: Advanced risk modeling and optimization\n4. **Climate Modeling**: Processing massive environmental datasets\n5. **AI Enhancement**: Accelerating machine learning algorithms\n\n## Conclusion\nQuantum computing represents a paradigm shift that could revolutionize how we solve complex computational problems across multiple industries.",
                usage=Usage(prompt_tokens=200, completion_tokens=150, total_tokens=350)
            )
        ]
        
        # Mock retrieval response for the initial concept extraction
        mock_retrieval_response = VectorSearchResponse(
            results=[
                VectorSearchResult(
                    text="Quantum computing is a type of computation that harnesses quantum mechanical phenomena such as superposition and entanglement to process information. Unlike classical computers that use bits, quantum computers use quantum bits or qubits.",
                    score=0.95,
                    metadata={"source": "quantum-computing-basics"}
                )
            ]
        )
        
        try:
            from agentic_platform.workflow.prompt_chaining.chaining_controller import PromptChainingSearchWorkflowController
            from agentic_platform.core.models.api_models import AgenticRequest, AgenticResponse
            from agentic_platform.core.models.memory_models import Message
            
            # Create a sample request
            test_message = Message.from_text("user", "Explain quantum computing step by step")
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
                response = PromptChainingSearchWorkflowController.search(request)
                
                # Verify response structure
                assert isinstance(response, AgenticResponse), "Response should be AgenticResponse"
                assert response.message is not None, "Response should have a message"
                assert response.message.role == "assistant", "Response message should be from assistant"
                assert response.session_id == request.session_id, "Session ID should match"
                
                # Check that we got some text response
                response_text = response.text
                assert response_text is not None, "Response should have text content"
                assert len(response_text.strip()) > 0, "Response text should not be empty"
                
                # Verify the response contains expected content from our mocked final output
                assert "Quantum Computing Explained" in response_text, "Response should contain the formatted title"
                assert "Core Concepts" in response_text, "Response should contain core concepts section"
                assert "Real-World Applications" in response_text, "Response should contain applications section"
                assert "qubits" in response_text.lower(), "Response should mention qubits"
                
                # Verify that external dependencies were called the expected number of times
                assert mock_llm.call_count == 4, f"Expected 4 LLM calls (one per chaining step), got {mock_llm.call_count}"
                assert mock_retrieval.call_count == 1, f"Expected 1 retrieval call (for concept extraction), got {mock_retrieval.call_count}"
                
                print(f"✅ Prompt Chaining integration test passed!")
                print(f"   LLM calls: {mock_llm.call_count}")
                print(f"   Retrieval calls: {mock_retrieval.call_count}")
                print(f"   Response length: {len(response_text)} characters")
                
        except ImportError as e:
            pytest.skip(f"Prompt Chaining controller not available: {e}")
        except Exception as e:
            pytest.fail(f"Error testing prompt chaining controller: {e}")
