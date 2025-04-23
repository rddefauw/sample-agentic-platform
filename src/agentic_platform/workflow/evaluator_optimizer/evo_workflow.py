from typing import Dict
from langgraph.graph import StateGraph, START, END

from agentic_platform.workflow.evaluator_optimizer.evo_nodes import (
    generate_answer, 
    evaluate_answer, 
    improve_answer, 
    finalize_answer,
    should_improve,
    WorkflowState
)

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
class EvaluatorOptimizerWorkflow:
    """
    Implements the evaluator-optimizer workflow pattern from module 2.
    """
    
    def __init__(self, max_iterations: int = 3):
        """
        Initialize the EvaluatorOptimizerWorkflow with a compiled workflow graph.
        """
        self.max_iterations = max_iterations
        self.workflow = self._build_workflow()

    def _init_state(self, question: str) -> WorkflowState:
        """Initialize the workflow state with a question."""
        return WorkflowState(
            question=question,
            answer="",
            context="",
            feedback="",
            iteration=0,
            final_answer=None
        )
    
    def _build_workflow(self):
        """Builds the evaluator-optimizer workflow"""
        workflow = StateGraph(WorkflowState)

        # Add nodes to the graph
        workflow.add_node("generate", generate_answer)
        workflow.add_node("evaluate", evaluate_answer)
        workflow.add_node("improve", improve_answer)
        workflow.add_node("finalize", finalize_answer)
        
        # Connect the workflow
        workflow.add_edge(START, "generate")
        workflow.add_edge("generate", "evaluate")

        # Build decision map. 
        decision_map: Dict[str, str] = {
            "IMPROVE": "improve",
            "DONE": "finalize"
        }

        # Add conditional edges.
        workflow.add_conditional_edges("evaluate", should_improve, decision_map)

        # Create the improvement loop
        workflow.add_edge("improve", "evaluate")

        # Finalize the workflow
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    def run(self, question: str) -> str:
        """
        Run the search workflow with a given query.
        """
        # Initialize state
        initial_state: WorkflowState = self._init_state(question)

        # Run the workflow
        final_state: WorkflowState = self.workflow.invoke(initial_state)
        
        return final_state["final_answer"]