from agentic_platform.core.models.api_models import SearchWorkflowRequest, SearchWorkflowResponse
from agentic_platform.workflow.evaluator_optimizer.evo_workflow import EvaluatorOptimizerWorkflow
import uuid

# Instantiate the chat service so we don't recreate the graph on each request.
evaluator_optimizer_workflow = EvaluatorOptimizerWorkflow()

class EvaluatorOptimizerWorkflowController:

    @staticmethod
    def search(request: SearchWorkflowRequest) -> SearchWorkflowResponse:
        """
        Search with the LangGraph search workflow. 
        """
        response: str = evaluator_optimizer_workflow.run(request.query)
        
        # Return the chat response object to the server.
        return SearchWorkflowResponse(
            response=response,
            conversationId=str(uuid.uuid4())
        )