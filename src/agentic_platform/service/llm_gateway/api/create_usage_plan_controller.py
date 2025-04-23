from agentic_platform.service.llm_gateway.models.gateway_api_types import CreateUsagePlanRequest, CreateUsagePlanResponse
from agentic_platform.service.llm_gateway.client.usage_plan_client import UsagePlanClient
from agentic_platform.service.llm_gateway.models.usage_types import UsagePlan

class CreateUsagePlanController:

    @classmethod
    def create(cls, request: CreateUsagePlanRequest) -> CreateUsagePlanResponse:
        # Define our key.
        # Convert request to a dict
        data = request.model_dump()
        
        # Set tenant_id to 'SYSTEM' if not provided
        if not data.get('tenant_id'):
            data['tenant_id'] = 'SYSTEM'
        
        # Create UsagePlan object, applying all model defaults
        plan = UsagePlan.model_validate(data)

        # Create the key.
        response: UsagePlan = UsagePlanClient.create_usage_plan(plan)
        # Return the key.
        return CreateUsagePlanResponse(
            plan=response
        )