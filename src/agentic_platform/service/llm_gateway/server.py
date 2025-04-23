# Continue with regular imports.
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
from agentic_platform.core.middleware.path_middleware import PathTransformMiddleware
from agentic_platform.service.llm_gateway.models.gateway_api_types import (
    ConverseRequest,
    ConverseResponse,
    CreateUsagePlanRequest,
    CreateUsagePlanResponse,
    RevokeUsagePlanRequest,
    RevokeUsagePlanResponse
)
from agentic_platform.service.llm_gateway.api.create_usage_plan_controller import CreateUsagePlanController
from agentic_platform.service.llm_gateway.api.revoke_usage_plan_controller import RevokeUsagePlanController
from agentic_platform.service.llm_gateway.api.converse_controller import ConverseController
from agentic_platform.core.middleware.configure_middleware import configuration_server_middleware
from agentic_platform.service.llm_gateway.api.get_usage_plan_controller import GetUsagePlanController
from agentic_platform.service.llm_gateway.models.usage_types import UsagePlan, UsagePlanEntityType
from agentic_platform.core.models.auth_models import AgenticPlatformAuth

app = FastAPI()

# Configure middelware that's common to all servers.
configuration_server_middleware(app, path_prefix="/llm-gateway")

# In our custom LLM Gateway Auth middleware, we store the auth object in the request state.
# This is the easiest way to support both API key and JwT authentication.
async def get_usage_plan(request: Request) -> UsagePlan:
    auth: AgenticPlatformAuth = request.state.auth

    entity_id: str = None
    entity_type: UsagePlanEntityType = None
    if auth.type == "user":
        entity_id = auth.user.user_id
        entity_type = UsagePlanEntityType.USER
    elif auth.type == "service":
        entity_id = auth.service.service_id
        entity_type = UsagePlanEntityType.SERVICE
    else:
        raise HTTPException(status_code=401, detail="Invalid authentication method")
    
    print(f"entity_id: {entity_id}, entity_type: {entity_type}")

    # Get usage plan checks the cache first which is an async operation.
    # The idea here is that every request at ths point is authenticated. So we want to create a 
    # default usage plan if one doesn't exist with pretty low values. Admins can always change it later.
    return await GetUsagePlanController.get_or_create_usage_plan(entity_id, entity_type)

@app.post("/model/{model_id}/converse")
async def converse(model_id: str, request: Request) -> ConverseResponse:
    """Call Bedrock converse endpoint."""
    usage_plan: UsagePlan = await get_usage_plan(request) 
    # Get the request body as a dictionary.
    request_body: Dict[Any, Any] = await request.json()
    # Create a ConverseRequest object.
    converse_request: ConverseRequest = ConverseRequest(modelId=model_id, **request_body)
    # Call the converse controller.
    return await ConverseController.converse(converse_request, usage_plan)
    
@app.post("/create-key")
async def create_key(request: CreateUsagePlanRequest) -> CreateUsagePlanResponse:
    """Create an API Key."""
    return CreateUsagePlanController.create_key(request)

@app.post("/revoke-key")
async def revoke_key(request: RevokeUsagePlanRequest) -> RevokeUsagePlanResponse:
    """Revoke an API Key."""
    return RevokeUsagePlanController.revoke_key(request)

@app.get("/health")
async def health():
    """
    Health check endpoint for Kubernetes probes.
    """
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4000)  # nosec B104 - Binding to all interfaces within container is intended