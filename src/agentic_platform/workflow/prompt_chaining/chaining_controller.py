from agentic_platform.core.models.api_models import AgenticRequest, AgenticResponse
from agentic_platform.workflow.prompt_chaining.chaining_workflow import PromptChainingSearchWorkflow
from agentic_platform.core.models.memory_models import Message
import uuid

# Instantiate the chat service so we don't recreate the graph on each request.
search_workflow = PromptChainingSearchWorkflow()

class PromptChainingSearchWorkflowController:

    @staticmethod
    def search(request: AgenticRequest) -> AgenticResponse:
        """
        Search with the LangGraph prompt chaining workflow. 
        """
        # Get the latest user text from the request
        user_text = request.latest_user_text
        if not user_text:
            user_text = "Hello"  # Default fallback
        
        response_text: str = search_workflow.run(user_text)
        
        # Create response message
        response_message = Message.from_text("assistant", response_text)
        
        # Return the agent response
        return AgenticResponse(
            message=response_message,
            session_id=request.session_id
        )