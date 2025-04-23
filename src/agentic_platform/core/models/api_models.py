from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from agentic_platform.core.models.agent_models import TraceEvent, StreamChunk
from agentic_platform.core.models.vectordb_models import VectorSearchRequest, VectorSearchResponse

class ChatRequest(BaseModel):
    message: str
    conversationId: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
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
    traces: Optional[List[TraceEvent]] = None

class AgentResponseStream(AgentResponse):
    """Response model for agent tasks"""
    conversationId: str
    chunk: StreamChunk

class SearchWorkflowRequest(BaseModel):
    """Request model for search workflow"""
    query: str

class SearchWorkflowResponse(BaseModel):
    """Response model for search workflow"""
    response: str
    conversationId: str
    traces: Optional[List[TraceEvent]] = None

class RetrieveRequest(BaseModel):
    """
    Request model for retrieve using vector search.

    Leaving space for other types of retrieval queries.
    
    """
    vectorsearch_request: VectorSearchRequest

class RetrieveResponse(BaseModel):
    """
    Response model for retrieve

    Leaving space for other types of retrieval queries.
    """
    vectorsearch_results: VectorSearchResponse



