import pytest
from unittest.mock import patch, MagicMock

from agentic_platform.service.retrieval_gateway.client.vectorsearch_client import VectorSearchClient
from agentic_platform.core.models.vectordb_models import (
    VectorSearchRequest, 
    VectorSearchResponse, 
    VectorSearchResult,
    FilterCondition
)


class TestVectorSearchClient:
    """Test VectorSearchClient - shim for calling vector databases"""
    
    @patch('agentic_platform.service.retrieval_gateway.client.vectorsearch_client.BedrockKnowledgeBaseClient.retrieve')
    def test_retrieve_success(self, mock_bedrock_retrieve):
        """Test successful vector search retrieval"""
        # Setup mock response from Bedrock KB
        mock_results = [
            VectorSearchResult(
                text="Machine learning is a subset of artificial intelligence",
                score=0.89,
                metadata={"source": "ml_textbook.pdf", "chapter": "1"},
                source_location={"uri": "s3://docs/ml_textbook.pdf"},
                content_type="text"
            )
        ]
        mock_response = VectorSearchResponse(
            results=mock_results,
            guardrail_action=None
        )
        mock_bedrock_retrieve.return_value = mock_response
        
        # Create vector search request
        request = VectorSearchRequest(
            query="What is machine learning?",
            limit=5
        )
        
        # Call vector search client
        result = VectorSearchClient.retrieve(request)
        
        # Verify Bedrock KB client was called
        mock_bedrock_retrieve.assert_called_once_with(request)
        
        # Verify response is passed through unchanged
        assert result is mock_response
        assert isinstance(result, VectorSearchResponse)
        assert len(result.results) == 1
        assert result.results[0].text == "Machine learning is a subset of artificial intelligence"
        assert result.results[0].score == 0.89
    
    @patch('agentic_platform.service.retrieval_gateway.client.vectorsearch_client.BedrockKnowledgeBaseClient.retrieve')
    def test_retrieve_with_filters(self, mock_bedrock_retrieve):
        """Test vector search with filters"""
        # Setup mock response
        mock_response = VectorSearchResponse(results=[], guardrail_action=None)
        mock_bedrock_retrieve.return_value = mock_response
        
        # Create request with filters
        filters = [
            FilterCondition(field="document_type", operator="eq", value="manual"),
            FilterCondition(field="year", operator="gte", value="2020")
        ]
        request = VectorSearchRequest(
            query="installation instructions",
            limit=10,
            filters=filters
        )
        
        # Call vector search client
        result = VectorSearchClient.retrieve(request)
        
        # Verify Bedrock KB client was called with exact request
        mock_bedrock_retrieve.assert_called_once_with(request)
        
        # Verify response is passed through
        assert result is mock_response
    
    @patch('agentic_platform.service.retrieval_gateway.client.vectorsearch_client.BedrockKnowledgeBaseClient.retrieve')
    def test_retrieve_with_search_type(self, mock_bedrock_retrieve):
        """Test vector search with specific search type"""
        # Setup mock response
        mock_response = VectorSearchResponse(results=[], guardrail_action=None)
        mock_bedrock_retrieve.return_value = mock_response
        
        # Create request with search type
        request = VectorSearchRequest(
            query="hybrid search query",
            limit=5,
            search_type="HYBRID"
        )
        
        # Call vector search client
        result = VectorSearchClient.retrieve(request)
        
        # Verify Bedrock KB client was called with request including search type
        mock_bedrock_retrieve.assert_called_once_with(request)
        assert result is mock_response
    
    @patch('agentic_platform.service.retrieval_gateway.client.vectorsearch_client.BedrockKnowledgeBaseClient.retrieve')
    def test_retrieve_multiple_results(self, mock_bedrock_retrieve):
        """Test vector search returning multiple results"""
        # Setup mock response with multiple results
        mock_results = [
            VectorSearchResult(
                text="First relevant document",
                score=0.95,
                metadata={"doc_id": "1", "category": "tech"},
                source_location={"uri": "s3://docs/doc1.pdf"},
                content_type="text"
            ),
            VectorSearchResult(
                text="Second relevant document", 
                score=0.88,
                metadata={"doc_id": "2", "category": "tech"},
                source_location={"uri": "s3://docs/doc2.pdf"},
                content_type="text"
            ),
            VectorSearchResult(
                text="Third relevant document",
                score=0.82,
                metadata={"doc_id": "3", "category": "business"},
                source_location={"uri": "s3://docs/doc3.pdf"},
                content_type="text"
            )
        ]
        mock_response = VectorSearchResponse(
            results=mock_results,
            guardrail_action=None
        )
        mock_bedrock_retrieve.return_value = mock_response
        
        # Create request
        request = VectorSearchRequest(
            query="comprehensive search query",
            limit=3
        )
        
        # Call vector search client
        result = VectorSearchClient.retrieve(request)
        
        # Verify all results are passed through
        assert len(result.results) == 3
        assert result.results[0].score == 0.95
        assert result.results[1].score == 0.88
        assert result.results[2].score == 0.82
        
        # Verify metadata is preserved
        assert result.results[0].metadata["category"] == "tech"
        assert result.results[2].metadata["category"] == "business"
    
    @patch('agentic_platform.service.retrieval_gateway.client.vectorsearch_client.BedrockKnowledgeBaseClient.retrieve')
    def test_retrieve_empty_results(self, mock_bedrock_retrieve):
        """Test vector search with no results"""
        # Setup mock empty response
        mock_response = VectorSearchResponse(
            results=[],
            guardrail_action=None
        )
        mock_bedrock_retrieve.return_value = mock_response
        
        # Create request
        request = VectorSearchRequest(
            query="query with no matches",
            limit=5
        )
        
        # Call vector search client
        result = VectorSearchClient.retrieve(request)
        
        # Verify empty results are handled correctly
        assert len(result.results) == 0
        assert result.results == []
        assert result.guardrail_action is None
    
    @patch('agentic_platform.service.retrieval_gateway.client.vectorsearch_client.BedrockKnowledgeBaseClient.retrieve')
    def test_retrieve_with_guardrail_action(self, mock_bedrock_retrieve):
        """Test vector search with guardrail action"""
        # Setup mock response with guardrail action
        mock_response = VectorSearchResponse(
            results=[],
            guardrail_action="ABSTAINED"
        )
        mock_bedrock_retrieve.return_value = mock_response
        
        # Create request
        request = VectorSearchRequest(
            query="potentially sensitive content",
            limit=5
        )
        
        # Call vector search client
        result = VectorSearchClient.retrieve(request)
        
        # Verify guardrail action is preserved
        assert result.guardrail_action == "ABSTAINED"
        assert len(result.results) == 0
    
    @patch('agentic_platform.service.retrieval_gateway.client.vectorsearch_client.BedrockKnowledgeBaseClient.retrieve')
    def test_retrieve_propagates_exceptions(self, mock_bedrock_retrieve):
        """Test that exceptions from Bedrock KB client are propagated"""
        # Setup Bedrock KB to raise exception
        mock_bedrock_retrieve.side_effect = ValueError("Knowledge base not found")
        
        # Create request
        request = VectorSearchRequest(
            query="test query",
            limit=5
        )
        
        # Should raise the same exception
        with pytest.raises(ValueError, match="Knowledge base not found"):
            VectorSearchClient.retrieve(request)
        
        # Verify Bedrock KB client was called
        mock_bedrock_retrieve.assert_called_once_with(request)
    
    @patch('agentic_platform.service.retrieval_gateway.client.vectorsearch_client.BedrockKnowledgeBaseClient.retrieve')
    def test_retrieve_handles_boto3_exceptions(self, mock_bedrock_retrieve):
        """Test that boto3 exceptions are propagated"""
        from botocore.exceptions import ClientError
        
        # Setup Bedrock KB to raise boto3 exception
        error_response = {
            'Error': {
                'Code': 'ResourceNotFoundException',
                'Message': 'Knowledge base not found'
            }
        }
        mock_bedrock_retrieve.side_effect = ClientError(error_response, 'Retrieve')
        
        # Create request
        request = VectorSearchRequest(
            query="test query",
            limit=5
        )
        
        # Should raise the same ClientError
        with pytest.raises(ClientError):
            VectorSearchClient.retrieve(request)
    
    def test_retrieve_method_signature(self):
        """Test the retrieve method signature"""
        import inspect
        
        method = getattr(VectorSearchClient, 'retrieve')
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())
        
        # Should be a classmethod with cls and request parameters
        assert params == ['request']
        
        # Check parameter types
        assert sig.parameters['request'].annotation == VectorSearchRequest
        assert sig.return_annotation == VectorSearchResponse
    
    def test_vectorsearch_client_class_structure(self):
        """Test VectorSearchClient class structure"""
        import inspect
        
        # Should have retrieve method
        assert hasattr(VectorSearchClient, 'retrieve')
        
        # retrieve should be a classmethod
        assert isinstance(inspect.getattr_static(VectorSearchClient, 'retrieve'), classmethod)
        
        # Should have proper docstring
        assert VectorSearchClient.__doc__ == "Shim for calling a vectorDB. Makes it easy to swap out vectorDBs."
    
    def test_vectorsearch_client_as_shim(self):
        """Test that VectorSearchClient acts as a proper shim/abstraction layer"""
        # The client should delegate to BedrockKnowledgeBaseClient
        # This allows easy swapping of vector DB implementations
        
        # Check that it imports the right modules
        from agentic_platform.service.retrieval_gateway.client.vectorsearch_client import BedrockKnowledgeBaseClient
        assert BedrockKnowledgeBaseClient is not None
        
        # The retrieve method should be simple delegation
        import inspect
        source = inspect.getsource(VectorSearchClient.retrieve)
        assert "BedrockKnowledgeBaseClient.retrieve" in source
        assert "return" in source 