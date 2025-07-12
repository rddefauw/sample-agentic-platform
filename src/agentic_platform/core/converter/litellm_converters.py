import json
from typing import Dict, Any, List
from agentic_platform.core.models.llm_models import LLMResponse, LLMRequest, Usage
from agentic_platform.core.models.memory_models import Message, ToolCall, TextContent

class LiteLLMRequestConverter:
    """Converts internal LLMRequest to LiteLLM API format"""
    
    @staticmethod
    def convert_message(message: Message) -> Dict[str, Any]:
        """Convert an internal Message to LiteLLM format"""
        litellm_message = {
            "role": message.role,
        }
        
        # Add content if present
        if message.text:
            litellm_message["content"] = message.text
        
        # Add tool calls if present
        if message.tool_calls:
            litellm_message["tool_calls"] = [
                {
                    "id": tool_call.id or f"call_{i}",
                    "type": "function",
                    "function": {
                        "name": tool_call.name,
                        "arguments": json.dumps(tool_call.arguments)
                    }
                }
                for i, tool_call in enumerate(message.tool_calls)
            ]
        
        # Add tool results if present
        if message.tool_results:
            # Tool results are typically added as assistant messages in LiteLLM
            # This is a simplification - may need to be adjusted based on actual LiteLLM API behavior
            for i, tool_result in enumerate(message.tool_results):
                if tool_result.content:
                    for content in tool_result.content:
                        if content.type == "text":
                            litellm_message["content"] = content.text
                        # Handle other content types if needed
        
        return litellm_message
    
    @staticmethod
    def convert_messages(messages: List[Message]) -> List[Dict[str, Any]]:
        """Convert a list of internal Messages to LiteLLM format"""
        return [LiteLLMRequestConverter.convert_message(msg) for msg in messages]
    
    @staticmethod
    def convert_tools(tools: List[Any]) -> List[Dict[str, Any]]:
        """Convert internal tool specs to LiteLLM format"""
        litellm_tools = []
        
        for tool in tools:
            schema = tool.model.model_json_schema()
            
            litellm_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": schema
                }
            })
        
        return litellm_tools
    
    @staticmethod
    def convert_llm_request(request: LLMRequest) -> Dict[str, Any]:
        """Convert an internal LLMRequest to LiteLLM API format"""
        # Start with system message
        litellm_messages = [{"role": "system", "content": request.system_prompt}]
        
        # Add user and assistant messages
        litellm_messages.extend(LiteLLMRequestConverter.convert_messages(request.messages))
        
        # Build the request payload
        payload = {
            "model": request.model_id,
            "messages": litellm_messages,
            **request.hyperparams  # Add any additional parameters
        }
        
        # Add tools if present
        if request.tools:
            payload["tools"] = LiteLLMRequestConverter.convert_tools(request.tools)
            
            # Add tool_choice if force_tool is specified
            if request.force_tool:
                payload["tool_choice"] = {
                    "type": "function",
                    "function": {"name": request.force_tool}
                }
        
        return payload

class LiteLLMResponseConverter:
    """Converts LiteLLM API responses to internal format"""
    
    @staticmethod
    def to_llm_response(litellm_response: Dict[str, Any]) -> LLMResponse:
        """Convert a LiteLLM API response to internal LLMResponse format"""
        # Extract the assistant's message
        choices = litellm_response.get("choices", [])
        if not choices:
            return LLMResponse(raw_response=litellm_response)
        
        choice = choices[0]
        message = choice.get("message", {})
        content = message.get("content", "")
        
        # Extract tool calls if present
        tool_calls = []
        if message and "tool_calls" in message and message["tool_calls"]:
            for tool_call in message["tool_calls"]:
                if tool_call.get("type") == "function":
                    function = tool_call.get("function", {})
                    try:
                        arguments = json.loads(function.get("arguments", "{}"))
                    except json.JSONDecodeError:
                        arguments = {}
                    
                    tool_calls.append(ToolCall(
                        id=tool_call.get("id", ""),
                        name=function.get("name", ""),
                        arguments=arguments
                    ))
        
        # Create usage object
        usage_data = litellm_response.get("usage", {})
        usage = Usage(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0)
        )
        
        # Create output messages
        output = []
        if content:
            output.append(Message(
                role="assistant",
                content=[TextContent(type="text", text=content)]
            ))
        
        return LLMResponse(
            id=litellm_response.get("id", ""),
            text=content,
            stop_reason=choice.get("finish_reason"),
            tool_calls=tool_calls,
            usage=usage,
            output=output,
            raw_response=litellm_response
        )