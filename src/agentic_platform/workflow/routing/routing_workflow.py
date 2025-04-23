from typing import Dict
from langgraph.graph import StateGraph, START, END

from agentic_platform.workflow.routing.routing_nodes import (
    classify_question,
    handle_installation,
    handle_security,
    handle_querying,
    handle_performance,
    WorkflowState
)

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class RoutingSearchWorkflow:
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
        """Initialize the workflow state with a question."""
        return WorkflowState(
            question=query,
            category="",
            response=""
        )
    
    def _build_workflow(self):
        """Creates a workflow for routing OpenSearch questions"""
        workflow = StateGraph(WorkflowState)
        
        # Add nodes to our graph
        workflow.add_node("classify", classify_question)
        workflow.add_node("install", handle_installation)
        workflow.add_node("security", handle_security)
        workflow.add_node("query", handle_querying)
        workflow.add_node("performance", handle_performance)
        
        # Create conditional routing
        workflow.add_edge(START, "classify")
        
        # Create conditional edges based on the category
        workflow.add_conditional_edges(
            "classify",
            lambda state: state["category"],
            {
                "INSTALL": "install",
                "SECURITY": "security",
                "QUERY": "query",
                "PERFORMANCE": "performance"
            }
        )
        
        # All handlers lead to END
        workflow.add_edge("install", END)
        workflow.add_edge("security", END)
        workflow.add_edge("query", END)
        workflow.add_edge("performance", END)
        
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

        return final_state["response"]