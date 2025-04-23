from agentic_platform.core.models.memory_models import (
    GetSessionContextRequest,
    GetSessionContextResponse,
    UpsertSessionContextRequest,
    UpsertSessionContextResponse,
    GetMemoriesRequest,
    GetMemoriesResponse,
    CreateMemoryRequest,
    CreateMemoryResponse
)

from agentic_platform.service.memory_gateway.client.memory.pg_memory_client import PGMemoryClient
class MemoryClient:

    @classmethod
    def get_session_context(cls, request: GetSessionContextRequest) -> GetSessionContextResponse:
        return PGMemoryClient.get_session_context(request)
    
    @classmethod
    def upsert_session_context(cls, request: UpsertSessionContextRequest) -> UpsertSessionContextResponse:
        return PGMemoryClient.upsert_session_context(request)
    
    @classmethod
    def get_memories(cls, request: GetMemoriesRequest) -> GetMemoriesResponse:
        return PGMemoryClient.get_memories(request)
    
    @classmethod
    def create_memory(cls, request: CreateMemoryRequest) -> CreateMemoryResponse:
        return PGMemoryClient.create_memory(request)
