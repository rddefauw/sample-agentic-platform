from typing import List, Callable
from agentic_platform.core.models.api_models import AgenticRequest, AgenticResponse
from agentic_platform.core.models.memory_models import Message, TextContent
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
    
    async def invoke(self, request: AgenticRequest) -> AgenticResponse:
        # Get or create conversation
        if request.session_id:
            sess_request = GetSessionContextRequest(session_id=request.session_id)
            session_results = memory_client.get_session_context(sess_request).results
            if session_results:
                self.conversation = session_results[0]
            else:
                self.conversation = SessionContext(session_id=request.session_id)
        else:
            self.conversation = SessionContext(session_id=request.session_id)

        # Add the message from request to conversation
        self.conversation.add_message(request.message)
        
        # Get the user message text for PydanticAI
        latest_user_text = request.user_text
        if not latest_user_text:
            raise ValueError("No user message found in request")

        # Convert to pydanticai messages and run
        response: ModelResponse = await self.agent.run(latest_user_text)
        
        # Convert response messages to our format
        converted_messages: List[Message] = PydanticAIMessageConverter.convert_messages(response.all_messages())
        
        # Add only the new assistant messages to conversation (filter out the user message we just added)
        assistant_messages = [msg for msg in converted_messages if msg.role == "assistant"]
        self.conversation.add_messages(assistant_messages)
        
        # Save updated conversation
        memory_client.upsert_session_context(UpsertSessionContextRequest(
            session_context=self.conversation
        ))

        # Return the last assistant message as response
        last_assistant_message = assistant_messages[-1] if assistant_messages else Message(
            role="assistant",
            content=[TextContent(type="text", text="No response generated")]
        )

        # Return the response using new format
        return AgenticResponse(
            session_id=self.conversation.session_id,
            message=last_assistant_message,
            metadata={"model": "anthropic.claude-3-sonnet-20240229-v1:0"}
        )
