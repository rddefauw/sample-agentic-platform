from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Literal, Union
from enum import Enum
from uuid import uuid4
from datetime import datetime
from agentic_platform.core.models.memory_models import (
    BaseContent, TextContent, ImageContent, AudioContent, JsonContent,
    ToolCall, ToolResult, Message
)
from agentic_platform.core.models.prompt_models import BasePrompt
import json
from fastapi import Response, status

class StreamEventType(str, Enum):
    """Types of events that can be streamed"""
    TEXT_DELTA = "text_delta"       # A chunk of text content
    TEXT_DONE = "text_done"         # Text content is complete
    THINKING = "thinking"           # Agent's internal reasoning
    TOOL_CALL = "tool_call"         # Tool being called
    TOOL_RESULT = "tool_result"     # Result from tool
    ERROR = "error"                 # Error occurred
    DONE = "done"                   # Stream complete

class BaseStreamEvent(BaseModel):
    """Base class for stream events"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TextDeltaEvent(BaseStreamEvent):
    """Event containing a chunk of text"""
    type: Literal[StreamEventType.TEXT_DELTA] = StreamEventType.TEXT_DELTA
    text: str  # The text chunk

class TextDoneEvent(BaseStreamEvent):
    """Event signaling text content is complete"""
    type: Literal[StreamEventType.TEXT_DONE] = StreamEventType.TEXT_DONE
    text: str  # The complete text

class ThinkingEvent(BaseStreamEvent):
    """Event containing agent's thinking process"""
    type: Literal[StreamEventType.THINKING] = StreamEventType.THINKING
    thinking: str

class ToolCallEvent(BaseStreamEvent):
    """Event containing a tool call"""
    type: Literal[StreamEventType.TOOL_CALL] = StreamEventType.TOOL_CALL
    tool_call: ToolCall  # Reuse our ToolCall type

class ToolResultEvent(BaseStreamEvent):
    """Event containing a tool result"""
    type: Literal[StreamEventType.TOOL_RESULT] = StreamEventType.TOOL_RESULT
    tool_result: ToolResult  # Reuse our ToolResult type

class ErrorEvent(BaseStreamEvent):
    """Event containing an error"""
    type: Literal[StreamEventType.ERROR] = StreamEventType.ERROR
    error: str

class DoneEvent(BaseStreamEvent):
    """Event signaling stream completion"""
    type: Literal[StreamEventType.DONE] = StreamEventType.DONE

# Union type for all possible events
StreamEvent = Union[
    TextDeltaEvent,
    TextDoneEvent,
    ThinkingEvent,
    ToolCallEvent,
    ToolResultEvent,
    ErrorEvent,
    DoneEvent
]
    
    