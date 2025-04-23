from typing import List, Callable
from agentic_platform.core.models.api_models import AgentRequest, AgentResponse
from agentic_platform.core.models.memory_models import Message
from agentic_platform.core.models.prompt_models import BasePrompt
from agentic_platform.core.client.memory_gateway.memory_gateway_client import MemoryGatewayClient
from agentic_platform.core.models.memory_models import SessionContext, Message
from agentic_platform.core.converter.pydanticai_converters import PydanticAIMessageConverter
from agentic_platform.core.client.llm_gateway.llm_gateway_client import LLMGatewayClient
from pydantic_ai import Agent
from pydantic_ai.providers.bedrock import BedrockProvider
from pydantic_ai.models.bedrock import BedrockConverseModel
from pydantic_ai.models import ModelResponse
from agentic_platform.core.models.memory_models import (
    UpsertSessionContextRequest, 
    GetSessionContextRequest
)

memory_client = MemoryGatewayClient()

class PyAIAgent:
    # This is new, we're adding tools in the constructor to bind them to the agent.
    # Don't get too attached to this idea, it'll change as we get into MCP.
    def __init__(self, tools: List[Callable]):
        # This is the identifier for PydanticAI calling Bedrock.
        self.conversation: SessionContext = SessionContext()

        # Get our bedrock client that's configured to use the proxy.
        client = LLMGatewayClient.get_bedrock_client()

        # Point pydanticai to our gateway.
        model: BedrockConverseModel = BedrockConverseModel(
            model_name="anthropic.claude-3-sonnet-20240229-v1:0",
            provider=BedrockProvider(bedrock_client=client)
        )
        self.agent: Agent = Agent(
            model=model,
            system_prompt='You are a helpful assistant.',
        )

        # Add our tools to the agent.
        [self.agent.tool_plain(func)for func in tools]
    
    async def invoke(self, request: AgentRequest) -> AgentResponse:
        # Get or create conversation
        if request.session_id:
            sess_request = GetSessionContextRequest(session_id=request.session_id)
            self.conversation = memory_client.get_session_context(sess_request).results[0]
        else:
            self.conversation = SessionContext()

        # Add user message to conversation
        self.conversation.add_message(Message(role="user", text=request.text))
        # Convert to langchain messages
        response: ModelResponse = await self.agent.run(request.text)
        # Convert to our response format
        messages: List[Message] = PydanticAIMessageConverter.convert_messages(response.all_messages())
        self.conversation.add_messages(messages)
        memory_client.upsert_session_context(UpsertSessionContextRequest(
            session_context=self.conversation
        ))

        # Return the response
        return AgentResponse(
            session_id=self.conversation.session_id,
            message=messages[-1].text
        )