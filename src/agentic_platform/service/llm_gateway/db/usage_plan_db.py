import boto3
import hashlib
from typing import Dict, Optional, List, Any
from agentic_platform.service.llm_gateway.models.usage_types import UsagePlan, UsagePlanEntityType
import os

# Constants
USAGE_PLANS_TABLE = os.getenv('DYNAMODB_USAGE_PLANS_TABLE')

# Create DynamoDB resource once at module level
ddb = boto3.resource('dynamodb')
plans_table = ddb.Table(USAGE_PLANS_TABLE)

class UsagePlanDB:
    """Client for usage plan management in DynamoDB."""

    @classmethod
    def hash_key(cls, key: str) -> str:
        """Hash API keys for secure storage."""
        return hashlib.sha256(key.encode()).hexdigest()
    
    @classmethod
    def _to_dynamo_item(cls, plan: UsagePlan) -> Dict[str, Any]:
        """Convert Pydantic model to DynamoDB item format"""
        plan_dict = plan.model_dump(mode='json')
        # Entity type is always provided, just convert to string
        plan_dict['entity_type'] = str(plan_dict['entity_type'])
        return plan_dict

    @classmethod
    def _from_dynamo_item(cls, item: Dict[str, Any]) -> UsagePlan:
        """Convert DynamoDB item to Pydantic model"""
        # Entity type is always a string in DynamoDB, convert to enum
        if 'entity_type' in item:
            item['entity_type'] = UsagePlanEntityType(item['entity_type'])
        return UsagePlan.model_validate(item)

    @classmethod
    def get_plan_by_id(cls, entity_id: str, entity_type: UsagePlanEntityType) -> Optional[UsagePlan]:
        """
        Fetch the usage plan using the primary key (entity_id + entity_type).
        """
        try:
            # Convert enum to string for DynamoDB
            entity_type_str = str(entity_type)

            # If we're looking up by API key, we need to hash the key
            if entity_type == UsagePlanEntityType.API_KEY:
                entity_id = cls.hash_key(entity_id)
            
            response = plans_table.get_item(
                Key={
                    'entity_id': entity_id,
                    'entity_type': entity_type_str
                }
            )
            
            if 'Item' not in response:
                return None
                
            return cls._from_dynamo_item(response['Item'])
        except Exception as e:
            print(f"Error getting plan: {e}")
            return None
    
    @classmethod
    def create_plan(cls, plan: UsagePlan) -> bool:
        """Create new usage plan in DynamoDB."""        
        try:
            # So we don't modify the original plan
            plan_copy = plan.model_copy()
            
            # If an API key is being generated, we need to hash the key
            if plan_copy.entity_type == UsagePlanEntityType.API_KEY:
                plan_copy.entity_id = cls.hash_key(plan_copy.entity_id)
            
            # Convert to DynamoDB item
            item = cls._to_dynamo_item(plan_copy)
            
            print(f"Creating plan: {item}")
            # Put the item
            plans_table.put_item(Item=item)
            
            return True
        except Exception as e:
            print(f"Error creating plan: {e}")
            return False

    @classmethod
    async def deactivate_plan(cls, entity_id: str, entity_type: UsagePlanEntityType) -> bool:
        """Mark a plan as inactive by updating the active flag."""
        try:
            # Convert enum to string for DynamoDB
            entity_type_str = str(entity_type)
                
            plans_table.update_item(
                Key={
                    'entity_id': entity_id,
                    'entity_type': entity_type_str
                },
                UpdateExpression='SET active = :false',
                ExpressionAttributeValues={':false': False}
            )
            return True
        except Exception as e:
            print(f"Error deactivating plan: {e}")
            return False
            
    @classmethod
    def get_plans_by_tenant(cls, tenant_id: str) -> List[UsagePlan]:
        """Get all plans for a tenant using the GSI."""
        try:
            response = plans_table.query(
                IndexName='tenant_index',
                KeyConditionExpression='tenant_id = :tid',
                ExpressionAttributeValues={':tid': tenant_id}
            )
            
            if not response.get('Items'):
                return []
                
            return [cls._from_dynamo_item(item) for item in response['Items']]
        except Exception as e:
            print(f"Error getting plans by tenant: {e}")
            return []