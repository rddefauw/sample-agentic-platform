from agentic_platform.workflow.routing.routing_prompts import (
    ClassifyPrompt,
    InstallationPrompt,
    SecurityPrompt,
    QueryPrompt,
    PerformancePrompt
)
from agentic_platform.core.models.prompt_models import BasePrompt
from agentic_platform.core.models.vectordb_models import VectorSearchRequest, VectorSearchResponse
from agentic_platform.core.client.retrieval_gateway.retrieval_gateway_client import RetrievalGatewayClient
from agentic_platform.core.models.llm_models import LLMRequest, LLMResponse
from agentic_platform.core.models.memory_models import Message
from agentic_platform.core.client.llm_gateway.llm_gateway_client import LLMGatewayClient
from typing import Dict, Any, TypedDict, List, Type
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


####################
# Workflow state
####################

# Define the WorkflowState using TypedDict
# Define the WorkflowState using TypedDict
class WorkflowState(TypedDict):
    question: str
    category: str
    response: str

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

def _do_rag(user_input: str, rag_prompt: Type[BasePrompt]) -> str:
    """Calls RAG to get a response with context from vector search"""
    # Retrieve the context from the vector store
    context: str = _call_vector_search(user_input, 2)
    # Create the RAG prompt
    inputs: Dict[str, Any] = {"question": user_input, "context": context}
    rag_prompt: BasePrompt = rag_prompt(inputs=inputs)
    # Call Bedrock with the RAG prompt
    return _call_bedrock(rag_prompt)

def classify_question(state: WorkflowState) -> Dict[str, str]:
    """Classifies the question into a category"""
    inputs = {"question": state['question']}
    prompt = ClassifyPrompt(inputs=inputs)
    
    category = _call_bedrock(prompt).strip()
    state['category'] = category
    return {"category": category}

def handle_installation(state: WorkflowState) -> WorkflowState:
    """Handles installation & setup questions"""    
    state['response'] = _do_rag(state['question'], InstallationPrompt)
    return state

def handle_security(state: WorkflowState) -> WorkflowState:
    """Handles security & authentication questions"""
    state['response'] = _do_rag(state['question'], SecurityPrompt)
    return state

def handle_querying(state: WorkflowState) -> WorkflowState:
    """Handles querying & indexing questions"""
    state['response'] = _do_rag(state['question'], QueryPrompt)
    return state

def handle_performance(state: WorkflowState) -> WorkflowState:
    """Handles performance optimization questions"""
    state['response'] = _do_rag(state['question'], PerformancePrompt)
    return state
