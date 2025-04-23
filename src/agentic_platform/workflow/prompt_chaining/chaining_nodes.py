from agentic_platform.workflow.prompt_chaining.chaining_prompts import (
    ExtractConceptPrompt, 
    SimplifyExplanationPrompt, 
    GenerateExamplesPrompt, 
    FormatOutputPrompt
)
from agentic_platform.core.models.prompt_models import BasePrompt
from agentic_platform.core.models.vectordb_models import VectorSearchRequest, VectorSearchResponse
from agentic_platform.core.client.retrieval_gateway.retrieval_gateway_client import RetrievalGatewayClient
from agentic_platform.core.models.llm_models import LLMRequest, LLMResponse
from agentic_platform.core.models.memory_models import Message
from agentic_platform.core.client.llm_gateway.llm_gateway_client import LLMGatewayClient
from typing import Dict, Any, TypedDict
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


####################
# Workflow state
####################

# Define the WorkflowState using TypedDict
class WorkflowState(TypedDict):
    # Input
    query: str = ""
    # Extracted concepts
    concepts: str = ""
    # Simplified explanation
    explanation: str = ""
    # Generated examples
    examples: str = ""
    # Final formatted output
    final_output: str = ""
    # Track completion status
    complete: bool = False

####################
# Helper functions
####################

def _call_bedrock(prompt: BasePrompt) -> str:
    """Calls Bedrock to get a response"""
    request: LLMRequest = LLMRequest(
        system_prompt=prompt.system_prompt,
        messages=[Message(role='user', text=prompt.user_prompt)],
        model_id=prompt.model_id,
        hyperparams=prompt.hyperparams
    )

    response: LLMResponse = LLMGatewayClient.chat_invoke(request=request)
    return response.text

def _call_vector_search(query:str, limit:int) -> VectorSearchResponse:
    """Calls VectorDB to get a response"""
    vs_request: VectorSearchRequest = VectorSearchRequest(
        query=query,
        limit=limit
    )
    response: VectorSearchResponse = RetrievalGatewayClient.retrieve(vs_request)
    return '\n'.join([result.text for result in response.results])


def extract_concepts(state: WorkflowState) -> WorkflowState:
    """Extracts key concepts from documentation"""
    logger.info("Starting concept extraction...")

    query: str = state['query']
    context: str = _call_vector_search(query, 1)

    # Create the prompt
    inputs: Dict[str, Any] = {"question": query, "context": context}
    prompt: BasePrompt = ExtractConceptPrompt(inputs=inputs)

    # Call Bedrock
    concepts: str = _call_bedrock(prompt)
    state['concepts'] = concepts
    logger.info(f"Concepts extracted")
    return state

def simplify_explanation(state: WorkflowState) -> WorkflowState:
    """Explains concepts in simpler terms"""
    logger.info("Starting simplification of explanation...")
    inputs: Dict[str, Any] = {"concepts": state['concepts']}
    prompt: BasePrompt = SimplifyExplanationPrompt(inputs=inputs)

    explanation: str = _call_bedrock(prompt)
    state['explanation'] = explanation
    logger.info(f"Simplified explanation")
    return state

def generate_examples(state: WorkflowState) -> WorkflowState:
    """Provides practical implementation examples"""
    logger.info("Generating examples...")
    inputs: Dict[str, Any] = {"concepts": state['concepts'], "explanation": state['explanation']}
    prompt: BasePrompt = GenerateExamplesPrompt(inputs=inputs)

    examples: str = _call_bedrock(prompt)
    state['examples'] = examples
    logger.info(f"Examples generated")
    return state

def format_output(state: WorkflowState) -> WorkflowState:
    """Formats the final documentation breakdown"""
    logger.info("Formatting final output...")
    inputs: Dict[str, Any] = {
        "concepts": state['concepts'], 
        "explanation": state['explanation'], 
        "examples": state['examples']
    }
    prompt: BasePrompt = FormatOutputPrompt(inputs=inputs)

    final_output: str = _call_bedrock(prompt)
    state['final_output'] = final_output
    logger.info("Final output formatted.")
    return state