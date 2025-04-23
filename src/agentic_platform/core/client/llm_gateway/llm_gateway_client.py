
from agentic_platform.core.models.llm_models import LLMRequest, LLMResponse
from agentic_platform.core.models.embedding_models import EmbedRequest, EmbedResponse
from agentic_platform.core.client.llm_gateway.bedrock_gateway_client import BedrockGatewayClient


br_client = BedrockGatewayClient()


class LLMGatewayClient:
    '''Placeholder class for wherever you want to send your requests.'''
    @staticmethod
    def chat_invoke(request: LLMRequest) -> LLMResponse:
        return br_client.chat_invoke(request=request)
    
    @staticmethod
    def embed_invoke(request: EmbedRequest) -> EmbedResponse:
        return br_client.embed_invoke(request=request)
    
    def get_bedrock_client():
        return br_client.get_client()
