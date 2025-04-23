from typing import Dict
from langgraph.graph import StateGraph, START, END

from agentic_platform.workflow.orchestrator.orchestrator_nodes import (
    assign_workers,
    plan_diagnostics,
    investigate_issue,
    synthesize_findings,
    TroubleshootingState,
)

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class OrchestratorSearchWorkflow:
    """
    Implements the orchestrator workflow pattern from module 3.
    """
    
    def __init__(self, max_iterations: int = 3):
        """
        Initialize the SearchOptimizerWorkflow with a compiled workflow graph.
        """
        self.max_iterations = max_iterations
        self.workflow = self._build_workflow()

    def init_state(self, query: str) -> TroubleshootingState:
        """Initialize the workflow state with a question."""
        return TroubleshootingState(
            problem=query,
            diagnostic_plan=[],
            investigation_results=[],
            final_report=""
        )
    
    def _build_workflow(self):
        """Creates a parallel workflow for orchestrated troubleshooting using RAG"""
        # Initialize the state graph with our state structure
        workflow = StateGraph(TroubleshootingState)
        
        # Add nodes to our graph
        workflow.add_node("plan", plan_diagnostics)
        workflow.add_node("investigate_issue", investigate_issue)
        workflow.add_node("synthesize", synthesize_findings)
        
        # Connect the workflow
        workflow.add_edge(START, "plan")
        workflow.add_conditional_edges("plan", assign_workers, ["investigate_issue"])
        workflow.add_edge("investigate_issue", "synthesize")
        workflow.add_edge("synthesize", END)
        
        return workflow.compile()

    
    def run(self, query: str) -> str:
        """
        Run the search workflow with a given query.
        """
        # Initialize state
        initial_state: TroubleshootingState = self.init_state(query=query)

        # Run the workflow
        final_state: TroubleshootingState = self.workflow.invoke(initial_state)

        return final_state["final_report"]