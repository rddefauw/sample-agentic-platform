from agentic_platform.core.models.api_models import AgenticRequest, AgenticResponse
from agentic_platform.workflow.evaluator_optimizer.evo_workflow import EvaluatorOptimizerWorkflow
from agentic_platform.core.models.memory_models import Message
import uuid

# Instantiate the chat service so we don't recreate the graph on each request.
evaluator_optimizer_workflow = EvaluatorOptimizerWorkflow()

class EvaluatorOptimizerWorkflowController:

    @staticmethod
    def search(request: AgenticRequest) -> AgenticResponse:
        """
        Search with the LangGraph evaluator optimizer workflow. 
        """
        # Get the latest user text from the request
        user_text = request.latest_user_text
        if not user_text:
            user_text = "Hello"  # Default fallback
        
        response_text: str = evaluator_optimizer_workflow.run(user_text)
        
        # Create response message
        response_message = Message.from_text("assistant", response_text)
        
        # Return the agent response
        return AgenticResponse(
            message=response_message,
            session_id=request.session_id
        )