from fastapi import FastAPI
import uvicorn
import logging
import os

from agentic_platform.core.models.api_models import SearchWorkflowRequest, SearchWorkflowResponse
from agentic_platform.core.decorator.api_error_decorator import handle_exceptions
from agentic_platform.core.middleware.configure_middleware import configuration_server_middleware
from agentic_platform.workflow.orchestrator.orchestrator_controller import OrchestratorSearchWorkflowController

# Get logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

app = FastAPI(title="Orchestrator Workflow")

# Essential middleware.
configuration_server_middleware(app,path_prefix="/orchestrator")

# Essential endpoints
@app.post("/search", response_model=SearchWorkflowResponse)
@handle_exceptions(status_code=500, error_prefix="Search Workflow API Error")
async def search(request: SearchWorkflowRequest) -> SearchWorkflowResponse:
    """
    Search with a langgraph orchestrator workflow.
    """
    return OrchestratorSearchWorkflowController.search(request)

@app.get("/health")
async def health():
    """
    Health check endpoint for Kubernetes probes.
    """
    return {"status": "healthy"}

# Run the server with uvicorn.
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) # nosec B104 - Binding to all interfaces within container is intended