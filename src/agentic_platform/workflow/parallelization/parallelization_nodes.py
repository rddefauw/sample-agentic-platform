from agentic_platform.workflow.parallelization.parallelization_prompts import (
    BeginnerPrompt,
    ExpertPrompt,
    CostPrompt
)
from agentic_platform.core.models.prompt_models import BasePrompt
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
class WorkflowState(TypedDict):
    question: str
    beginner_solution: str
    expert_solution: str  
    cost_solution: str
    final_output: str


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

def parallel_start(state: WorkflowState) -> WorkflowState:
    """Starts the parallel workflow"""
    return state

def generate_beginner_solution(state: WorkflowState) -> Dict:
    """Generates a beginner-friendly solution"""
    beginner_prompt: BasePrompt = BeginnerPrompt(inputs={"question": state["question"]})
    solution: str = _call_bedrock(beginner_prompt)
    # Only return the field this function is responsible for
    return {"beginner_solution": solution}

def generate_expert_solution(state: WorkflowState) -> Dict:
    """Generates an expert-level solution"""
    expert_prompt: BasePrompt = ExpertPrompt(inputs={"question": state["question"]})
    solution: str = _call_bedrock(expert_prompt)
    # Only return the field this function is responsible for
    return {"expert_solution": solution}

def generate_cost_solution(state: WorkflowState) -> Dict:
    """Generates a cost-optimized solution"""
    cost_prompt: BasePrompt = CostPrompt(inputs={"question": state["question"]})
    solution: str = _call_bedrock(cost_prompt)
    # Only return the field this function is responsible for
    return {"cost_solution": solution}

def format_output(state: WorkflowState) -> WorkflowState:
    """Formats the parallel solutions into a clear response"""
    state["final_output"] = f"""
    # OpenSearch Solution Approaches
    
    ## 📘 Beginner-Friendly Solution
    {state["beginner_solution"]}
    
    ## 🎯 Expert-Level Solution
    {state["expert_solution"]}
    
    ## 💰 Cost-Optimized Solution
    {state["cost_solution"]}
    """
    return state