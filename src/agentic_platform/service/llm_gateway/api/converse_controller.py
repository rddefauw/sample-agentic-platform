from agentic_platform.service.llm_gateway.api.base_llm_controller import BaseLLMController
from agentic_platform.service.llm_gateway.models.gateway_api_types import ConverseRequest, ConverseResponse
from agentic_platform.service.llm_gateway.models.usage_types import UsageRecord, UsagePlan
from agentic_platform.service.llm_gateway.client.bedrock_client import BedrockClient


class ConverseController(BaseLLMController):

    @classmethod
    async def converse(cls, request: ConverseRequest, usage_plan: UsagePlan) -> ConverseResponse:
        '''
        This is a passthrough endpoint for the converse API.
        It's useful for frameworks that have integrated with Bedrock b/c they don't 
        expect our own types.
        '''
        # Get the rate limit result from our base class.
        # Get user message if available. If not we'll just skip it.
        try:
            user_message = request.messages[-1]['content'][0]['text']
        except:
            user_message = ''
            
        await cls.check_rate_limits(usage_plan, request.modelId, user_message)
        
        # if not, execute the converse passthrough.
        response: ConverseResponse = BedrockClient.converse(request)

        print(response)

        return response

        # Record the usage. We could do this async, but the models take seconds to return.
        # Shaving off milliseconds here is not a big deal.
    #     usage_record: UsageRecord = cls.get_usage_record(request, response, api_key)
    #     await cls.record_usage(api_key, request.modelId, usage_record)
    #     await cls.update_usage_record(usage_record)

    #     return response

    # @classmethod
    # def get_usage_record(cls, request: ConverseRequest, response: ConverseResponse, api_key: APIKey) -> UsageRecord:
    #     '''
    #     Convert the response to our usage record type.
    #     '''
    #     input_tokens: int = response['usage']['inputTokens']
    #     output_tokens: int = response['usage']['outputTokens']

    #     return UsageRecord(
    #         tenant_id=api_key.tenant_id,
    #         model=request.modelId,
    #         input_tokens=input_tokens,
    #         output_tokens=output_tokens
    #     )