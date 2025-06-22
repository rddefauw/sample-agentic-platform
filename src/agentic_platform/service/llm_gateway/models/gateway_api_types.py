from pydantic import BaseModel, Field, model_validator, ConfigDict
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from agentic_platform.service.llm_gateway.models.usage_types import (
    UsageRecord,
    RateLimits,
    UsagePlan,
    UsagePlanEntityType
)

class CreateUsagePlanRequest(BaseModel):
    entity_type: UsagePlanEntityType  # Always required
    entity_id: str
    tenant_id: Optional[str] = None
    model_permissions: List[str]
    model_limits: Dict[str, RateLimits] = Field(default_factory=dict)
    default_limits: RateLimits = Field(default_factory=RateLimits)
    metadata: Optional[Dict] = Field(default_factory=dict)
    active: bool = True
    

class CreateUsagePlanResponse(BaseModel):
    plan: UsagePlan

class RevokeUsagePlanRequest(BaseModel):
    entity_id: str
    entity_type: UsagePlanEntityType

class RevokeUsagePlanResponse(BaseModel):
    success: bool

class CheckRateLimitsRequest(BaseModel):
    '''This is an internal API type.'''
    tenant_id: str
    model_id: str
    estimated_input_tokens: int
    estimated_output_tokens: int

class GetUsageSummaryRequest(BaseModel):
    tenant_id: str
    start_time: datetime
    end_time: datetime

class GetUsageSummaryResponse(BaseModel):
    usage_records: List[UsageRecord]

# For the passthrough endpoint
class ConverseRequest(BaseModel):
    model_config = ConfigDict(extra="allow")  # This allows arbitrary additional fields which is the rest of the request body.
    
    modelId: str

class ConverseResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    
    output: Dict[str, Any]

class ChatCompletionRequest(BaseModel):
    model_config = ConfigDict(extra="allow")  # This allows arbitrary additional fields which is the rest of the request body.
    
    model: str

class ChatCompletionResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    
    choices: List[Any]