from typing import List, Callable
from pydantic import BaseModel

from agentic_platform.core.models.api_models import AgentRequest, AgentResponse
from agentic_platform.core.models.memory_models import Message
from agentic_platform.core.models.prompt_models import BasePrompt
from agentic_platform.core.models.llm_models import LLMRequest, LLMResponse
from agentic_platform.core.models.tool_models import ToolSpec
from agentic_platform.core.client.memory_gateway.memory_gateway_client import MemoryGatewayClient
from agentic_platform.core.models.memory_models import SessionContext, Message, ToolResult
from agentic_platform.core.client.llm_gateway.llm_gateway_client import LLMGatewayClient
from agentic_platform.agent.diy_agent.diy_agent_prompt import DIYAgentPrompt
from agentic_platform.core.decorator.toolspec_decorator import tool_spec

from agentic_platform.core.models.memory_models import (
    UpsertSessionContextRequest, 
    GetSessionContextRequest
)

memory_client = MemoryGatewayClient()

class DIYAgent:
    # This is new, we're adding tools in the constructor to bind them to the agent.
    # Don't get too attached to this idea, it'll change as we get into MCP.
    def __init__(self, tools: List[Callable]):
        self.tools: List[ToolSpec] = [tool_spec(t) for t in tools]
        self.conversation: SessionContext = SessionContext()
        self.prompt: BasePrompt = DIYAgentPrompt()

    def call_llm(self) -> LLMResponse:
        # Create LLM request
        request: LLMRequest = LLMRequest(
            system_prompt=self.prompt.system_prompt,
            messages=self.conversation.get_messages(),
            model_id=self.prompt.model_id,
            hyperparams=self.prompt.hyperparams,
            tools=self.tools
        )

        # Call the LLM.
        response: LLMResponse = LLMGatewayClient.chat_invoke(request)
        # Append the llms response to the conversation.
        self.conversation.add_message(Message(
            role="assistant",
            text=response.text,
            tool_calls=response.tool_calls
        ))
        # Return the response.
        return response
    
    def execute_tools(self, llm_response: LLMResponse) -> List[ToolResult]:
        """Call tools and return the results."""
        # It's possible that the model will call multiple tools.
        tool_results: List[ToolResult] = []
        # Iterate over the tool calls and call the tool.
        for tool_invocation in llm_response.tool_calls:
            # Get the tool spec for the tool call.
            tool: ToolSpec = next((t for t in self.tools if t.name == tool_invocation.name), None)
            # Call the tool.
            input_data: BaseModel = tool.model.model_validate(tool_invocation.arguments)
            tool_response: ToolResult = tool.function(input_data)
            # Add the tool use id to the tool result.
            tool_response.id = tool_invocation.id
            # Add the tool result to the list.
            tool_results.append(tool_response)

        # Add the tool results to the conversation
        message: Message = Message(role="user", tool_results=tool_results)
        self.conversation.add_message(message)
        
        # Return the tool results even though we don't use it.
        return tool_results
    
    def invoke(self, request: AgentRequest) -> AgentResponse:
        # Get prompt from request
        prompt: BasePrompt = self.prompt.format(inputs={"user_message": request.message})
        # Get or create conversation
        if request.conversationId:
            request = GetSessionContextRequest(session_id=request.session_id)
            self.conversation = memory_client.get_session_context(request).results[0]
        else:
            self.conversation = SessionContext(session_id=request.session_id)

        # Add user message to conversation
        self.conversation.add_message(Message(role="user", text=request.text))

        # Keep calling LLM until we get a final response
        while True:
            # Call the LLM
            response: LLMResponse = self.call_llm()
            
            # If the model wants to use tools
            if response.stop_reason == "tool_use":
                # Execute the tools
                self.execute_tools(response)
                # Continue the loop to get final response
                continue
            
            # If we get here, it's a final response         
            break

        # Save updated conversation
        memory_client.upsert_session_context(UpsertSessionContextRequest(
            session_context=self.conversation
        ))

        # Return our own type.
        return AgentResponse(
            response=response.text,
            conversation_id=self.conversation.session_id
        )