from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Optional, Literal
import time
import uuid
import re
from enum import Enum
class UsagePlanEntityType(str, Enum):
    USER = "USER"
    SERVICE = "SERVICE"
    API_KEY = "API_KEY"
    DEPARTMENT = "DEPARTMENT"
    PROJECT = "PROJECT"

    def __str__(self) -> str:
        return self.value

class RateLimits(BaseModel):
    """Rate limits configuration"""
    input_tpm: int = Field(default=40000, description="Input tokens per minute limit")
    output_tpm: int = Field(default=10000, description="Output tokens per minute limit")
    rpm: int = Field(default=60, description="Requests per minute limit")

class UsagePlan(BaseModel):
    """Usage plan with rate limits"""
    usage_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_id: str
    entity_type: UsagePlanEntityType
    tenant_id: str = 'SYSTEM' # By default, we assume no tenancy unless the user has a tenant_id (either team or org.)
    budget_id: Optional[str] = None # Placeholder for future use.
    model_permissions: List[str]
    active: bool = Field(default=True)
    default_limits: RateLimits = Field(default_factory=RateLimits)
    model_limits: Dict[str, RateLimits] = Field(default_factory=dict)
    metadata: Optional[Dict] = Field(default_factory=dict)
    created_at: int = Field(default_factory=lambda: int(time.time()))

    def get_limits_for_model(self, model_id: str) -> RateLimits:
        """Get limits for a specific model, falling back to defaults"""
        return self.model_limits.get(model_id, self.default_limits)
    

class RateLimitResult(BaseModel):
    """Result from rate limit check"""
    allowed: bool
    tenant_id: str
    model_id: str
    
    # Current usage and limits
    current_usage: RateLimits
    model_usage: RateLimits
    applied_limits: RateLimits
    model_limits: RateLimits

class UsageRecord(BaseModel):
    """Record of API usage"""
    tenant_id: str
    model: str
    input_tokens: int
    output_tokens: int
    timestamp: int = Field(default_factory=lambda: int(time.time()))
    metadata: Optional[Dict] = Field(default_factory=dict)