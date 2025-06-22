import pytest
import json
from uuid import uuid4

from agentic_platform.core.models.api_models import (
    AgenticRequest, AgenticRequestStream, AgenticResponse,
    RetrieveRequest, RetrieveResponse
)
from agentic_platform.core.models.memory_models import (
    Message, TextContent, JsonContent, ImageContent, AudioContent, ToolCall, ToolResult
)
from agentic_platform.core.models.vectordb_models import VectorSearchRequest, VectorSearchResponse


class TestAgenticRequest:
    """Test AgenticRequest model functionality"""
    
    # Removed trivial default values test - just testing framework defaults
    
    def test_agent_request_from_text_convenience_method(self):
        """Test AgenticRequest.from_text convenience constructor"""
        request = AgenticRequest.from_text("Analyze this code", include_thinking=True)
        
        assert request.message.role == "user"
        assert request.message.text == "Analyze this code"
        assert request.include_thinking is True
        assert request.stream is False
    
    def test_agent_request_user_text_property(self):
        """Test user_text property returns user message text"""
        user_message = Message.from_text("user", "Latest user message")
        request = AgenticRequest(message=user_message)
        
        assert request.user_text == "Latest user message"
    
    def test_agent_request_user_text_no_user_message(self):
        """Test user_text returns None when message is not from user"""
        assistant_message = Message.from_text("assistant", "Only assistant message")
        request = AgenticRequest(message=assistant_message)
        
        assert request.user_text is None
    
    # Removed trivial constructor test - just testing field assignment


class TestAgenticRequestStream:
    """Test AgenticRequestStream model functionality"""
    
    # Removed trivial inheritance test - tests Python class inheritance, not business logic


class TestAgenticResponse:
    """Test AgenticResponse model functionality"""
    
    # Removed trivial constructor test - just testing field assignment
    
    # Removed trivial property test - just tests simple getter
    
    def test_agent_response_json_data_property(self):
        """Test AgenticResponse json_data property"""
        message = Message(
            role="assistant",
            content=[
                TextContent(text="Here's the data:"),
                JsonContent(content={"result": "success", "data": [1, 2, 3]}),
                JsonContent(content={"another": "object"})
            ]
        )
        response = AgenticResponse(message=message, session_id="test")
        
        json_data = response.json_data
        assert len(json_data) == 2
        assert json_data[0] == {"result": "success", "data": [1, 2, 3]}
        assert json_data[1] == {"another": "object"}
    
    def test_agent_response_json_data_empty_content(self):
        """Test json_data property with no content"""
        message = Message(role="assistant", content=None)
        response = AgenticResponse(message=message, session_id="test")
        
        assert response.json_data == []
    
    # Removed trivial property test - just returns message.tool_calls
    
    def test_agent_response_has_errors_property(self):
        """Test AgenticResponse has_errors property"""
        # Test with no errors
        tool_results = [
            ToolResult(content=[TextContent(text="Success")], isError=False)
        ]
        message = Message(role="assistant", tool_results=tool_results)
        response = AgenticResponse(message=message, session_id="test")
        
        assert response.has_errors is False
        
        # Test with errors
        tool_results_with_error = [
            ToolResult(content=[TextContent(text="Success")], isError=False),
            ToolResult(content=[TextContent(text="Error occurred")], isError=True)
        ]
        message_with_error = Message(role="assistant", tool_results=tool_results_with_error)
        response_with_error = AgenticResponse(message=message_with_error, session_id="test")
        
        assert response_with_error.has_errors is True
    
    def test_agent_response_with_metadata(self):
        """Test AgenticResponse with custom metadata"""
        message = Message.from_text("assistant", "Response")
        metadata = {"confidence": 0.95, "model": "gpt-4"}
        response = AgenticResponse(message=message, session_id="test", metadata=metadata)
        
        assert response.metadata == metadata


class TestRetrievalModels:
    """Test retrieval models"""
    
    def test_retrieve_request_creation(self):
        """Test RetrieveRequest creation"""
        vector_request = VectorSearchRequest(
            query="test query",
            limit=5
        )
        request = RetrieveRequest(vectorsearch_request=vector_request)
        
        assert request.vectorsearch_request == vector_request
    
    def test_retrieve_response_creation(self):
        """Test RetrieveResponse creation"""
        vector_response = VectorSearchResponse(
            results=[],
            total_count=0
        )
        response = RetrieveResponse(vectorsearch_results=vector_response)
        
        assert response.vectorsearch_results == vector_response



class TestSerialization:
    """Test serialization and deserialization"""
    
    def test_agent_request_serialization(self):
        """Test AgenticRequest serialization/deserialization"""
        original_request = AgenticRequest.from_text(
            "Test message",
            max_tokens=100,
            include_thinking=True,
            context={"key": "value"}
        )
        
        # Serialize to dict
        data = original_request.model_dump()
        
        # Deserialize back
        restored_request = AgenticRequest(**data)
        
        assert restored_request.message.text == original_request.message.text
        assert restored_request.max_tokens == original_request.max_tokens
        assert restored_request.include_thinking == original_request.include_thinking
        assert restored_request.context == original_request.context
    
    def test_agent_response_serialization(self):
        """Test AgenticResponse serialization/deserialization"""
        message = Message(
            role="assistant",
            content=[
                TextContent(text="Hello"),
                JsonContent(content={"data": "value"})
            ]
        )
        original_response = AgenticResponse(
            message=message,
            session_id="test-session",
            metadata={"confidence": 0.95}
        )
        
        # Serialize to dict
        data = original_response.model_dump()
        
        # Deserialize back
        restored_response = AgenticResponse(**data)
        
        assert restored_response.text == original_response.text
        assert restored_response.session_id == original_response.session_id
        assert restored_response.metadata == original_response.metadata
        assert len(restored_response.json_data) == 1
    
    def test_json_serialization_roundtrip(self):
        """Test full JSON serialization roundtrip"""
        request = AgenticRequest.from_text("Test message", include_thinking=True)
        
        # Convert to JSON string
        json_str = request.model_dump_json()
        
        # Parse back from JSON
        data = json.loads(json_str)
        restored_request = AgenticRequest(**data)
        
        assert restored_request.message.text == request.message.text
        assert restored_request.include_thinking == request.include_thinking
    
    def test_complex_agent_response_serialization(self):
        """Test serialization of complex AgenticResponse with tool calls and results"""
        tool_calls = [ToolCall(name="search", arguments={"query": "test"})]
        tool_results = [ToolResult(
            content=[TextContent(text="Search results")],
            isError=False
        )]
        
        message = Message(
            role="assistant",
            content=[TextContent(text="Here are the results:")],
            tool_calls=tool_calls,
            tool_results=tool_results
        )
        
        response = AgenticResponse(message=message, session_id="test")
        
        # Serialize and deserialize
        data = response.model_dump()
        restored = AgenticResponse(**data)
        
        assert len(restored.tool_calls) == 1
        assert restored.tool_calls[0].name == "search"
        assert restored.has_errors is False
        assert restored.text == "Here are the results:"


class TestCompleteSerialization:
    """Test complete serialization of all field types and discriminated unions"""
    
    def test_all_content_types_serialize_completely(self):
        """Test that all content types preserve all fields during serialization"""
        # Create message with all content types
        message = Message(
            role="assistant",
            content=[
                TextContent(type="text", text="This is text content"),
                ImageContent(
                    type="image", 
                    data="base64encodedimagedata", 
                    mimeType="image/png"
                ),
                AudioContent(
                    type="audio", 
                    data="base64encodedaudiodata", 
                    mimeType="audio/wav"
                ),
                JsonContent(
                    type="json", 
                    content={"nested": {"data": "value"}, "array": [1, 2, 3]}
                )
            ],
            tool_calls=[
                ToolCall(
                    name="search_tool", 
                    arguments={"query": "test", "limit": 10}, 
                    id="tool_call_123"
                )
            ],
            tool_results=[
                ToolResult(
                    id="tool_result_456",
                    content=[TextContent(type="text", text="Tool result")],
                    isError=False
                )
            ]
        )
        
        # Serialize and deserialize
        serialized = message.model_dump()
        restored = Message(**serialized)
        
        # Verify all content types preserved
        assert len(restored.content) == 4
        
        # Check TextContent
        text_content = restored.content[0]
        assert text_content.type == "text"
        assert text_content.text == "This is text content"
        
        # Check ImageContent
        image_content = restored.content[1]
        assert image_content.type == "image"
        assert image_content.data == "base64encodedimagedata"
        assert image_content.mimeType == "image/png"
        
        # Check AudioContent
        audio_content = restored.content[2]
        assert audio_content.type == "audio"
        assert audio_content.data == "base64encodedaudiodata"
        assert audio_content.mimeType == "audio/wav"
        
        # Check JsonContent
        json_content = restored.content[3]
        assert json_content.type == "json"
        assert json_content.content == {"nested": {"data": "value"}, "array": [1, 2, 3]}
        
        # Check tool calls preserved
        assert len(restored.tool_calls) == 1
        assert restored.tool_calls[0].name == "search_tool"
        assert restored.tool_calls[0].arguments == {"query": "test", "limit": 10}
        assert restored.tool_calls[0].id == "tool_call_123"
        
        # Check tool results preserved
        assert len(restored.tool_results) == 1
        assert restored.tool_results[0].id == "tool_result_456"
        assert restored.tool_results[0].isError is False
        assert len(restored.tool_results[0].content) == 1
        assert restored.tool_results[0].content[0].text == "Tool result"
    
    def test_complex_agent_request_complete_serialization(self):
        """Test that complex AgenticRequest preserves all fields perfectly"""
        # Create complex message with multiple content types
        complex_message = Message(
            role="user",
            content=[
                TextContent(type="text", text="Please analyze this image"),
                ImageContent(
                    type="image",
                    data="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
                    mimeType="image/png"
                )
            ]
        )
        
        # Create complex request
        original_request = AgenticRequest(
            message=complex_message,
            session_id="test-session-12345",
            stream=True,
            max_tokens=1000,
            include_thinking=True,
            context={
                "user_preferences": {"language": "en", "detail_level": "high"},
                "session_metadata": {"started_at": "2024-01-01T12:00:00Z"},
                "custom_config": {"temperature": 0.7, "top_p": 0.9}
            }
        )
        
        # Full serialization roundtrip
        serialized_data = original_request.model_dump()
        restored_request = AgenticRequest(**serialized_data)
        
        # Verify top-level fields
        assert restored_request.session_id == "test-session-12345"
        assert restored_request.stream is True
        assert restored_request.max_tokens == 1000
        assert restored_request.include_thinking is True
        assert restored_request.context == original_request.context
        
        # Verify message structure
        msg = restored_request.message
        assert msg.role == "user"
        assert len(msg.content) == 2
        assert msg.content[0].type == "text"
        assert msg.content[0].text == "Please analyze this image"
        assert msg.content[1].type == "image"
        assert msg.content[1].mimeType == "image/png"
    
    def test_json_string_serialization_preserves_discriminated_unions(self):
        """Test that JSON string serialization preserves discriminated union types"""
        # Create response with all content types
        message = Message(
            role="assistant",
            content=[
                TextContent(type="text", text="Mixed content response:"),
                JsonContent(type="json", content={"status": "success"}),
                ImageContent(type="image", data="base64data", mimeType="image/jpeg"),
                AudioContent(type="audio", data="audiodata", mimeType="audio/mp3")
            ]
        )
        
        response = AgenticResponse(
            message=message,
            session_id="json-test-session",
            metadata={"serialization_test": True, "content_types": 4}
        )
        
        # Serialize to JSON string
        json_str = response.model_dump_json()
        
        # Parse back from JSON string
        parsed_data = json.loads(json_str)
        restored_response = AgenticResponse(**parsed_data)
        
        # Verify all content types preserved with correct discriminator
        content = restored_response.message.content
        assert len(content) == 4
        
        assert content[0].type == "text"
        assert content[0].text == "Mixed content response:"
        
        assert content[1].type == "json" 
        assert content[1].content == {"status": "success"}
        
        assert content[2].type == "image"
        assert content[2].data == "base64data"
        assert content[2].mimeType == "image/jpeg"
        
        assert content[3].type == "audio"
        assert content[3].data == "audiodata"
        assert content[3].mimeType == "audio/mp3"
        
        # Verify metadata preserved
        assert restored_response.metadata["serialization_test"] is True
        assert restored_response.metadata["content_types"] == 4
    
    def test_timestamp_and_all_optional_fields_preserved(self):
        """Test that timestamps and all optional fields are preserved"""
        import time
        
        # Create message with explicit timestamp
        timestamp = time.time()
        message = Message(
            role="user",
            content=[TextContent(type="text", text="Test message")],
            timestamp=timestamp
        )
        
        # Serialize and restore
        data = message.model_dump()
        restored = Message(**data)
        
        # Verify timestamp preserved exactly
        assert restored.timestamp == timestamp
        assert abs(restored.timestamp_datetime.timestamp() - timestamp) < 0.001
        
        # Test with all None fields
        minimal_message = Message(
            role="assistant",
            content=None,
            tool_calls=[],
            tool_results=[]
        )
        
        minimal_data = minimal_message.model_dump()
        restored_minimal = Message(**minimal_data)
        
        assert restored_minimal.content is None
        assert restored_minimal.tool_calls == []
        assert restored_minimal.tool_results == []
    
    def test_empty_and_edge_case_serialization(self):
        """Test serialization of empty and edge case values"""
        # Empty context and metadata
        request = AgenticRequest(
            message=Message.from_text("user", "test"),
            context={},
            max_tokens=None,
            include_thinking=False
        )
        
        response = AgenticResponse(
            message=Message.from_text("assistant", "response"),
            session_id="edge-case-test",
            metadata={}
        )
        
        # Serialize both
        request_data = request.model_dump()
        response_data = response.model_dump()
        
        # Restore both
        restored_request = AgenticRequest(**request_data)
        restored_response = AgenticResponse(**response_data)
        
        # Verify empty collections preserved
        assert restored_request.context == {}
        assert restored_request.max_tokens is None
        assert restored_response.metadata == {}
        
        # Verify convenience properties still work
        assert restored_response.text == "response"
        assert restored_response.json_data == []
        assert restored_response.tool_calls == []
        assert restored_response.has_errors is False
