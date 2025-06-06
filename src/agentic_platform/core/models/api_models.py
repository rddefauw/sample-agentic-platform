from pydantic import BaseModel
from typing import Optional, Dict, Any, List, Union
from agentic_platform.core.models.streaming_models import StreamEvent
from agentic_platform.core.models.vectordb_models import VectorSearchRequest, VectorSearchResponse
from agentic_platform.core.models.streaming_models import BaseStreamEvent

class ChatRequest(BaseModel):
    text: str
    conversationId: Optional[str] = None

class ChatResponse(BaseModel):
    text: str
    conversationId: str

class AgentRequest(BaseModel):
    """Request model for agent tasks"""
    text: str
    session_id: Optional[str] = None
    additionalInfo: Optional[Dict[str, Any]] = None
    includeTraces: Optional[bool] = False

class AgentRequestStream(AgentRequest):
    """Request model for agent tasks"""
    stream: bool = True

class AgentResponse(BaseModel):
    """Response model for agent tasks"""
    message: str
    session_id: str
    traces: Optional[List[StreamEvent]] = None


class SearchWorkflowRequest(BaseModel):
    """Request model for search workflow"""
    query: str

class SearchWorkflowResponse(BaseModel):
    """Response model for search workflow"""
    response: str
    conversationId: str
    traces: Optional[List[StreamEvent]] = None

class RetrieveRequest(BaseModel):
    """Request model for retrieve using vector search."""
    vectorsearch_request: VectorSearchRequest

class RetrieveResponse(BaseModel):
    """Response model for retrieve"""
    vectorsearch_results: VectorSearchResponse



