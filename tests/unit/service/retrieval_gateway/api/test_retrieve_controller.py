import pytest
from unittest.mock import patch, MagicMock

from agentic_platform.service.retrieval_gateway.api.retrieve_controller import RetrieveController
from agentic_platform.core.models.api_models import RetrieveRequest, RetrieveResponse
from agentic_platform.core.models.vectordb_models import (
    VectorSearchRequest, 
    VectorSearchResponse, 
    VectorSearchResult
)


class TestRetrieveController:
    """Test RetrieveController - handles vector search retrieval requests"""
    
    @patch('agentic_platform.service.retrieval_gateway.api.retrieve_controller.VectorSearchClient.retrieve')
    def test_retrieve_success(self, mock_vector_search):
        """Test successful retrieval request"""
        # Setup mock vector search response
        mock_results = [
            VectorSearchResult(
                text="Sample document text",
                score=0.85,
                metadata={"source": "doc1.pdf"},
                source_location={"uri": "s3://bucket/doc1.pdf"},
                content_type="text"
            )
        ]
        mock_response = VectorSearchResponse(
            results=mock_results,
            guardrail_action=None
        )
        mock_vector_search.return_value = mock_response
        
        # Create retrieve request
        vector_request = VectorSearchRequest(
            query="What is machine learning?",
            limit=5
        )
        request = RetrieveRequest(vectorsearch_request=vector_request)
        
        # Call controller
        result = RetrieveController.retrieve(request)
        
        # Verify vector search client was called
        mock_vector_search.assert_called_once_with(vector_request)
        
        # Verify response structure
        assert isinstance(result, RetrieveResponse)
        assert result.vectorsearch_results == mock_response
        assert len(result.vectorsearch_results.results) == 1
        assert result.vectorsearch_results.results[0].text == "Sample document text"
        assert result.vectorsearch_results.results[0].score == 0.85
    
    @patch('agentic_platform.service.retrieval_gateway.api.retrieve_controller.VectorSearchClient.retrieve')
    def test_retrieve_empty_results(self, mock_vector_search):
        """Test retrieval with no results found"""
        # Setup mock empty response
        mock_response = VectorSearchResponse(
            results=[],
            guardrail_action=None
        )
        mock_vector_search.return_value = mock_response
        
        # Create retrieve request
        vector_request = VectorSearchRequest(
            query="nonexistent topic",
            limit=10
        )
        request = RetrieveRequest(vectorsearch_request=vector_request)
        
        # Call controller
        result = RetrieveController.retrieve(request)
        
        # Verify response structure
        assert isinstance(result, RetrieveResponse)
        assert result.vectorsearch_results.results == []
        assert len(result.vectorsearch_results.results) == 0
    
    @patch('agentic_platform.service.retrieval_gateway.api.retrieve_controller.VectorSearchClient.retrieve')
    def test_retrieve_multiple_results(self, mock_vector_search):
        """Test retrieval with multiple results"""
        # Setup mock multiple results
        mock_results = [
            VectorSearchResult(
                text="First document about AI",
                score=0.92,
                metadata={"source": "ai_guide.pdf", "page": 1},
                source_location={"uri": "s3://bucket/ai_guide.pdf"},
                content_type="text"
            ),
            VectorSearchResult(
                text="Second document about machine learning",
                score=0.87,
                metadata={"source": "ml_book.pdf", "page": 15},
                source_location={"uri": "s3://bucket/ml_book.pdf"},
                content_type="text"
            ),
            VectorSearchResult(
                text="Third document about deep learning",
                score=0.81,
                metadata={"source": "dl_paper.pdf", "page": 3},
                source_location={"uri": "s3://bucket/dl_paper.pdf"},
                content_type="text"
            )
        ]
        mock_response = VectorSearchResponse(
            results=mock_results,
            guardrail_action=None
        )
        mock_vector_search.return_value = mock_response
        
        # Create retrieve request
        vector_request = VectorSearchRequest(
            query="artificial intelligence and machine learning",
            limit=3
        )
        request = RetrieveRequest(vectorsearch_request=vector_request)
        
        # Call controller
        result = RetrieveController.retrieve(request)
        
        # Verify response
        assert isinstance(result, RetrieveResponse)
        assert len(result.vectorsearch_results.results) == 3
        
        # Verify results are in expected order (by score)
        scores = [r.score for r in result.vectorsearch_results.results]
        assert scores == [0.92, 0.87, 0.81]
        
        # Verify all metadata is preserved
        assert result.vectorsearch_results.results[0].metadata["page"] == 1
        assert result.vectorsearch_results.results[1].metadata["page"] == 15
        assert result.vectorsearch_results.results[2].metadata["page"] == 3
    
    @patch('agentic_platform.service.retrieval_gateway.api.retrieve_controller.VectorSearchClient.retrieve')
    def test_retrieve_with_guardrail_action(self, mock_vector_search):
        """Test retrieval with guardrail action present"""
        # Setup mock response with guardrail action
        mock_results = [
            VectorSearchResult(
                text="Filtered content",
                score=0.75,
                metadata={"filtered": True},
                source_location={"uri": "s3://bucket/filtered.pdf"},
                content_type="text"
            )
        ]
        mock_response = VectorSearchResponse(
            results=mock_results,
            guardrail_action="ABSTAINED"
        )
        mock_vector_search.return_value = mock_response
        
        # Create retrieve request
        vector_request = VectorSearchRequest(
            query="potentially sensitive query",
            limit=5
        )
        request = RetrieveRequest(vectorsearch_request=vector_request)
        
        # Call controller
        result = RetrieveController.retrieve(request)
        
        # Verify guardrail action is preserved
        assert result.vectorsearch_results.guardrail_action == "ABSTAINED"
        assert len(result.vectorsearch_results.results) == 1
    
    @patch('agentic_platform.service.retrieval_gateway.api.retrieve_controller.VectorSearchClient.retrieve')
    def test_retrieve_propagates_exceptions(self, mock_vector_search):
        """Test that exceptions from VectorSearchClient are propagated"""
        # Setup vector search client to raise exception
        mock_vector_search.side_effect = RuntimeError("Vector search service unavailable")
        
        # Create retrieve request
        vector_request = VectorSearchRequest(
            query="test query",
            limit=5
        )
        request = RetrieveRequest(vectorsearch_request=vector_request)
        
        # Should raise the same exception
        with pytest.raises(RuntimeError, match="Vector search service unavailable"):
            RetrieveController.retrieve(request)
        
        # Verify vector search client was called
        mock_vector_search.assert_called_once_with(vector_request)
    
    def test_retrieve_method_signature(self):
        """Test the retrieve method signature"""
        import inspect
        
        method = getattr(RetrieveController, 'retrieve')
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())
        
        # Should be a classmethod with cls and request parameters
        assert params == ['request']
        
        # Check parameter types
        assert sig.parameters['request'].annotation == RetrieveRequest
        assert sig.return_annotation == RetrieveResponse
    
    def test_retrieve_controller_class_structure(self):
        """Test RetrieveController class structure"""
        import inspect
        
        # Should have retrieve method
        assert hasattr(RetrieveController, 'retrieve')
        
        # retrieve should be a classmethod
        assert isinstance(inspect.getattr_static(RetrieveController, 'retrieve'), classmethod)
    
    @patch('agentic_platform.service.retrieval_gateway.api.retrieve_controller.VectorSearchClient.retrieve')
    @patch('builtins.print')  # Mock print to avoid console output during tests
    def test_retrieve_prints_response(self, mock_print, mock_vector_search):
        """Test that controller prints the response for debugging"""
        # Setup mock response
        mock_response = VectorSearchResponse(results=[], guardrail_action=None)
        mock_vector_search.return_value = mock_response
        
        # Create request
        vector_request = VectorSearchRequest(query="test", limit=5)
        request = RetrieveRequest(vectorsearch_request=vector_request)
        
        # Call controller
        RetrieveController.retrieve(request)
        
        # Verify print was called with response
        mock_print.assert_called_once_with(f"Response: {mock_response}") 