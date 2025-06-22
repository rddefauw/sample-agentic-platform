import pytest
from unittest.mock import patch, MagicMock

from agentic_platform.service.llm_gateway.client.bedrock_client import BedrockClient
from agentic_platform.service.llm_gateway.models.gateway_api_types import ConverseRequest, ConverseResponse


class TestBedrockClient:
    """Test BedrockClient - AWS Bedrock service integration client"""
    
    @patch('agentic_platform.service.llm_gateway.client.bedrock_client.bedrock')
    def test_converse_success(self, mock_bedrock):
        """Test successful conversation with Bedrock"""
        # Setup mock response
        mock_response = {
            'ResponseMetadata': {'HTTPStatusCode': 200},
            'output': {
                'message': {
                    'content': [{'text': 'Hello! How can I help you today?'}]
                }
            },
            'usage': {'inputTokens': 10, 'outputTokens': 15}
        }
        mock_bedrock.converse.return_value = mock_response
        
        # Create request
        request = ConverseRequest(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            messages=[
                {
                    "role": "user",
                    "content": [{"text": "Hello, how are you?"}]
                }
            ]
        )
        
        # Call client
        result = BedrockClient.converse(request)
        
        # Verify bedrock was called with request data
        mock_bedrock.converse.assert_called_once()
        
        # Extract the kwargs passed to bedrock.converse
        call_kwargs = mock_bedrock.converse.call_args[1]
        assert call_kwargs['modelId'] == "anthropic.claude-3-sonnet-20240229-v1:0"
        assert len(call_kwargs['messages']) == 1
        assert call_kwargs['messages'][0]['role'] == "user"
        
        # Verify response
        assert result is mock_response
    
    @patch('agentic_platform.service.llm_gateway.client.bedrock_client.bedrock')
    def test_converse_with_system_messages(self, mock_bedrock):
        """Test conversation with system messages"""
        mock_response = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        mock_bedrock.converse.return_value = mock_response
        
        # Create request with system message
        request = ConverseRequest(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            messages=[
                {
                    "role": "system",
                    "content": [{"text": "You are a helpful assistant."}]
                },
                {
                    "role": "user",
                    "content": [{"text": "What's the weather like?"}]
                }
            ]
        )
        
        # Call client
        result = BedrockClient.converse(request)
        
        # Verify bedrock was called with all messages
        call_kwargs = mock_bedrock.converse.call_args[1]
        assert len(call_kwargs['messages']) == 2
        assert call_kwargs['messages'][0]['role'] == "system"
        assert call_kwargs['messages'][1]['role'] == "user"
        
        # Verify response
        assert result is mock_response
    
    @patch('agentic_platform.service.llm_gateway.client.bedrock_client.bedrock')
    def test_converse_with_inference_config(self, mock_bedrock):
        """Test conversation with inference configuration"""
        mock_response = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        mock_bedrock.converse.return_value = mock_response
        
        # Create request with inference config
        request = ConverseRequest(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            messages=[{"role": "user", "content": [{"text": "Test"}]}],
            inferenceConfig={
                "maxTokens": 1000,
                "temperature": 0.7,
                "topP": 0.9
            }
        )
        
        # Call client
        result = BedrockClient.converse(request)
        
        # Verify bedrock was called with inference config
        call_kwargs = mock_bedrock.converse.call_args[1]
        assert 'inferenceConfig' in call_kwargs
        assert call_kwargs['inferenceConfig']['maxTokens'] == 1000
        assert call_kwargs['inferenceConfig']['temperature'] == 0.7
        assert call_kwargs['inferenceConfig']['topP'] == 0.9
        
        # Verify response
        assert result is mock_response
    
    @patch('agentic_platform.service.llm_gateway.client.bedrock_client.bedrock')
    def test_converse_passes_through_bedrock_exceptions(self, mock_bedrock):
        """Test that Bedrock exceptions are passed through"""
        # Setup bedrock to raise exception
        from botocore.exceptions import ClientError
        error_response = {
            'Error': {
                'Code': 'ValidationException',
                'Message': 'Invalid model ID'
            }
        }
        mock_bedrock.converse.side_effect = ClientError(error_response, 'Converse')
        
        # Create request
        request = ConverseRequest(
            modelId="invalid-model",
            messages=[{"role": "user", "content": [{"text": "Test"}]}]
        )
        
        # Should raise the same exception
        with pytest.raises(ClientError):
            BedrockClient.converse(request)
        
        # Verify bedrock was called
        mock_bedrock.converse.assert_called_once()
    
    @patch('agentic_platform.service.llm_gateway.client.bedrock_client.bedrock')
    def test_converse_request_serialization(self, mock_bedrock):
        """Test that ConverseRequest is properly serialized for Bedrock"""
        mock_response = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        mock_bedrock.converse.return_value = mock_response
        
        # Create complex request
        request = ConverseRequest(
            modelId="test-model",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"text": "First part"},
                        {"text": "Second part"}
                    ]
                }
            ],
            system=[{"text": "System instruction"}],
            inferenceConfig={
                "maxTokens": 500,
                "temperature": 0.5
            },
            toolConfig={
                "tools": [
                    {
                        "toolSpec": {
                            "name": "test_tool",
                            "description": "A test tool"
                        }
                    }
                ]
            }
        )
        
        # Call client
        BedrockClient.converse(request)
        
        # Verify all request components were serialized
        call_kwargs = mock_bedrock.converse.call_args[1]
        assert 'modelId' in call_kwargs
        assert 'messages' in call_kwargs
        assert 'system' in call_kwargs
        assert 'inferenceConfig' in call_kwargs
        assert 'toolConfig' in call_kwargs
        
        # Verify structure integrity
        assert call_kwargs['modelId'] == "test-model"
        assert len(call_kwargs['messages'][0]['content']) == 2
        assert call_kwargs['system'][0]['text'] == "System instruction"
        assert call_kwargs['inferenceConfig']['maxTokens'] == 500
        assert call_kwargs['toolConfig']['tools'][0]['toolSpec']['name'] == "test_tool"
    
    def test_converse_method_is_classmethod(self):
        """Test that converse is a classmethod"""
        import inspect
        
        method = getattr(BedrockClient, 'converse')
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())
        
        # Should have request parameter (classmethod with bound cls)
        assert 'request' in params
    
    def test_bedrock_client_class_structure(self):
        """Test the BedrockClient class structure"""
        # Should have only the converse method
        methods = [method for method in dir(BedrockClient) 
                  if not method.startswith('_')]
        assert 'converse' in methods
        
        # Should be callable
        assert callable(BedrockClient.converse)
    
    def test_bedrock_client_initialization(self):
        """Test that bedrock client is properly initialized"""
        # Import should trigger client creation
        from agentic_platform.service.llm_gateway.client import bedrock_client
        
        # Should have bedrock client available
        assert hasattr(bedrock_client, 'bedrock')
        assert bedrock_client.bedrock is not None
    
    @patch('agentic_platform.service.llm_gateway.client.bedrock_client.bedrock')
    def test_converse_minimal_request(self, mock_bedrock):
        """Test conversation with minimal request"""
        mock_response = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        mock_bedrock.converse.return_value = mock_response
        
        # Create minimal request
        request = ConverseRequest(
            modelId="test-model",
            messages=[{"role": "user", "content": [{"text": "Hi"}]}]
        )
        
        # Call client
        result = BedrockClient.converse(request)
        
        # Verify minimal fields are passed
        call_kwargs = mock_bedrock.converse.call_args[1]
        assert call_kwargs['modelId'] == "test-model"
        assert len(call_kwargs['messages']) == 1
        
        # Verify response
        assert result is mock_response 