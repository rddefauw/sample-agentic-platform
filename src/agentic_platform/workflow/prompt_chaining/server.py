from fastapi import FastAPI
import uvicorn
import logging
import os

from agentic_platform.core.models.api_models import AgenticRequest, AgenticResponse
from agentic_platform.core.decorator.api_error_decorator import handle_exceptions
from agentic_platform.core.middleware.configure_middleware import configuration_server_middleware
from agentic_platform.workflow.prompt_chaining.chaining_controller import PromptChainingSearchWorkflowController

# Get logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

app = FastAPI(title="Prompt Chaining Workflow")

# Essential middleware.
configuration_server_middleware(app,path_prefix="/prompt-chaining")

# Essential endpoints
@app.post("/search", response_model=AgenticResponse)
@handle_exceptions(status_code=500, error_prefix="Prompt Chaining Workflow API Error")
async def search(request: AgenticRequest) -> AgenticResponse:
    """
    Search with a langgraph prompt chaining workflow.
    """
    return PromptChainingSearchWorkflowController.search(request)

@app.get("/health")
async def health():
    """
    Health check endpoint for Kubernetes probes.
    """
    return {"status": "healthy"}

# Run the server with uvicorn.
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) # nosec B104 - Binding to all interfaces within container is intended