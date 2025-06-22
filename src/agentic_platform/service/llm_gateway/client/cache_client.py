from redis.asyncio import Redis, ConnectionPool
from redis.exceptions import RedisClusterException
from agentic_platform.service.llm_gateway.db.usage_plan_db import UsagePlanDB
from agentic_platform.service.llm_gateway.models.usage_types import RateLimitResult, UsagePlan, RateLimits, UsagePlanEntityType
from agentic_platform.service.llm_gateway.secret.get_redis_pass import get_redis_password
import os
import time
from typing import Tuple, List, Optional
from redis.asyncio.connection import SSLConnection

ENVIRONMENT: str = os.getenv('ENVIRONMENT')

connection_params = {
    "host": os.getenv('REDIS_HOST'),
    "port": int(os.getenv('REDIS_PORT')),
    "password": get_redis_password(),
    "decode_responses": True,
}

if ENVIRONMENT != 'local':
    connection_params["connection_class"] = SSLConnection
    connection_params["ssl_cert_reqs"] = "none"

# Global Redis connection pool
REDIS_POOL = ConnectionPool(**connection_params)

class RateLimiter:
    """Redis-based rate limiter with sliding window."""
    
    WINDOW_SIZE = 60  # seconds
    USAGE_PLAN_CACHE_TTL = 60 * 60 * 24 * 1  #1 days
    redis = Redis(connection_pool=REDIS_POOL)
    
    @classmethod
    def _get_rate_limit_keys(cls, usage_plan: UsagePlan, model_id: str) -> Tuple[str, str]:
        """Get Redis keys for the current time window."""
        window = int(time.time()) - (int(time.time()) % cls.WINDOW_SIZE)
        return (
            f"usage:{usage_plan.entity_type}:{usage_plan.entity_id}:{window}",
            f"usage:{usage_plan.entity_type}:{usage_plan.entity_id}:{model_id}:{window}"
        )
    
    @classmethod
    def _get_usage_plan_key(cls, entity_id: str, entity_type: UsagePlanEntityType) -> str:
        """Get Redis key for the Usage Plan."""
        return f"usage_plan:{entity_type}:{entity_id}"
    
    @classmethod
    async def cache_usage_plan(cls, usage_plan: UsagePlan) -> bool:
        """
        Cache Usage Plan details in Redis.
        """
        try:
            # Convert UsagePlan to dict for storage
            key_data: str = usage_plan.model_dump_json()
            redis_key: str = cls._get_usage_plan_key(usage_plan.entity_id, usage_plan.entity_type)
            # Store in Redis with TTL
            await cls.redis.setex(redis_key, cls.USAGE_PLAN_CACHE_TTL, key_data)
            return True
        except Exception:
            return False

    @classmethod
    async def get_usage_plan_from_cache(cls, entity_id: str, entity_type: UsagePlanEntityType) -> Optional[UsagePlan]:
        """Get Usage Plan details from Redis cache.
        """
        try:
            # If the entity type is API_KEY, we need to hash the entity_id.
            if entity_type == UsagePlanEntityType.API_KEY:
                entity_id = UsagePlanDB.hash_key(entity_id)

            # Try to get from Redis
            cached_data: str = await cls.redis.get(cls._get_usage_plan_key(entity_id, entity_type))
            if not cached_data:
                return None
            
            # Return the data asn an API Key Object.
            print(f"Cached data: {cached_data}")
            return UsagePlan.model_validate_json(cached_data)
        except Exception:
            return None

    @classmethod
    async def check_limit(cls, plan: UsagePlan, model_id: str, est_input: int, est_output: int) -> RateLimitResult:
        """Check if the estimated token usage would exceed rate limits."""
        global_key, model_key = cls._get_rate_limit_keys(plan, model_id)
        
        # Get current usage with pipeline
        tr = cls.redis.pipeline()
        tr.hmget(global_key, ['input', 'output', 'rpm'])
        tr.hmget(model_key, ['input', 'output', 'rpm'])
        results = await tr.execute()
        
        # Parse usage
        tenant_vals: List[int] = [int(v or 0) for v in (results[0] or [0, 0, 0])]
        model_vals: List[int] = [int(v or 0) for v in (results[1] or [0, 0, 0])]
        
        limits: RateLimits = plan.get_limits_for_model(model_id)

        current: RateLimits = RateLimits(
            input_tpm=tenant_vals[0],
            output_tpm=tenant_vals[1],
            rpm=tenant_vals[2]
        )
        model: RateLimits = RateLimits(
            input_tpm=model_vals[0],
            output_tpm=model_vals[1],
            rpm=model_vals[2]
        )

        # Check if would exceed
        would_exceed = any([
            current.input_tpm + est_input > limits.input_tpm,
            current.output_tpm + est_output > limits.output_tpm,
            current.rpm + 1 > limits.rpm,
            model.input_tpm + est_input > limits.input_tpm,
            model.output_tpm + est_output > limits.output_tpm,
            model.rpm + 1 > limits.rpm
        ])

        return RateLimitResult(
            allowed=not would_exceed,
            tenant_id=plan.tenant_id,
            model_id=model_id,
            current_usage=current,
            model_usage=model,
            applied_limits=limits,
            model_limits=limits
        )

    @classmethod
    async def record_usage(cls, plan: UsagePlan, model_id: str, input_tokens: int, output_tokens: int) -> bool:
        """
        Record actual token usage in the current window.

        This is best effort. We'd rather keep the system running if this fails for some reason.
        """
        global_key, model_key = cls._get_rate_limit_keys(plan, model_id)
        
        try:
            tr = cls.redis.pipeline()
            
            # Update both tenant and model usage
            for key in (global_key, model_key):
                tr.hincrby(key, 'input', input_tokens)
                tr.hincrby(key, 'output', output_tokens)
                tr.hincrby(key, 'rpm', 1)
                tr.expire(key, cls.WINDOW_SIZE * 2)
            
            await tr.execute()

            return True
            
        except RedisClusterException:
            return False