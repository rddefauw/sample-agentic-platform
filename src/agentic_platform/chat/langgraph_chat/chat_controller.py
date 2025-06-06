from typing import Dict, Any
import uuid
import re

from agentic_platform.core.models.memory_models import Message
from agentic_platform.core.models.prompt_models import BasePrompt
from agentic_platform.core.models.api_models import ChatRequest, ChatResponse

from agentic_platform.chat.langgraph_chat.chat_workflow import LangGraphChat
from agentic_platform.chat.langgraph_chat.chat_prompt import ChatPrompt

# Instantiate the chat service so we don't recreate the graph on each request.
chat_service = LangGraphChat()

class ChatController:

    @classmethod
    def extract_response(cls, text: str) -> str:
        response_match = re.search(r'<response>(.*?)</response>', text, re.DOTALL)
        return response_match.group(1).strip() if response_match else "I'm sorry, something went wrong. Please try again."

    @classmethod
    def chat(cls, request: ChatRequest) -> ChatResponse:
        """
        Chat with the LangGraph chat agent. 
        
        The goal of this function is to abstract away the LangGraph specifics from the rest of the system.
        This is important to provide "2-way" compatibility between different frameworks.
        """
        # TODO: Implement memory retrieval.
        # message_history = MessageHistory(messages=[])

        # Convert the variables to a dictionary for the prompt to insert.
        inputs: Dict[str, Any] = {
            "chat_history": '',
            "message": request.text
        }

        # Create a Chat prompt object from the inputs.
        prompt: BasePrompt = ChatPrompt(inputs=inputs)

        # Run the chat service and get back a message object.
        response: Message = chat_service.run(prompt)

        # TODO: Append to the message history.
        
        # Return the chat response object to the server.
        return ChatResponse(
            text=cls.extract_response(response.text),
            conversationId=request.conversationId if request.conversationId else str(uuid.uuid4())
        )