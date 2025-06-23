"""
Integration tests for Retrieval Gateway.

This module contains integration tests for the Retrieval Gateway service,
testing the controller functionality with mocked external dependencies.
"""

import pytest
import sys
import os
from typing import Dict, Any
import uuid
from unittest.mock import patch, MagicMock

# Add the source directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../', 'src'))

from agentic_platform.core.models.api_models import RetrieveRequest, RetrieveResponse
from agentic_platform.core.models.vectordb_models import VectorSearchRequest, VectorSearchResponse, VectorSearchResult, FilterCondition

class TestRetrievalGateway:
    """Integration tests for Retrieval Gateway controller with mocked external dependencies"""
    
    def test_retrieve_happy_path(self, sample_retrieve_request):
        """Test the retrieve controller happy path"""
        
        # Create a mock search result
        mock_result = VectorSearchResult(
            text="This is a sample search result for testing",
            score=0.95,
            metadata={"source": "test-document"}
        )
        
        # Create a mock search response
        mock_search_response = VectorSearchResponse(
            results=[mock_result]
        )
        
        try:
            from agentic_platform.service.retrieval_gateway.api.retrieve_controller import RetrieveController
            from agentic_platform.service.retrieval_gateway.client.vectorsearch_client import VectorSearchClient
            
            # Convert the request dict to a proper RetrieveRequest object
            request = RetrieveRequest(**sample_retrieve_request)
            
            # Mock the vector search client
            with patch.object(VectorSearchClient, 'retrieve', return_value=mock_search_response) as mock_retrieve:
                
                # Call the controller
                response = RetrieveController.retrieve(request)
                
                # Verify the response
                assert isinstance(response, RetrieveResponse), "Response should be RetrieveResponse"
                assert response.vectorsearch_results is not None, "Response should have vectorsearch_results"
                assert response.vectorsearch_results.results is not None, "vectorsearch_results should have results"
                
                # Verify results structure
                search_results = response.vectorsearch_results.results
                assert isinstance(search_results, list), "results should be a list"
                
                # We should have our mock result
                assert len(search_results) > 0, "Should have at least one result"
                
                # Check the structure of the first result
                first_result = search_results[0]
                assert first_result.text == "This is a sample search result for testing", "Result text should match mock"
                assert first_result.score == 0.95, "Result score should match mock"
                assert first_result.metadata == {"source": "test-document"}, "Result metadata should match mock"
                
                # Verify that the vector search client was called with the correct request
                mock_retrieve.assert_called_once_with(request.vectorsearch_request)
                
                print(f"✅ Retrieval Gateway retrieve test passed!")
                print(f"   Retrieved {len(search_results)} results")
                
        except ImportError as e:
            pytest.skip(f"Retrieval Gateway controller not available: {e}")
        except Exception as e:
            pytest.fail(f"Error testing Retrieval Gateway controller: {e}")
    
    def test_retrieve_with_filters(self):
        """Test the retrieve controller with filters"""
        
        # Create a mock search result
        mock_result = VectorSearchResult(
            text="This is a filtered search result",
            score=0.85,
            metadata={"category": "test"}
        )
        
        # Create a mock search response
        mock_search_response = VectorSearchResponse(
            results=[mock_result]
        )
        
        try:
            from agentic_platform.service.retrieval_gateway.api.retrieve_controller import RetrieveController
            from agentic_platform.service.retrieval_gateway.client.vectorsearch_client import VectorSearchClient
            
            # Create a request with filters
            filter_condition = FilterCondition(
                field="category",
                operator="eq",
                value="test"
            )
            
            vector_search_request = VectorSearchRequest(
                query="test query with filters",
                filters=[filter_condition],
                limit=5,
                search_type="SEMANTIC"
            )
            
            request = RetrieveRequest(
                vectorsearch_request=vector_search_request
            )
            
            # Mock the vector search client
            with patch.object(VectorSearchClient, 'retrieve', return_value=mock_search_response) as mock_retrieve:
                
                # Call the controller
                response = RetrieveController.retrieve(request)
                
                # Verify the response
                assert isinstance(response, RetrieveResponse), "Response should be RetrieveResponse"
                assert response.vectorsearch_results is not None, "Response should have vectorsearch_results"
                
                # Verify that the vector search client was called with the correct request
                mock_retrieve.assert_called_once()
                call_args = mock_retrieve.call_args[0][0]
                assert len(call_args.filters) == 1, "Should have one filter"
                assert call_args.filters[0].field == "category", "Filter field should be 'category'"
                assert call_args.filters[0].operator == "eq", "Filter operator should be 'eq'"
                assert call_args.filters[0].value == "test", "Filter value should be 'test'"
                
                print(f"✅ Retrieval Gateway retrieve with filters test passed!")
                
        except ImportError as e:
            pytest.skip(f"Retrieval Gateway controller not available: {e}")
        except Exception as e:
            pytest.fail(f"Error testing Retrieval Gateway controller: {e}")
    
    def test_retrieve_with_hybrid_search(self):
        """Test the retrieve controller with hybrid search"""
        
        # Create a mock search result
        mock_result = VectorSearchResult(
            text="This is a hybrid search result",
            score=0.90,
            metadata={"source": "hybrid-test"}
        )
        
        # Create a mock search response
        mock_search_response = VectorSearchResponse(
            results=[mock_result]
        )
        
        try:
            from agentic_platform.service.retrieval_gateway.api.retrieve_controller import RetrieveController
            from agentic_platform.service.retrieval_gateway.client.vectorsearch_client import VectorSearchClient
            
            # Create a request with hybrid search
            vector_search_request = VectorSearchRequest(
                query="test query for hybrid search",
                limit=5,
                search_type="HYBRID"
            )
            
            request = RetrieveRequest(
                vectorsearch_request=vector_search_request
            )
            
            # Mock the vector search client
            with patch.object(VectorSearchClient, 'retrieve', return_value=mock_search_response) as mock_retrieve:
                
                # Call the controller
                response = RetrieveController.retrieve(request)
                
                # Verify the response
                assert isinstance(response, RetrieveResponse), "Response should be RetrieveResponse"
                assert response.vectorsearch_results is not None, "Response should have vectorsearch_results"
                
                # Verify that the vector search client was called with the correct request
                mock_retrieve.assert_called_once()
                call_args = mock_retrieve.call_args[0][0]
                assert call_args.search_type == "HYBRID", "Search type should be 'HYBRID'"
                
                print(f"✅ Retrieval Gateway retrieve with hybrid search test passed!")
                
        except ImportError as e:
            pytest.skip(f"Retrieval Gateway controller not available: {e}")
        except Exception as e:
            pytest.fail(f"Error testing Retrieval Gateway controller: {e}")
    
    def test_retrieve_with_custom_limit(self):
        """Test the retrieve controller with custom result limit"""
        
        # Create mock search results
        mock_results = [
            VectorSearchResult(
                text=f"This is result {i}",
                score=0.95 - (i * 0.05),
                metadata={"index": i}
            )
            for i in range(3)
        ]
        
        # Create a mock search response
        mock_search_response = VectorSearchResponse(
            results=mock_results
        )
        
        try:
            from agentic_platform.service.retrieval_gateway.api.retrieve_controller import RetrieveController
            from agentic_platform.service.retrieval_gateway.client.vectorsearch_client import VectorSearchClient
            
            # Create a request with a custom limit
            custom_limit = 3
            vector_search_request = VectorSearchRequest(
                query="test query with custom limit",
                limit=custom_limit,
                search_type="SEMANTIC"
            )
            
            request = RetrieveRequest(
                vectorsearch_request=vector_search_request
            )
            
            # Mock the vector search client
            with patch.object(VectorSearchClient, 'retrieve', return_value=mock_search_response) as mock_retrieve:
                
                # Call the controller
                response = RetrieveController.retrieve(request)
                
                # Verify the response
                assert isinstance(response, RetrieveResponse), "Response should be RetrieveResponse"
                assert response.vectorsearch_results is not None, "Response should have vectorsearch_results"
                
                # Verify results structure
                search_results = response.vectorsearch_results.results
                assert isinstance(search_results, list), "results should be a list"
                
                # The number of results should match our mock
                assert len(search_results) == custom_limit, f"Should have {custom_limit} results"
                
                # Verify that the vector search client was called with the correct request
                mock_retrieve.assert_called_once()
                call_args = mock_retrieve.call_args[0][0]
                assert call_args.limit == custom_limit, f"Limit should be {custom_limit}"
                
                print(f"✅ Retrieval Gateway retrieve with custom limit test passed!")
                print(f"   Retrieved {len(search_results)} results with limit {custom_limit}")
                
        except ImportError as e:
            pytest.skip(f"Retrieval Gateway controller not available: {e}")
        except Exception as e:
            pytest.fail(f"Error testing Retrieval Gateway controller: {e}")
