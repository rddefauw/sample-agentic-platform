from typing import Dict, List, Any

from pydantic_ai.messages import ModelMessage
from pydantic_core import to_jsonable_python

from agentic_platform.core.models.memory_models import Message, ToolCall, ToolResult

from typing import Dict, List, Any

from pydantic_ai.messages import ModelMessage
from pydantic_core import to_jsonable_python

from agentic_platform.core.models.memory_models import Message, ToolCall, ToolResult

class PydanticAIMessageConverter:

    @classmethod
    def convert_tool_call(cls, tool_call: Dict[str, Any]) -> ToolCall:
        return ToolCall(
            name=tool_call['tool_name'],
            arguments=tool_call['args'],
            id=tool_call['tool_call_id']
        )

    @classmethod
    def convert_tool_result(cls, tool_result: Dict[str, Any]) -> ToolResult:
        return ToolResult(
            id=tool_result['tool_call_id'],
            content=ToolResult.to_content(tool_result['content']),
            isError=False
        )

    @classmethod
    def convert_text(cls, text: Dict[str, Any]) -> str:
        return text['content']

    @classmethod
    def convert_message(cls, message: Dict[str, Any]) -> Message:
        # Create a dictionary to store the message parts.
        message_dict: Dict[str, Any] = {}

        # PydanticAI kind field is either request/response. It does not have a specific tool field like LangChain.
        role: str = 'user' if message['kind'] == 'request' else 'assistant'

        message_dict['role'] = role

        # For each part handle the type appropriately.
        for part in message['parts']:
            # Grab the part kind.
            part_kind: str = part['part_kind']

            # Handle the type appropriately.
            if part_kind == 'text' or part_kind == 'user-prompt':
                message_dict['text'] = cls.convert_text(part)

            elif part_kind == 'tool-call':
                tool_call: ToolCall = cls.convert_tool_call(part)
                message_dict.setdefault("tool_calls", []).append(tool_call)

            elif part_kind == 'tool-return':
                tool_result: ToolResult = cls.convert_tool_result(part)
                message_dict.setdefault("tool_results", []).append(tool_result)

        return Message(**message_dict)

    @classmethod
    def convert_messages(cls, messages: List[ModelMessage]) -> List[Message]:
        json_messages: List[Dict[str, Any]] = to_jsonable_python(messages)
        return [cls.convert_message(message) for message in json_messages]