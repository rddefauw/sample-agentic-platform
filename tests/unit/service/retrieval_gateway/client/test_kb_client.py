import pytest
from unittest.mock import patch, MagicMock
import os

from agentic_platform.service.retrieval_gateway.client.kb_client import BedrockKnowledgeBaseClient
from agentic_platform.core.models.vectordb_models import (
    VectorSearchRequest, 
    VectorSearchResponse, 
    VectorSearchResult,
    FilterCondition
)


class TestBedrockKnowledgeBaseClient:
    """Test BedrockKnowledgeBaseClient - Bedrock Knowledge Base integration with pagination"""
    
    @patch('agentic_platform.service.retrieval_gateway.client.kb_client.bedrock_client')
    def test_retrieve_success_single_page(self, mock_bedrock_client):
        """Test successful retrieval with single page of results"""
        # Setup mock Bedrock response
        mock_response = {
            'retrievalResults': [
                {
                    'content': {'text': 'Machine learning overview'},
                    'score': 0.9,
                    'metadata': {'source': 'ml_guide.pdf'},
                    'location': {'uri': 's3://bucket/ml_guide.pdf'}
                }
            ],
            'guardrailAction': None
        }
        mock_bedrock_client.retrieve.return_value = mock_response
        
        # Create request
        request = VectorSearchRequest(
            query="What is machine learning?",
            limit=5
        )
        
        # Call client
        result = BedrockKnowledgeBaseClient.retrieve(request)
        
        # Verify Bedrock was called with correct parameters
        mock_bedrock_client.retrieve.assert_called_once()
        call_kwargs = mock_bedrock_client.retrieve.call_args[1]
        
        assert call_kwargs['knowledgeBaseId'] == os.getenv("KNOWLEDGE_BASE_ID")
        assert call_kwargs['retrievalQuery']['text'] == "What is machine learning?"
        
        # Verify response structure
        assert isinstance(result, VectorSearchResponse)
        assert len(result.results) == 1
        assert result.results[0].text == 'Machine learning overview'
        assert result.results[0].score == 0.9
        assert result.results[0].metadata == {'source': 'ml_guide.pdf'}
        assert result.results[0].source_location == {'uri': 's3://bucket/ml_guide.pdf'}
    
    @patch('agentic_platform.service.retrieval_gateway.client.kb_client.bedrock_client')
    def test_retrieve_with_pagination(self, mock_bedrock_client):
        """Test retrieval with multiple pages of results"""
        # Setup mock responses for pagination
        first_response = {
            'retrievalResults': [
                {
                    'content': {'text': 'First result'},
                    'score': 0.9,
                    'metadata': {},
                    'location': {}
                },
                {
                    'content': {'text': 'Second result'},
                    'score': 0.8,
                    'metadata': {},
                    'location': {}
                }
            ],
            'nextToken': 'page2_token'
        }
        
        second_response = {
            'retrievalResults': [
                {
                    'content': {'text': 'Third result'},
                    'score': 0.7,
                    'metadata': {},
                    'location': {}
                }
            ]
            # No nextToken indicates end of results
        }
        
        # Configure mock to return different responses on sequential calls
        mock_bedrock_client.retrieve.side_effect = [first_response, second_response]
        
        # Create request for 3 results
        request = VectorSearchRequest(
            query="test query",
            limit=3
        )
        
        # Call client
        result = BedrockKnowledgeBaseClient.retrieve(request)
        
        # Verify both Bedrock calls were made
        assert mock_bedrock_client.retrieve.call_count == 2
        
        # Verify first call
        first_call_kwargs = mock_bedrock_client.retrieve.call_args_list[0][1]
        assert 'nextToken' not in first_call_kwargs
        
        # Verify second call includes nextToken
        second_call_kwargs = mock_bedrock_client.retrieve.call_args_list[1][1]
        assert second_call_kwargs['nextToken'] == 'page2_token'
        
        # Verify combined results
        assert len(result.results) == 3
        assert result.results[0].text == 'First result'
        assert result.results[1].text == 'Second result'
        assert result.results[2].text == 'Third result'
        
        # Verify scores are preserved
        assert result.results[0].score == 0.9
        assert result.results[1].score == 0.8
        assert result.results[2].score == 0.7
    
    @patch('agentic_platform.service.retrieval_gateway.client.kb_client.bedrock_client')
    def test_retrieve_respects_limit(self, mock_bedrock_client):
        """Test that retrieval respects the requested limit"""
        # Setup mock response with more results than requested
        mock_response = {
            'retrievalResults': [
                {'content': {'text': f'Result {i}'}, 'score': 0.9 - i*0.1, 'metadata': {}, 'location': {}}
                for i in range(10)  # 10 results returned
            ]
        }
        mock_bedrock_client.retrieve.return_value = mock_response
        
        # Request only 3 results
        request = VectorSearchRequest(
            query="test query",
            limit=3
        )
        
        # Call client
        result = BedrockKnowledgeBaseClient.retrieve(request)
        
        # Verify only 3 results are returned
        assert len(result.results) == 3
        assert result.results[0].text == 'Result 0'
        assert result.results[1].text == 'Result 1'
        assert result.results[2].text == 'Result 2'
    
    @patch('agentic_platform.service.retrieval_gateway.client.kb_client.bedrock_client')
    def test_retrieve_with_filters_single(self, mock_bedrock_client):
        """Test retrieval with a single filter"""
        mock_response = {'retrievalResults': []}
        mock_bedrock_client.retrieve.return_value = mock_response
        
        # Create request with single filter
        filters = [FilterCondition(field="category", operator="eq", value="technical")]
        request = VectorSearchRequest(
            query="filtered query",
            limit=5,
            filters=filters
        )
        
        # Call client
        BedrockKnowledgeBaseClient.retrieve(request)
        
        # Verify filter was converted correctly
        call_kwargs = mock_bedrock_client.retrieve.call_args[1]
        filter_config = call_kwargs['retrievalConfiguration']['vectorSearchConfiguration']['filter']
        
        assert 'equals' in filter_config
        assert filter_config['equals']['key'] == 'category'
        assert filter_config['equals']['value'] == 'technical'
    
    @patch('agentic_platform.service.retrieval_gateway.client.kb_client.bedrock_client')
    def test_retrieve_with_filters_multiple(self, mock_bedrock_client):
        """Test retrieval with multiple filters"""
        mock_response = {'retrievalResults': []}
        mock_bedrock_client.retrieve.return_value = mock_response
        
        # Create request with multiple filters
        filters = [
            FilterCondition(field="category", operator="eq", value="technical"),
            FilterCondition(field="year", operator="gte", value="2020")
        ]
        request = VectorSearchRequest(
            query="filtered query",
            limit=5,
            filters=filters
        )
        
        # Call client
        BedrockKnowledgeBaseClient.retrieve(request)
        
        # Verify filters were combined with andAll
        call_kwargs = mock_bedrock_client.retrieve.call_args[1]
        filter_config = call_kwargs['retrievalConfiguration']['vectorSearchConfiguration']['filter']
        
        assert 'andAll' in filter_config
        assert len(filter_config['andAll']) == 2
        
        # Check first filter
        first_filter = filter_config['andAll'][0]
        assert 'equals' in first_filter
        assert first_filter['equals']['key'] == 'category'
        assert first_filter['equals']['value'] == 'technical'
        
        # Check second filter
        second_filter = filter_config['andAll'][1]
        assert 'greaterThanOrEquals' in second_filter
        assert second_filter['greaterThanOrEquals']['key'] == 'year'
        assert second_filter['greaterThanOrEquals']['value'] == '2020'
    
    def test_map_operator_conversions(self):
        """Test operator mapping from generic to Bedrock format"""
        # Test all supported operators
        test_cases = [
            ("eq", "equals"),
            ("neq", "notEquals"),
            ("gt", "greaterThan"),
            ("gte", "greaterThanOrEquals"),
            ("lt", "lessThan"),
            ("lte", "lessThanOrEquals"),
            ("contains", "stringContains"),
            ("starts_with", "startsWith"),
            ("in", "in"),
            ("not_in", "notIn")
        ]
        
        for generic_op, bedrock_op in test_cases:
            result = BedrockKnowledgeBaseClient._map_operator(generic_op)
            assert result == bedrock_op
        
        # Test unknown operator passthrough
        result = BedrockKnowledgeBaseClient._map_operator("unknown_op")
        assert result == "unknown_op"
    
    @patch('agentic_platform.service.retrieval_gateway.client.kb_client.bedrock_client')
    def test_retrieve_with_search_type(self, mock_bedrock_client):
        """Test retrieval with specific search type"""
        mock_response = {'retrievalResults': []}
        mock_bedrock_client.retrieve.return_value = mock_response
        
        # Create request with search type
        request = VectorSearchRequest(
            query="hybrid search",
            limit=5,
            search_type="HYBRID"
        )
        
        # Call client
        BedrockKnowledgeBaseClient.retrieve(request)
        
        # Verify search type was included
        call_kwargs = mock_bedrock_client.retrieve.call_args[1]
        vector_config = call_kwargs['retrievalConfiguration']['vectorSearchConfiguration']
        assert vector_config['overrideSearchType'] == 'HYBRID'
    
    def test_convert_result_text_content(self):
        """Test result conversion for text content"""
        # Test with text content
        bedrock_item = {
            'content': {'text': 'Sample document text'},
            'score': 0.85,
            'metadata': {'source': 'doc.pdf'},
            'location': {'uri': 's3://bucket/doc.pdf'}
        }
        
        result = BedrockKnowledgeBaseClient._convert_result(bedrock_item)
        
        assert isinstance(result, VectorSearchResult)
        assert result.text == 'Sample document text'
        assert result.score == 0.85
        assert result.metadata == {'source': 'doc.pdf'}
        assert result.source_location == {'uri': 's3://bucket/doc.pdf'}
        assert result.content_type is None  # Not specified in input
    
    def test_convert_result_binary_content(self):
        """Test result conversion for binary content"""
        # Test with binary content
        bedrock_item = {
            'content': {'byteContent': b'binary_data', 'type': 'application/pdf'},
            'score': 0.75,
            'metadata': {},
            'location': {}
        }
        
        result = BedrockKnowledgeBaseClient._convert_result(bedrock_item)
        
        assert result.text == '[Binary content]'
        assert result.score == 0.75
        assert result.content_type == 'application/pdf'
    
    def test_convert_result_row_content(self):
        """Test result conversion for row/tabular content"""
        # Test with row content
        bedrock_item = {
            'content': {
                'row': [
                    {'columnName': 'title', 'columnValue': 'Document Title'},
                    {'columnName': 'author', 'columnValue': 'John Doe'}
                ]
            },
            'score': 0.8,
            'metadata': {},
            'location': {}
        }
        
        result = BedrockKnowledgeBaseClient._convert_result(bedrock_item)
        
        expected_text = 'title: Document Title | author: John Doe'
        assert result.text == expected_text
        assert result.score == 0.8
    
    def test_convert_result_minimal(self):
        """Test result conversion with minimal data"""
        # Test with minimal data
        bedrock_item = {
            'content': {},
            # Missing score, metadata, location
        }
        
        result = BedrockKnowledgeBaseClient._convert_result(bedrock_item)
        
        assert result.text == ''
        assert result.score == 0.0
        assert result.metadata == {}
        assert result.source_location == {}
        assert result.content_type is None
    
    @patch('agentic_platform.service.retrieval_gateway.client.kb_client.bedrock_client')
    def test_retrieve_empty_results(self, mock_bedrock_client):
        """Test retrieval with no results"""
        mock_response = {
            'retrievalResults': [],
            'guardrailAction': None
        }
        mock_bedrock_client.retrieve.return_value = mock_response
        
        request = VectorSearchRequest(query="no matches", limit=5)
        result = BedrockKnowledgeBaseClient.retrieve(request)
        
        assert len(result.results) == 0
        assert result.guardrail_action is None
    
    @patch('agentic_platform.service.retrieval_gateway.client.kb_client.bedrock_client')
    def test_retrieve_with_guardrail_action(self, mock_bedrock_client):
        """Test retrieval with guardrail action"""
        mock_response = {
            'retrievalResults': [],
            'guardrailAction': 'ABSTAINED'
        }
        mock_bedrock_client.retrieve.return_value = mock_response
        
        request = VectorSearchRequest(query="sensitive query", limit=5)
        result = BedrockKnowledgeBaseClient.retrieve(request)
        
        assert result.guardrail_action == 'ABSTAINED'
    
    @patch('agentic_platform.service.retrieval_gateway.client.kb_client.bedrock_client')
    def test_retrieve_propagates_exceptions(self, mock_bedrock_client):
        """Test that Bedrock exceptions are propagated"""
        from botocore.exceptions import ClientError
        
        # Setup Bedrock to raise exception
        error_response = {
            'Error': {
                'Code': 'ResourceNotFoundException',
                'Message': 'Knowledge base not found'
            }
        }
        mock_bedrock_client.retrieve.side_effect = ClientError(error_response, 'Retrieve')
        
        request = VectorSearchRequest(query="test", limit=5)
        
        with pytest.raises(ClientError):
            BedrockKnowledgeBaseClient.retrieve(request)
    
    @patch('agentic_platform.service.retrieval_gateway.client.kb_client.bedrock_client')
    @patch('builtins.print')  # Mock print to avoid console output during tests
    def test_retrieve_prints_debug_info(self, mock_print, mock_bedrock_client):
        """Test that debugging print statements are called"""
        mock_response = {
            'retrievalResults': [
                {'content': {'text': 'test'}, 'score': 0.8, 'metadata': {}, 'location': {}}
            ]
        }
        mock_bedrock_client.retrieve.return_value = mock_response
        
        request = VectorSearchRequest(query="test", limit=5)
        BedrockKnowledgeBaseClient.retrieve(request)
        
        # Verify print statements were called (for debugging)
        assert mock_print.call_count >= 2  # At least "Results:" and "All results:" prints
    
    # Removed class structure test - tests Python class definition, not functionality 