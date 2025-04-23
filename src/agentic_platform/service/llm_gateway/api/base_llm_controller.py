from agentic_platform.service.llm_gateway.models.usage_types import RateLimitResult, UsageRecord, UsagePlan, UsagePlanEntityType
from agentic_platform.service.llm_gateway.client.cache_client import RateLimiter
from agentic_platform.service.llm_gateway.client.usage_client import UsageClient
from agentic_platform.service.llm_gateway.client.usage_plan_client import UsagePlanClient
from agentic_platform.service.llm_gateway.api.get_usage_plan_controller import GetUsagePlanController
from fastapi import HTTPException
from typing import Tuple, Optional

class BaseLLMController:

    @classmethod
    def _estimate_tokens(cls, model_id: str, input: str, max_output_tokens: int = 256) -> Tuple[int, int]:
        '''
        You can call the tokenizer here to get exact numbers, but we'd rather not take the latency hit here.
        You can create estimators for each model if you prefer. For now that param isn't used.
        '''
        # Each word is approximately 1.33 tokens. Some tokenizers are different but this gives us a good estimate.
        estimated_input = len(input.split()) * 1.33
        estimated_output = max_output_tokens
        return estimated_input, estimated_output
    
    @classmethod
    async def _get_plan(cls, entity_id: str, entity_type: UsagePlanEntityType) -> UsagePlan:
        return await GetUsagePlanController.get_usage_plan(entity_id, entity_type)

    @classmethod
    async def check_rate_limits(cls, plan: UsagePlan, model_id: str, input: str) -> RateLimitResult:
        '''
        Check the rate limits for the given key and model. Each invocation controller 
        will inherit this class to implement the specific logic for the given path.
        '''
        print(f"Checking rate limits for plan: {plan}, model_id: {model_id}, input: {input}")
        # Estimate token usage using heuristics to keep network calls to a minimum.
        est_input, est_output = cls._estimate_tokens(model_id, input)
        limit_result: RateLimitResult = await RateLimiter.check_limit(plan, model_id, est_input, est_output)
        # Throw 429 if the limit is exceeded.
        if not limit_result.allowed:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Return the limit result if it's allowed.
        return limit_result
    
    @classmethod
    async def record_usage(cls, plan: UsagePlan, model_id: str, usage_record: UsageRecord) -> bool:
        '''
        Record usage after the response is returned. We're awaiting this because it's 
        pretty fast, but if milliseconds matter, you can do this async.
        '''
        in_tokens: int = usage_record.input_tokens
        out_tokens: int = usage_record.output_tokens
        return await RateLimiter.record_usage(plan, model_id, in_tokens, out_tokens)
    
    @classmethod
    async def update_usage_record(cls, usage_record: UsageRecord) -> bool:
        '''
        Update the usage record for the given key and model.
        We're also awaiting the response here because it's pretty fast, but if milliseconds matter,
        you can do this async as well. This is a bit slower than the REDIS call.
        '''
        return await UsageClient.record_usage(usage_record)

        