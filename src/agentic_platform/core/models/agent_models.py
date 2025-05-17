from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Literal, AsyncGenerator, Union
from enum import Enum
from uuid import uuid4
from agentic_platform.core.models.memory_models import Message, ToolCall, ToolResult
from agentic_platform.core.models.prompt_models import BasePrompt
import json
from fastapi import Response, status
from sse_starlette.sse import EventSourceResponse

class ChunkType(str, Enum):
    """Types of chunks in the agent stream"""
    CONTENT = "content"     # Regular content from the agent
    TRACE = "trace"         # Trace of tool/agent activity
    THINKING = "thinking"   # Agent's internal reasoning
    COMPLETE = "complete"   # Final completion signal

class ToolState(str, Enum):
    """States a tool can be in"""
    STARTED = "started"     # Tool has started execution
    RUNNING = "running"     # Tool is running, may have intermediate output
    COMPLETED = "completed" # Tool has completed successfully
    ERROR = "error"         # Tool encountered an error

class TraceEvent(BaseModel):
    """Details about a tool trace event"""
    name: str                               # Name of the tool
    state: ToolState                        # Current state of the tool
    id: str = Field(default_factory=lambda: str(uuid4()))  # Unique ID for this tool
    input: Optional[Dict[str, Any]] = None  # Input parameters
    output: Optional[Any] = None            # Output (partial or complete)
    error: Optional[str] = None             # Error message if applicable

class StreamChunk(BaseModel):
    """Unified chunk object for agent streaming"""
    # Core fields
    type: ChunkType
    
    # Content - applicable to any chunk type
    content: Optional[str] = None
    
    # Trace-specific fields (when type is TRACE)
    trace: Optional[TraceEvent] = None
    
    # Completion metadata (for COMPLETE chunks)
    message_id: Optional[str] = None
    citations: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        validate_assignment = True

class AgentInvokeRequest(BaseModel):
    """Request model for agent invocation"""
    prompt: BasePrompt
    conversation_id: Optional[str] = None
    include_traces: Optional[bool] = False
    
class AgentInvokeResponse(BaseModel):
    """Response model for agent invocation"""
    message: Message
    conversation_id: str
    traces: Optional[List[TraceEvent]] = None
    
class AgentResponse(BaseModel):
    """Complete, non-streaming response from an agent"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    conversation_id: str
    message: Message  # The main content message
    tool_calls: List[ToolCall] = Field(default_factory=list)  # Tools that were called
    tool_results: List[ToolResult] = Field(default_factory=list)  # Results from tools
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @property
    def text(self) -> Optional[str]:
        """Get the text content from the message"""
        return self.message.text
    
    @classmethod
    def from_text(cls, text: str, role: str, conversation_id: str, **kwargs) -> "AgentResponse":
        """Create a simple text response"""
        return cls(
            conversation_id=conversation_id,
            message=Message.from_text(role=role, text=text),
            **kwargs
        )

# Event-specific payload models
class TextEventPayload(BaseModel):
    """Payload for text events"""
    text: str

class ThinkingEventPayload(BaseModel):
    """Payload for thinking events"""
    text: str

class ToolCallEventPayload(BaseModel):
    """Payload for tool call events"""
    tool_call: ToolCall

class ToolResultEventPayload(BaseModel):
    """Payload for tool result events"""
    tool_result: ToolResult

class ErrorEventPayload(BaseModel):
    """Payload for error events"""
    error: str
    
class DoneEventPayload(BaseModel):
    """Payload for done events"""
    # Can include summary data if needed
    pass

# Event type enum
class StreamEventType(str, Enum):
    """Types of events that can be streamed"""
    TEXT = "text"
    THINKING = "thinking"  
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    ERROR = "error"
    DONE = "done"

# Clean union-based stream event
class AgentStreamEvent(BaseModel):
    """A single streamable event from an agent"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    conversation_id: str
    event_type: StreamEventType
    
    # The event payload, dependent on event_type
    payload: Union[
        TextEventPayload,
        ThinkingEventPayload,
        ToolCallEventPayload, 
        ToolResultEventPayload,
        ErrorEventPayload,
        DoneEventPayload
    ]
    
    # Optional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Factory methods for creating events
    @classmethod
    def text_event(cls, text: str, conversation_id: str, **kwargs) -> "AgentStreamEvent":
        """Create a text event"""
        return cls(
            conversation_id=conversation_id,
            event_type=StreamEventType.TEXT,
            payload=TextEventPayload(text=text),
            **kwargs
        )
    
    @classmethod
    def thinking_event(cls, text: str, conversation_id: str, **kwargs) -> "AgentStreamEvent":
        """Create a thinking event"""
        return cls(
            conversation_id=conversation_id,
            event_type=StreamEventType.THINKING,
            payload=ThinkingEventPayload(text=text),
            **kwargs
        )
    
    @classmethod
    def tool_call_event(cls, tool_call: ToolCall, conversation_id: str, **kwargs) -> "AgentStreamEvent":
        """Create a tool call event"""
        return cls(
            conversation_id=conversation_id,
            event_type=StreamEventType.TOOL_CALL,
            payload=ToolCallEventPayload(tool_call=tool_call),
            **kwargs
        )
    
    @classmethod
    def tool_result_event(cls, tool_result: ToolResult, conversation_id: str, **kwargs) -> "AgentStreamEvent":
        """Create a tool result event"""
        return cls(
            conversation_id=conversation_id,
            event_type=StreamEventType.TOOL_RESULT,
            payload=ToolResultEventPayload(tool_result=tool_result),
            **kwargs
        )
    
    @classmethod
    def error_event(cls, error: str, conversation_id: str, **kwargs) -> "AgentStreamEvent":
        """Create an error event"""
        return cls(
            conversation_id=conversation_id,
            event_type=StreamEventType.ERROR,
            payload=ErrorEventPayload(error=error),
            **kwargs
        )
    
    @classmethod
    def done_event(cls, conversation_id: str, **kwargs) -> "AgentStreamEvent":
        """Create a done event"""
        return cls(
            conversation_id=conversation_id,
            event_type=StreamEventType.DONE,
            payload=DoneEventPayload(),
            **kwargs
        )

# Example FastAPI endpoint
async def stream_agent_response(conversation_id: str):
    async def event_generator():
        # This would be your actual agent logic
        yield AgentStreamEvent.text_event("Hello, I'm", conversation_id).model_dump_json()
        yield AgentStreamEvent.text_event("Hello, I'm thinking about", conversation_id).model_dump_json()
        yield AgentStreamEvent.thinking_event("Let me search for information", conversation_id).model_dump_json()
        
        # Example tool call
        tool_call = ToolCall(name="search", arguments={"query": "weather"})
        yield AgentStreamEvent.tool_call_event(tool_call, conversation_id).model_dump_json()
        
        # Example tool result
        tool_result = ToolResult(id=tool_call.id, content=[{"type": "text", "text": "It's sunny"}], isError=False)
        yield AgentStreamEvent.tool_result_event(tool_result, conversation_id).model_dump_json()
        
        yield AgentStreamEvent.text_event("Hello, I'm thinking about the weather. It's sunny today!", conversation_id).model_dump_json()
        yield AgentStreamEvent.done_event(conversation_id).model_dump_json()

    return EventSourceResponse(event_generator())

# FastAPI route example:
# @app.get("/agent/stream/{conversation_id}")
# async def stream_agent(conversation_id: str):
#     return stream_agent_response(conversation_id)
    
    