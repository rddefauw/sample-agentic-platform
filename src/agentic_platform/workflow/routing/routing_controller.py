from agentic_platform.core.models.api_models import SearchWorkflowRequest, SearchWorkflowResponse
from agentic_platform.workflow.routing.routing_workflow import RoutingSearchWorkflow
import uuid

# Instantiate the chat service so we don't recreate the graph on each request.
search_workflow = RoutingSearchWorkflow()

class RoutingSearchWorkflowController:

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