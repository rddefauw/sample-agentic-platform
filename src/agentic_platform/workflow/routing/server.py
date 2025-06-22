from fastapi import FastAPI
import uvicorn
import logging
import os

from agentic_platform.core.models.api_models import AgenticRequest, AgenticResponse
from agentic_platform.core.decorator.api_error_decorator import handle_exceptions
from agentic_platform.core.middleware.configure_middleware import configuration_server_middleware
from agentic_platform.workflow.routing.routing_controller import RoutingSearchWorkflowController

# Get logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

app = FastAPI(title="Routing Workflow")

# Essential middleware.
configuration_server_middleware(app,path_prefix="/routing")

# Essential endpoints
@app.post("/search", response_model=AgenticResponse)
@handle_exceptions(status_code=500, error_prefix="Routing Workflow API Error")
async def search(request: AgenticRequest) -> AgenticResponse:
    """
    Search with a langgraph routing workflow.
    """
    return RoutingSearchWorkflowController.search(request)

@app.get("/health")
async def health():
    """
    Health check endpoint for Kubernetes probes.
    """
    return {"status": "healthy"}

# Run the server with uvicorn.
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) # nosec B104 - Binding to all interfaces within container is intended