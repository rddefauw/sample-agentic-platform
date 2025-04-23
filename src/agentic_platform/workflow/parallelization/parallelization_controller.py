from agentic_platform.core.models.api_models import SearchWorkflowRequest, SearchWorkflowResponse
from agentic_platform.workflow.parallelization.parallelization_workflow import ParallelizationSearchWorkflow
import uuid

# Instantiate the chat service so we don't recreate the graph on each request.
search_workflow = ParallelizationSearchWorkflow()

class ParallelizationSearchWorkflowController:

    @staticmethod
    def search(request: SearchWorkflowRequest) -> SearchWorkflowResponse:
        """
        Search with the LangGraph search workflow. 
        """
        response: str = search_workflow.run(request.query)
        
        # Return the chat response object to the server.
        return SearchWorkflowResponse(
            response=response,
            conversationId=str(uuid.uuid4())
        )