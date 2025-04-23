from agentic_platform.workflow.evaluator_optimizer.evo_prompts import (
    GenerateSolutionPrompt, 
    EvaluateSolutionPrompt, 
    DecisionPrompt, 
    ImproveSolutionPrompt
)
from agentic_platform.core.models.prompt_models import BasePrompt
from agentic_platform.core.models.vectordb_models import VectorSearchRequest, VectorSearchResponse
from agentic_platform.core.client.retrieval_gateway.retrieval_gateway_client import RetrievalGatewayClient
from agentic_platform.core.models.llm_models import LLMRequest, LLMResponse
from agentic_platform.core.models.memory_models import Message
from agentic_platform.core.client.llm_gateway.llm_gateway_client import LLMGatewayClient
from typing import Dict, Any, TypedDict


####################
# Workflow state
####################

class WorkflowState(TypedDict):
    question: str
    answer: str = None
    context: str = None
    feedback: str = None
    iteration: int = 0  
    final_answer: str = None

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


def generate_answer(state: WorkflowState) -> WorkflowState:
    """Generates an initial answer using RAG"""
    
    # Make sure we have a question in the state
    question: str = state.get('question')
    context: str = _call_vector_search(question, 2)


    # Build inputs
    inputs: Dict[str, any] = {
        'question': question,
        'context': context
    }

    rag_prompt: BasePrompt = GenerateSolutionPrompt(inputs=inputs)
    answer: str = _call_bedrock(rag_prompt)

    # Update the state dictionary.
    state["answer"] = answer
    state["context"] = context
    state['iteration'] = state['iteration'] + 1
    
    # Return updated state with the answer and initialize iteration counter
    return state

def evaluate_answer(state: WorkflowState) -> WorkflowState:
    """Evaluates the quality of the answer"""

    inputs: Dict[str, Any] = {
        "question": state["question"],
        "answer": state["answer"],
        "context": state["context"]
    }

    evaluate_prompt: BasePrompt = EvaluateSolutionPrompt(inputs=inputs)
    feedback: str = _call_bedrock(evaluate_prompt)

    state['feedback'] = feedback
    
    # Return updated state with feedback
    return state

def should_improve(state: WorkflowState) -> str:
    """Decides whether to improve or finalize based on evaluation"""
    
    # Limit to maximum 2 improvement iterations
    if state["iteration"] >= 2:
        return "DONE"
        
    # Create a simple prompt to decide if improvement is needed
    inputs: Dict[str, Any] = {
        'feedback': state['feedback']
    }
    decision_prompt: BasePrompt = DecisionPrompt(inputs=inputs)
    decision: str = _call_bedrock(decision_prompt)
    
    # Default to DONE if decision isn't clearly IMPROVE
    return "IMPROVE" if "IMPROVE" in decision else "DONE"

def improve_answer(state: WorkflowState) -> WorkflowState:
    """Improves the answer based on feedback using RAG"""

    # Just do the retrieve portion of RAG.
    context: str = _call_vector_search(state["question"], 2)

    # Build inputs.
    inputs={
        "question": state["question"],
        "answer": state["answer"],
        "feedback": state["feedback"],
        "context": context
    }
    
    # Create the improvement prompt
    improve_prompt = ImproveSolutionPrompt(inputs=inputs)
    improved_answer: str = _call_bedrock(improve_prompt)

    state["answer"] = improved_answer
    state["iteration"] = state["iteration"] + 1

    return state

def finalize_answer(state: WorkflowState) -> WorkflowState:
    """Finalizes the answer"""
    # The final answer is the current answer
    state["final_answer"] = state["answer"]
    return state