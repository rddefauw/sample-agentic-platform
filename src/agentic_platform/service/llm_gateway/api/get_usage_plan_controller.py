from agentic_platform.service.llm_gateway.client.usage_plan_client import UsagePlanClient
from agentic_platform.service.llm_gateway.db.usage_plan_db import UsagePlanDB
from agentic_platform.service.llm_gateway.models.usage_types import UsagePlan, UsagePlanEntityType
from agentic_platform.service.llm_gateway.client.cache_client import RateLimiter
from typing import Optional
from agentic_platform.service.llm_gateway.api.create_usage_plan_controller import CreateUsagePlanController
from agentic_platform.service.llm_gateway.models.gateway_api_types import CreateUsagePlanRequest
class GetUsagePlanController:

    @classmethod
    async def get_usage_plan(cls, entity_id: str, entity_type: UsagePlanEntityType) -> Optional[UsagePlan]:

        # if api key, we need to hash the key.
        if entity_type == UsagePlanEntityType.API_KEY:
            entity_id = UsagePlanDB.hash_key(entity_id)

        # Check Redis cache first.
        cached_key: Optional[UsagePlan] = await RateLimiter.get_usage_plan_from_cache(entity_id, entity_type)
        # If we have a cached key just return it.
        if cached_key:
            return cached_key

        # Check DynamoDB if not in cache.
        ddb_key: Optional[UsagePlan] = UsagePlanClient.get_plan_by_id(entity_id, entity_type)

        # If we have a DDB key, cache it and return it.
        if ddb_key:
            await RateLimiter.cache_usage_plan(ddb_key)
            return ddb_key
        
        return None
    
    @classmethod
    async def get_or_create_usage_plan(cls, entity_id: str, entity_type: UsagePlanEntityType) -> UsagePlan:
        print(f"\n\n\n\n\n\n\n\nGetting or creating usage plan for entity_id: {entity_id}, entity_type: {entity_type}")
        usage_plan: Optional[UsagePlan] = await cls.get_usage_plan(entity_id, entity_type)
        if usage_plan:
            return usage_plan
        
        # If it doesn't exist, create it with the default values. This can always be changed later by an admin
        create_request: CreateUsagePlanRequest = CreateUsagePlanRequest(
            entity_id=entity_id,
            entity_type=entity_type,
            model_permissions=['*']
        )
        response = CreateUsagePlanController.create(create_request)
        return response.plan
