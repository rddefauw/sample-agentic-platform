import pytest
import json
from datetime import datetime

from agentic_platform.core.models.memory_models import (
    SessionContext, Message, Memory,
    TextContent, ImageContent, AudioContent, JsonContent, BaseContent,
    ToolCall, ToolResult,
    GetMemoriesRequest, CreateMemoryRequest,
    GetSessionContextRequest, UpsertSessionContextRequest
)


class TestMessageModel:
    """Test Message model functionality"""
    
    def test_message_with_text_parameter(self):
        """Test Message constructor with text parameter"""
        message = Message(role="user", text="Hello world")
        
        assert message.role == "user"
        assert len(message.content) == 1
        assert isinstance(message.content[0], TextContent)
        assert message.content[0].text == "Hello world"
        assert message.text == "Hello world"
    
    def test_message_from_text_classmethod(self):
        """Test Message.from_text convenience constructor"""
        message = Message.from_text("assistant", "How can I help?")
        
        assert message.role == "assistant"
        assert len(message.content) == 1
        assert isinstance(message.content[0], TextContent)
        assert message.content[0].text == "How can I help?"
        assert message.text == "How can I help?"
    
    def test_message_text_property_aggregation(self):
        """Test that Message.text aggregates multiple TextContent blocks"""
        message = Message(role="user", content=[
            TextContent(text="Hello"),
            TextContent(text="world"),
            ImageContent(data="base64", mimeType="image/png"),
            TextContent(text="!")
        ])
        
        assert message.text == "Hello world !"
    
    def test_message_content_getters(self):
        """Test Message content getter methods"""
        message = Message(role="user", content=[
            TextContent(text="Hello world"),
            ImageContent(data="base64data", mimeType="image/png"),
            AudioContent(data="audiodata", mimeType="audio/wav"),
            JsonContent(content={"key": "value"})
        ])
        
        text_content = message.get_text_content()
        assert isinstance(text_content, TextContent)
        assert text_content.text == "Hello world"
        
        image_content = message.get_image_content()
        assert isinstance(image_content, ImageContent)
        assert image_content.data == "base64data"
        assert image_content.mimeType == "image/png"
        
        audio_content = message.get_audio_content()
        assert isinstance(audio_content, AudioContent)
        assert audio_content.data == "audiodata"
        assert audio_content.mimeType == "audio/wav"
        
        json_content = message.get_json_content()
        assert isinstance(json_content, JsonContent)
        assert json_content.content == {"key": "value"}
    
    def test_message_timestamp_handling(self):
        """Test Message timestamp functionality"""
        message = Message.from_text("user", "Test")
        
        # Should have a timestamp
        assert message.timestamp > 0
        
        # Should be able to get datetime
        dt = message.timestamp_datetime
        assert isinstance(dt, datetime)


class TestToolResultContentConversion:
    """Test ToolResult.to_content conversion logic"""
    
    def test_string_to_content(self):
        """Test string conversion to TextContent"""
        result = ToolResult.to_content("Hello world")
        
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert result[0].text == "Hello world"
    
    def test_dict_to_content(self):
        """Test dict conversion to JsonContent"""
        data = {"key": "value", "number": 42}
        result = ToolResult.to_content(data)
        
        assert len(result) == 1
        assert isinstance(result[0], JsonContent)
        assert result[0].content == data
    
    def test_list_to_content(self):
        """Test list conversion (should flatten)"""
        data = ["hello", {"key": "value"}, 42]
        result = ToolResult.to_content(data)
        
        assert len(result) == 3
        assert isinstance(result[0], TextContent)
        assert result[0].text == "hello"
        assert isinstance(result[1], JsonContent)
        assert result[1].content == {"key": "value"}
        assert isinstance(result[2], TextContent)
        assert result[2].text == "42"
    
    def test_none_to_content(self):
        """Test None conversion (should return empty list)"""
        result = ToolResult.to_content(None)
        assert result == []
    
    def test_numeric_types_to_content(self):
        """Test numeric type conversion"""
        int_result = ToolResult.to_content(42)
        assert len(int_result) == 1
        assert isinstance(int_result[0], TextContent)
        assert int_result[0].text == "42"
        
        float_result = ToolResult.to_content(3.14)
        assert len(float_result) == 1
        assert isinstance(float_result[0], TextContent)
        assert float_result[0].text == "3.14"
        
        bool_result = ToolResult.to_content(True)
        assert len(bool_result) == 1
        assert isinstance(bool_result[0], TextContent)
        assert bool_result[0].text == "True"


class TestSessionContextModel:
    """Test SessionContext model functionality"""
    
    def test_session_context_creation(self):
        """Test SessionContext creation with defaults"""
        session = SessionContext()
        
        # Should have auto-generated session_id
        assert session.session_id is not None
        assert len(session.session_id) > 0
        
        # Should have empty messages list
        assert session.messages == []
        
        # Optional fields should be None
        assert session.user_id is None
        assert session.agent_id is None
        assert session.system_prompt is None
        assert session.session_metadata is None
    
    def test_add_single_message(self):
        """Test adding a single message"""
        session = SessionContext(session_id="test")
        message = Message.from_text("user", "Hello")
        
        session.add_message(message)
        
        assert len(session.messages) == 1
        assert session.messages[0] is message
    
    def test_add_multiple_messages(self):
        """Test adding multiple messages at once"""
        session = SessionContext(session_id="test")
        messages = [
            Message.from_text("user", "Hello"),
            Message.from_text("assistant", "Hi there")
        ]
        
        session.add_messages(messages)
        
        assert len(session.messages) == 2
        assert session.messages == messages
    
    def test_get_messages(self):
        """Test get_messages method"""
        session = SessionContext(session_id="test")
        messages = [
            Message.from_text("user", "Hello"),
            Message.from_text("assistant", "Hi")
        ]
        session.add_messages(messages)
        
        retrieved = session.get_messages()
        assert retrieved == messages
    
    def test_add_metadata(self):
        """Test adding metadata"""
        session = SessionContext(session_id="test")
        metadata = {"key": "value", "number": 42}
        
        session.add_metadata(metadata)
        
        assert session.session_metadata == metadata


class TestMemoryModel:
    """Test Memory model functionality"""
    
    def test_memory_creation_with_required_fields(self):
        """Test Memory creation with all required fields"""
        memory = Memory(
            session_id="session-123",
            user_id="user-456", 
            agent_id="agent-789",
            content="Test memory content",
            embedding_model="test-model"
        )
        
        assert memory.session_id == "session-123"
        assert memory.user_id == "user-456"
        assert memory.agent_id == "agent-789"
        assert memory.content == "Test memory content"
        assert memory.embedding_model == "test-model"
        
        # Should have auto-generated fields
        assert memory.memory_id is not None
        assert len(memory.memory_id) > 0
        assert isinstance(memory.created_at, datetime)
        assert isinstance(memory.updated_at, datetime)
        
        # Should have default values
        assert memory.similarity == -1.0
        assert memory.embedding is None
    
    def test_memory_with_embedding(self):
        """Test Memory with embedding vector"""
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        memory = Memory(
            session_id="session-123",
            user_id="user-456",
            agent_id="agent-789", 
            content="Test content",
            embedding_model="test-model",
            embedding=embedding,
            similarity=0.95
        )
        
        assert memory.embedding == embedding
        assert memory.similarity == 0.95


class TestRequestModels:
    """Test request model validation"""
    
    def test_get_memories_request_validation(self):
        """Test GetMemoriesRequest validation logic"""
        # Should work with session_id
        request1 = GetMemoriesRequest(
            session_id="session-123",
            agent_id="agent-456"
        )
        assert request1.agent_id == "agent-456"
        
        # Should work with user_id
        request2 = GetMemoriesRequest(
            user_id="user-123", 
            agent_id="agent-456"
        )
        assert request2.agent_id == "agent-456"
        
        # Should fail without either
        with pytest.raises(ValueError, match="Either session_id or user_id must be provided"):
            GetMemoriesRequest(agent_id="agent-456")
    
    def test_get_memories_request_default_limit(self):
        """Test GetMemoriesRequest default limit"""
        request = GetMemoriesRequest(user_id="user-123")
        assert request.limit == 2
    
    def test_get_session_context_request(self):
        """Test GetSessionContextRequest creation"""
        request = GetSessionContextRequest(
            user_id="test-user",
            session_id="test-session"
        )
        assert request.user_id == "test-user"
        assert request.session_id == "test-session"
    
    def test_create_memory_request(self):
        """Test CreateMemoryRequest creation"""
        session_context = SessionContext(session_id="test-session")
        request = CreateMemoryRequest(
            session_id="test-session",
            user_id="test-user",
            agent_id="test-agent",
            session_context=session_context
        )
        assert request.session_id == "test-session"
        assert request.user_id == "test-user"
        assert request.agent_id == "test-agent"
        assert request.session_context == session_context


class TestSerializationFixed:
    """Test serialization/deserialization - these tests verify the discriminated union fix works"""
    
    def test_text_content_serialization_works(self):
        """Test that TextContent serializes and deserializes correctly - BUG FIXED"""
        session = SessionContext(session_id="test-session")
        message = Message(role="user", content=[TextContent(text="Hello world")])
        session.add_message(message)
        
        # Serialize
        json_data = session.model_dump_json()
        
        # Deserialize
        restored = SessionContext.model_validate_json(json_data)
        restored_content = restored.messages[0].content[0]
        
        # This now works correctly with discriminated union
        assert isinstance(restored_content, TextContent), f"Expected TextContent, got {type(restored_content)}"
        assert restored_content.text == "Hello world"
        assert restored_content.type == "text"
    
    def test_mixed_content_serialization_works(self):
        """Test serialization with multiple content types - BUG FIXED"""
        session = SessionContext(session_id="test-session")
        message = Message(role="user", content=[
            TextContent(text="Hello world"),
            ImageContent(data="base64data", mimeType="image/png"),
            JsonContent(content={"key": "value"})
        ])
        session.add_message(message)
        
        # Serialize
        json_data = session.model_dump_json()
        
        # Deserialize  
        restored = SessionContext.model_validate_json(json_data)
        restored_contents = restored.messages[0].content
        
        # All content types are now preserved correctly
        assert len(restored_contents) == 3
        assert isinstance(restored_contents[0], TextContent)
        assert isinstance(restored_contents[1], ImageContent)
        assert isinstance(restored_contents[2], JsonContent)
        
        # Check content values are preserved
        assert restored_contents[0].text == "Hello world"
        assert restored_contents[1].data == "base64data"
        assert restored_contents[1].mimeType == "image/png"
        assert restored_contents[2].content == {"key": "value"}
    
    def test_serialization_preserves_all_data(self):
        """Test that all data is properly preserved in JSON serialization"""
        session = SessionContext(session_id="test-session")
        message = Message(role="user", content=[
            TextContent(text="Hello world"),
            ImageContent(data="base64data", mimeType="image/png")
        ])
        session.add_message(message)
        
        # Check the raw JSON structure
        json_data = session.model_dump_json()
        parsed = json.loads(json_data)
        
        # Structure is preserved
        assert parsed["session_id"] == "test-session"
        assert len(parsed["messages"]) == 1
        assert len(parsed["messages"][0]["content"]) == 2
        
        # Type information is preserved
        assert parsed["messages"][0]["content"][0]["type"] == "text"
        assert parsed["messages"][0]["content"][1]["type"] == "image"
        
        # All content data is now properly included in the JSON
        content_items = parsed["messages"][0]["content"]
        text_item = content_items[0]
        image_item = content_items[1]
        
        # All fields are now present - bug is fixed!
        assert "text" in text_item
        assert text_item["text"] == "Hello world"
        assert "data" in image_item
        assert image_item["data"] == "base64data"
        assert "mimeType" in image_item
        assert image_item["mimeType"] == "image/png" 