from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Literal
from enum import Enum
from uuid import uuid4
from agentic_platform.core.models.memory_models import Message
from agentic_platform.core.models.prompt_models import BasePrompt

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
    
    