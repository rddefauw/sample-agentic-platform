from typing import Dict
from langgraph.graph import StateGraph, START, END

from agentic_platform.workflow.parallelization.parallelization_nodes import (
    parallel_start,
    generate_beginner_solution,
    generate_expert_solution,
    generate_cost_solution,
    format_output,
    WorkflowState
)

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class ParallelizationSearchWorkflow:
    """
    Implements the parallelization workflow pattern from module 3.
    """
    
    def __init__(self, max_iterations: int = 3):
        """
        Initialize the SearchOptimizerWorkflow with a compiled workflow graph.
        """
        self.max_iterations = max_iterations
        self.workflow = self._build_workflow()

    def init_state(self, query: str) -> WorkflowState:
        """Initialize the workflow state with a question."""
        return WorkflowState(
            question=query,
            beginner_solution="",
            expert_solution="",
            cost_solution="",
            final_output=""
        )
    
    def _build_workflow(self):
        """Creates a workflow for generating parallel solutions"""
        workflow = StateGraph(WorkflowState)
        
        # Add nodes to our graph
        workflow.add_node("parallelizer", parallel_start)
        workflow.add_node("beginner", generate_beginner_solution)
        workflow.add_node("expert", generate_expert_solution)
        workflow.add_node("cost", generate_cost_solution)
        workflow.add_node("format", format_output)
        
        # Create the parallel workflow
        # From START, branch to all three solution generators
        workflow.add_edge(START, "parallelizer")

        # Each parallel node leads to the parallelizer
        workflow.add_edge("parallelizer", "beginner")
        workflow.add_edge("parallelizer", "expert")
        workflow.add_edge("parallelizer", "cost")
        
        # Each solution node leads to format when all are complete.
        workflow.add_edge(["beginner", "expert", "cost"], "format")
        
        # Format leads to END
        workflow.add_edge("format", END)
        
        # Compile and return the workflow
        return workflow.compile()

    
    def run(self, query: str) -> str:
        """
        Run the search workflow with a given query.
        """
        # Initialize state
        initial_state: WorkflowState = self.init_state(query=query)

        # Run the workflow
        final_state: WorkflowState = self.workflow.invoke(initial_state)

        return final_state["final_output"]