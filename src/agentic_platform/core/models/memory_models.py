from typing import Dict, Any, Optional, List, Literal, Union
from pydantic import BaseModel, Field, field_validator
from uuid import uuid4
from datetime import datetime

##############################################################################
# Define a ToolCall type. This follows the MCP Tool specs params.
# Doing this allows us to easily extend ToolCall objects to fully support MCP.
# with a simple decorator to add method, jsonrpc, and id.
##############################################################################

class ToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any]
    id: Optional[str] = None

##########################################################################
# MCP is standardizing the way we return results however it's incomplete. 
# Bedrock for example has video and json results as well.
# However bedrock has text, json, document, image, and video. 
# We'll intentionally leave it open ended for now until MCP is updated.
##########################################################################

class BaseContent(BaseModel):
    type: Literal["text", "image", "audio", "json"]

class TextContent(BaseContent):
    type: Literal["text"] = "text"
    text: str

class ImageContent(BaseContent):
    type: Literal["image"] = "image"
    data: str  # base64-encoded data
    mimeType: str  # e.g., "image/png"

class AudioContent(BaseContent):
    type: Literal["audio"] = "audio"
    data: str  # base64-encoded audio data
    mimeType: str  # e.g., "audio/wav"

# This is not a part of MCP, but it's supported by Bedrock making ours a superset of MCP.
class JsonContent(BaseContent):
    type: Literal["json"] = "json"
    content: Dict[str, Any]

# With this approach we're able to support a superset of MCP and Bedrock message types.
class ToolResult(BaseModel):
    """A tool result"""
    # ToolUse Id is optional and can be added post instantiation by the calling agent.
    id: Optional[str] = None
    content: List[BaseContent]
    isError: bool = False

    @classmethod
    def to_content(cls, value: Any) -> List[BaseContent]:
        """Convert any Python value to properly typed content items"""
        # Handle None
        if value is None:
            return []
            
        # Already a content item
        if isinstance(value, BaseContent):
            return [value]
            
        # String -> TextContent
        if isinstance(value, str):
            return [TextContent(type="text", text=value)]
            
        # Dict -> JsonContent
        if isinstance(value, dict):
            return [JsonContent(type="json", content=value)]
            
        # List -> Process each item and flatten
        if isinstance(value, (list, tuple)):
            result = []
            for item in value:
                result.extend(cls.to_content(item))
            return result
            
        # Other types -> Try JSON, fall back to string
        try:
            # If it's a simple type like int, float, bool
            if isinstance(value, (int, float, bool)):
                return [TextContent(type="text", text=str(value))]
                
            # For other objects, try JSON
            import json
            return [JsonContent(type="json", content=value)]
        except:
            return [TextContent(type="text", text=str(value))]

class MediaInfo(BaseModel):
    """Container for media data and metadata"""
    data: str
    mime_type: str = "application/octet-stream"

class Message(BaseModel):
    """A message in the conversation"""
    role: Literal["user", "assistant"]
    text: Optional[str] = None
    # Store complete media info in single fields
    image: Optional[MediaInfo] = None
    audio: Optional[MediaInfo] = None
    json: Optional[Dict[str, Any]] = None
    tool_calls: List[ToolCall] = Field(default_factory=list)
    tool_results: List[ToolResult] = Field(default_factory=list)
    # For forward compatibility with where the industry is heading
    content: Optional[List[BaseContent]] = None
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())

    @property
    def timestamp_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.timestamp)
    
    # This is how we syncronize the fields with the content.
    def model_post_init(self, __context: Any) -> None:
        """Called after the model is fully initialized"""
        # Initialize content if it's None
        if self.content is None:
            self.content = []
            
        # Sync from fields to content
        if self.text:
            text_content = TextContent(type="text", text=self.text)
            self.content.append(text_content)
            
        if self.image:
            self.content.append(ImageContent(
                type="image",
                data=self.image.data,
                mimeType=self.image.mime_type
            ))
            
        if self.audio:
            self.content.append(AudioContent(
                type="audio",
                data=self.audio.data,
                mimeType=self.audio.mime_type
            ))
            
        if self.json:
            self.content.append(JsonContent(type="json", content=self.json))
        
        # If no fields but content is provided, sync from content to fields
        elif self.content:
            for item in self.content:
                if isinstance(item, TextContent) and not self.text:
                    self.text = item.text
                elif isinstance(item, ImageContent) and not self.image:
                    self.image = MediaInfo(data=item.data, mime_type=item.mimeType)
                elif isinstance(item, AudioContent) and not self.audio:
                    self.audio = MediaInfo(data=item.data, mime_type=item.mimeType)
                elif isinstance(item, JsonContent) and not self.json:
                    self.json = item.content

class SessionContext(BaseModel):
    """Represents a single conversation"""
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    messages: List[Message] = Field(default_factory=list)
    system_prompt: Optional[str] = None
    # You can pass graph checkpoints here.
    session_metadata: Optional[Dict[str, Any]] = None
    
    def add_message(self, message: Message) -> None:
        self.messages.append(message)

    def add_messages(self, messages: List[Message]) -> None:
        self.messages.extend(messages)

    def get_messages(self) -> List[Message]:
        """Get messages"""
        return self.messages
    
    def add_metadata(self, metadata: Dict[str, Any]) -> None:
        self.session_metadata = metadata

class Memory(BaseModel):
    memory_id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str
    user_id: str
    agent_id: str
    content: str
    embedding_model: str
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: datetime = Field(default_factory=lambda: datetime.now())
    embedding: Optional[List[float]] = None
    similarity: float = -1.0
    

class GetSessionContextRequest(BaseModel):
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class GetSessionContextResponse(BaseModel):
    results: List[SessionContext]

class UpsertSessionContextRequest(BaseModel):
    session_context: SessionContext
    
class UpsertSessionContextResponse(BaseModel):
    session_context: SessionContext
    
class GetMemoriesRequest(BaseModel):
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    embedding: Optional[List[float]] = None
    limit: int = 2

    # Add validation so you can't get memories of an agent without session or user
    @field_validator("agent_id")
    @classmethod
    def validate_agent_id(cls, v, info):
        data = info.data
        if not data.get("session_id") and not data.get("user_id"):
            raise ValueError("Either session_id or user_id must be provided")
        return v

class GetMemoriesResponse(BaseModel):
    memories: List[Memory]
    
class CreateMemoryRequest(BaseModel):
    session_id: str
    user_id: str
    agent_id: str
    session_context: SessionContext
    
class CreateMemoryResponse(BaseModel):
    memory: Memory
