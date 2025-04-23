from agentic_platform.workflow.orchestrator.orchestrator_prompts import (
    PlanningPrompt,
    InvestigationPrompt,
    SynthesisPrompt
)
from agentic_platform.core.models.prompt_models import BasePrompt
from agentic_platform.core.models.llm_models import LLMRequest, LLMResponse
from agentic_platform.core.models.memory_models import Message
from agentic_platform.core.client.llm_gateway.llm_gateway_client import LLMGatewayClient
from agentic_platform.core.client.retrieval_gateway.retrieval_gateway_client import RetrievalGatewayClient
from agentic_platform.core.models.vectordb_models import VectorSearchRequest, VectorSearchResponse

from typing import Dict, Any, TypedDict, List, Type
import logging
from typing import TypedDict, List, Annotated, Dict
import operator
from langgraph.constants import Send

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


####################
# Workflow state
####################

# Define the state structure to track our workflow
class TroubleshootingState(TypedDict):
    problem: str
    diagnostic_plan: List[str]
    investigation_results: Annotated[List[Dict[str, str]], operator.add]  # For parallel workers to add results
    final_report: str

# Define worker state
class WorkerState(TypedDict):
    problem: str
    issue: str
    investigation_results: Annotated[List[Dict[str, str]], operator.add]


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
    # Retrieve the context from the vector store
    context: str = _call_vector_search(user_input, 2)
    # Create the RAG prompt
    inputs: Dict[str, Any] = {"question": user_input, "context": context}
    rag_prompt: BasePrompt = rag_prompt(inputs=inputs)
    # Call Bedrock with the RAG prompt

    return _call_bedrock(rag_prompt)

####################
# Orchestrator nodes
####################

def plan_diagnostics(state: TroubleshootingState) -> TroubleshootingState:
    """Orchestrator: Plans the troubleshooting steps needed"""
    
    # Create the planning prompt with proper inputs
    planning_prompt = PlanningPrompt(inputs={"problem": state["problem"]})
    
    # Call bedrock using the planning prompt
    plan = _call_bedrock(planning_prompt)
    
    # Extract each diagnostic step as a potential issue to investigate
    steps = [step.strip() for step in plan.split('\n') if step.strip()]
    
    # Return updated state with diagnostic plan
    return {
        **state,
        "diagnostic_plan": steps,
        "investigation_results": []  # Initialize empty list for results
    }

def investigate_issue(state: WorkerState) -> WorkerState:
    """Worker: Uses RAG to investigate a specific potential issue"""
    
    # Create a more focused query for the RAG system
    search_query = f"OpenSearch {state['problem']} {state['issue']}"
    
    # Use the do_rag helper function with the proper prompt class and inputs
    investigation_result = _do_rag(
        search_query,  # Use this as the search query for RAG
        InvestigationPrompt
    )
    
    # Return a list with a single result dictionary to be added to the main results
    return {
        "investigation_results": [{"issue": state["issue"], "result": investigation_result}]
    }

def synthesize_findings(state: TroubleshootingState) -> TroubleshootingState:
    """Synthesizer: Creates a unified diagnostic response"""
    
    # Format all investigated issues into a structured summary
    issues_summary = ""
    for result in state["investigation_results"]:
        issues_summary += f"\n## Issue: {result['issue']}\n{result['result']}\n"
    
    # Create the synthesis prompt with proper inputs
    synthesis_prompt = SynthesisPrompt(inputs={
        "problem": state["problem"],
        "issues_summary": issues_summary
    })
    
    # Generate the unified response
    final_report = _call_bedrock(synthesis_prompt)
    
    # Return the updated state with the final report
    return {
        **state,
        "final_report": final_report
    }

# Create worker assignments using the Send API
def assign_workers(state: TroubleshootingState):
    """Assign a worker to each diagnostic issue in parallel"""
    
    # Create a Send message for each issue identified by the planner
    return [
        Send("investigate_issue", { "problem": state["problem"], "issue": issue }) 
        for issue in state["diagnostic_plan"]
    ]