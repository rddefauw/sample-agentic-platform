from typing import Dict
from langgraph.graph import StateGraph, START, END

from agentic_platform.workflow.prompt_chaining.chaining_nodes import (
    extract_concepts, 
    simplify_explanation, 
    generate_examples, 
    format_output,
    WorkflowState
)

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
class PromptChainingSearchWorkflow:
    """
    Implements the evaluator-optimizer workflow pattern from module 2.
    """
    
    def __init__(self, max_iterations: int = 3):
        """
        Initialize the SearchOptimizerWorkflow with a compiled workflow graph.
        """
        self.max_iterations = max_iterations
        self.workflow = self._build_workflow()

    def init_state(self, query: str) -> WorkflowState:
        """Initialize the search state with a query."""
        return WorkflowState(
            query=query,
            concepts= "",
            explanation= "",
            examples= "",
            final_output= "",
            complete= False
        )
    
    def _build_workflow(self):
        """Builds the evaluator-optimizer workflow"""
        workflow = StateGraph(WorkflowState)

        # Add nodes to the graph
        workflow.add_node("extract_concepts", extract_concepts)
        workflow.add_node("simplify_explanation", simplify_explanation)
        workflow.add_node("generate_examples", generate_examples)
        workflow.add_node("format_output", format_output)
        
        # Define the workflow edges. These are sequential.
        workflow.add_edge(START, "extract_concepts")
        workflow.add_edge("extract_concepts", "simplify_explanation")
        workflow.add_edge("simplify_explanation", "generate_examples")
        workflow.add_edge("generate_examples", "format_output")
        workflow.add_edge("format_output", END)
        
        # Compile and return the workflow
        return workflow.compile()
    
    def run(self, query: str) -> str:
        """
        Run the search workflow with a given query.
        """
        # Initialize state
        initial_state: WorkflowState = self.init_state(query)

        # Run the workflow
        final_state: WorkflowState = self.workflow.invoke(initial_state)
        
        return final_state["final_output"]