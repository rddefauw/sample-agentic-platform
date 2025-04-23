from agentic_platform.service.llm_gateway.models.gateway_api_types import ConverseRequest, ConverseResponse
from typing import Dict, Any

import boto3

bedrock = boto3.client('bedrock-runtime')

class BedrockClient:
    
    @classmethod
    def converse(cls, request: ConverseRequest) -> ConverseResponse:
        # Call Bedrock
        kwargs: Dict[str, Any] = request.model_dump()
        return bedrock.converse(**kwargs)
