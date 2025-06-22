import boto3
import uuid
from typing import Dict, List
from boto3.dynamodb.conditions import Key
from agentic_platform.service.llm_gateway.models.usage_types import UsageRecord
import os

# Constants
USAGE_TABLE = os.getenv('DYNAMODB_USAGE_LOGS_TABLE')
USAGE_TTL_SECONDS = 30 * 24 * 60 * 60  # 30 days in seconds

# Create DynamoDB resource once at module level
ddb = boto3.resource('dynamodb')
usage_table = ddb.Table(USAGE_TABLE)

class UsageClient:
    """Client for usage tracking in DynamoDB.
    
    Table Schema:
    - Partition Key: tenant_id (string)
    - Sort Key: usage_id (string, format: "timestamp#model#request_id")
    - GSI: tenant_timestamp_index
        - Partition Key: tenant_id
        - Sort Key: timestamp
    
    Used for:
    - Audit trails
    - Billing reconciliation
    - Historical record keeping
    - Per-request debugging
    """
    
    @classmethod
    def _to_dynamo_item(cls, record: UsageRecord) -> Dict:
        timestamp = record.timestamp
        total_tokens = record.input_tokens + record.output_tokens
        return {
            'tenant_id': record.tenant_id,
            'usage_id': f"{timestamp}#{record.model}#{uuid.uuid4().hex}",
            'model': record.model,
            'input_tokens': record.input_tokens,
            'output_tokens': record.output_tokens,
            'total_tokens': total_tokens,
            'timestamp': timestamp,
            'metadata': record.metadata,
            'ttl': timestamp + USAGE_TTL_SECONDS
        }

    @classmethod
    def _from_dynamo_item(cls, item: Dict) -> UsageRecord:
        return UsageRecord(
            tenant_id=item['tenant_id'],
            timestamp=item['timestamp'],
            model=item['model'],
            input_tokens=item['input_tokens'],
            output_tokens=item['output_tokens'],
            metadata=item.get('metadata', {})
        )

    @classmethod
    async def record_usage(cls, record: UsageRecord) -> bool:
        """Record detailed usage for audit and billing."""
        try:
            usage_table.put_item(Item=cls._to_dynamo_item(record))
            return True
        except Exception:
            return False

    @classmethod
    async def get_usage(cls, tenant_id: str, start_time: int, end_time: int) -> List[UsageRecord]:
        """Query usage by time range for billing and audit."""
        response = usage_table.query(
            KeyConditionExpression=Key('tenant_id').eq(tenant_id) & Key('timestamp').between(start_time, end_time),
            IndexName='tenant_timestamp_index'
        )
        
        return [cls._from_dynamo_item(item) for item in response['Items']]