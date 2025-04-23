from agentic_platform.service.llm_gateway.models.gateway_api_types import RevokeUsagePlanRequest, RevokeUsagePlanResponse
from agentic_platform.service.llm_gateway.client.usage_plan_client import UsagePlanClient

class RevokeUsagePlanController:

    @classmethod
    def revoke_usage_plan(cls, request: RevokeUsagePlanRequest) -> RevokeUsagePlanResponse:
        # Revoke the key.
        response: bool = UsagePlanClient.revoke_usage_plan(request.entity_id, request.entity_type)
        # Return the response.
        return RevokeUsagePlanResponse(success=response)