import boto3
from typing import Optional, List
from agentic_platform.service.llm_gateway.models.usage_types import UsagePlan, UsagePlanEntityType
from agentic_platform.service.llm_gateway.db.usage_plan_db import UsagePlanDB
import os

# Constants
USAGE_PLANS_TABLE = os.getenv('DYNAMODB_USAGE_PLANS_TABLE')

# Create DynamoDB resource once at module level
ddb = boto3.resource('dynamodb')
key_table = ddb.Table(USAGE_PLANS_TABLE)

class UsagePlanClient:
    """Client for usage plan management - abstraction layer over the DB client."""

    @classmethod
    def get_plan_by_id(cls, entity_id: str, entity_type: UsagePlanEntityType) -> Optional[UsagePlan]:
        """Fetch a usage plan by its ID and type."""
        return UsagePlanDB.get_plan_by_id(entity_id, entity_type)

    @classmethod
    def create_usage_plan(cls, plan: UsagePlan) -> UsagePlan:
        """Create a new API key with associated usage plan."""        
        # Create the plan in the database
        success: bool = UsagePlanDB.create_plan(plan)
        # In the APIKey case, we want to return the plan with the raw key
        return plan    
        
    @classmethod
    async def revoke_usage_plan(cls, entity_id: str, entity_type: UsagePlanEntityType) -> bool:
        """Revoke an API key by marking it as inactive."""
        # Hash the key to get the entity_id
        if entity_type == UsagePlanEntityType.API_KEY:
            entity_id = cls.hash_key(entity_id)
        
        # Deactivate the plan
        return await UsagePlanDB.deactivate_plan(
            entity_id=entity_id, 
            entity_type=entity_type
        )

    @classmethod
    def validate_plan(cls, entity_id: str, entity_type: UsagePlanEntityType) -> Optional[UsagePlan]:
        """Validate a raw API key and return the associated plan if active."""
        # Hash the key
        if entity_type == UsagePlanEntityType.API_KEY:
            entity_id = cls.hash_key(entity_id)
        
        # Get the plan
        plan: Optional[UsagePlan] = UsagePlanDB.get_plan_by_id(
            entity_id=entity_id,
            entity_type=entity_type
        )

        return plan if plan and plan.active else None

    @classmethod
    def get_usage_keys_by_tenant(cls, tenant_id: str) -> List[UsagePlan]:
        """Get all API keys for a tenant."""
        # Get all plans for the tenant
        return UsagePlanDB.get_plans_by_tenant(tenant_id)