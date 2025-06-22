import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import time

from agentic_platform.service.llm_gateway.client.usage_client import UsageClient
from agentic_platform.service.llm_gateway.models.usage_types import UsageRecord


class TestUsageClient:
    """Test UsageClient - handles usage record persistence"""
    
    def test_to_dynamo_item_conversion(self):
        """Test converting UsageRecord to DynamoDB item format"""
        timestamp = int(time.time())
        record = UsageRecord(
            tenant_id="test-tenant",
            model="test-model",
            input_tokens=100,
            output_tokens=50,
            timestamp=timestamp
        )
        
        item = UsageClient._to_dynamo_item(record)
        
        # Verify all fields are present
        assert item['tenant_id'] == "test-tenant"
        assert item['model'] == "test-model"
        assert item['input_tokens'] == 100
        assert item['output_tokens'] == 50
        assert item['total_tokens'] == 150  # Calculated
        assert item['timestamp'] == timestamp
        assert 'usage_id' in item  # Auto-generated
        assert 'ttl' in item  # Auto-generated
    
    def test_from_dynamo_item_conversion(self):
        """Test converting DynamoDB item to UsageRecord"""
        timestamp = int(time.time())
        item = {
            'usage_id': 'test-usage-id',
            'tenant_id': 'test-tenant',
            'model': 'test-model',
            'input_tokens': 200,
            'output_tokens': 100,
            'total_tokens': 300,
            'timestamp': timestamp,
            'metadata': {}
        }
        
        record = UsageClient._from_dynamo_item(item)
        
        # Verify conversion
        assert isinstance(record, UsageRecord)
        assert record.tenant_id == "test-tenant"
        assert record.model == "test-model"
        assert record.input_tokens == 200
        assert record.output_tokens == 100
        assert record.timestamp == timestamp
    
    @patch('agentic_platform.service.llm_gateway.client.usage_client.usage_table')
    @pytest.mark.asyncio
    async def test_record_usage_success(self, mock_table):
        """Test successful usage recording"""
        # Setup mock
        mock_table.put_item.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        
        record = UsageRecord(
            tenant_id="test-tenant",
            model="test-model",
            input_tokens=80,
            output_tokens=40
        )
        
        result = await UsageClient.record_usage(record)
        
        # Verify DynamoDB call
        mock_table.put_item.assert_called_once()
        call_args = mock_table.put_item.call_args
        item = call_args[1]['Item']
        assert item['tenant_id'] == "test-tenant"
        assert item['model'] == "test-model"
        assert item['input_tokens'] == 80
        assert item['output_tokens'] == 40
        assert item['total_tokens'] == 120
        
        assert result is True
    
    @patch('agentic_platform.service.llm_gateway.client.usage_client.usage_table')
    @pytest.mark.asyncio
    async def test_record_usage_failure(self, mock_table):
        """Test usage recording failure"""
        # Setup mock to raise exception
        mock_table.put_item.side_effect = Exception("DynamoDB error")
        
        record = UsageRecord(
            tenant_id="test-tenant",
            model="test-model",
            input_tokens=60,
            output_tokens=30
        )
        
        result = await UsageClient.record_usage(record)
        
        # Should handle error gracefully
        assert result is False
    
    def test_record_usage_method_signature(self):
        """Test the record_usage method signature"""
        import inspect
        
        method = getattr(UsageClient, 'record_usage')
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())
        
        # Should have record parameter (classmethod with bound cls)
        assert 'record' in params
        
        # Should be an async method
        assert inspect.iscoroutinefunction(method)
    
    def test_get_usage_method_signature(self):
        """Test the get_usage method signature"""
        import inspect
        
        method = getattr(UsageClient, 'get_usage')
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())
        
        # Should have tenant_id, start_time, end_time parameters (classmethod with bound cls)
        assert 'tenant_id' in params
        assert 'start_time' in params
        assert 'end_time' in params
        
        # Should be an async method
        assert inspect.iscoroutinefunction(method)
    
    def test_usage_id_generation(self):
        """Test that usage_id is generated for records"""
        record = UsageRecord(
            tenant_id="test-tenant",
            model="test-model",
            input_tokens=100,
            output_tokens=50
        )
        
        # Convert to DynamoDB item format
        item = UsageClient._to_dynamo_item(record)
        
        # Should have auto-generated usage_id
        assert 'usage_id' in item
        assert isinstance(item['usage_id'], str)
        assert len(item['usage_id']) > 0
    
    def test_dynamodb_initialization(self):
        """Test DynamoDB table initialization"""
        # This test verifies the table setup works
        from agentic_platform.service.llm_gateway.client.usage_client import usage_table
        
        # Should be able to access table
        assert usage_table is not None
        assert hasattr(usage_table, 'put_item')
    
    @patch('agentic_platform.service.llm_gateway.client.usage_client.usage_table')
    @pytest.mark.asyncio
    async def test_get_usage_success(self, mock_table):
        """Test successful usage retrieval"""
        # Setup mock response
        timestamp = int(time.time())
        mock_response = {
            'Items': [
                {
                    'usage_id': 'usage-1',
                    'tenant_id': 'test-tenant',
                    'model': 'test-model',
                    'input_tokens': 100,
                    'output_tokens': 50,
                    'total_tokens': 150,
                    'timestamp': timestamp,
                    'metadata': {}
                },
                {
                    'usage_id': 'usage-2', 
                    'tenant_id': 'test-tenant',
                    'model': 'test-model2',
                    'input_tokens': 200,
                    'output_tokens': 100,
                    'total_tokens': 300,
                    'timestamp': timestamp + 1,
                    'metadata': {}
                }
            ]
        }
        mock_table.query.return_value = mock_response
        
        start_time = timestamp - 100
        end_time = timestamp + 100
        
        records = await UsageClient.get_usage("test-tenant", start_time, end_time)
        
        # Verify query was called
        mock_table.query.assert_called_once()
        
        # Verify results
        assert len(records) == 2
        assert all(isinstance(r, UsageRecord) for r in records)
        assert records[0].tenant_id == "test-tenant"
        assert records[1].tenant_id == "test-tenant"
    
    def test_timestamp_formatting(self):
        """Test that timestamps are formatted correctly"""
        timestamp = int(time.time())
        record = UsageRecord(
            tenant_id="test-tenant",
            model="test-model", 
            input_tokens=100,
            output_tokens=50,
            timestamp=timestamp
        )
        
        item = UsageClient._to_dynamo_item(record)
        
        # Should have integer timestamp
        assert 'timestamp' in item
        assert item['timestamp'] == timestamp
        assert isinstance(item['timestamp'], int)
    
    def test_usage_client_class_structure(self):
        """Test the UsageClient class structure"""
        # Should have expected methods
        expected_methods = [
            '_to_dynamo_item',
            '_from_dynamo_item', 
            'record_usage',
            'get_usage'
        ]
        
        for method in expected_methods:
            assert hasattr(UsageClient, method)
            assert callable(getattr(UsageClient, method))
    
    def test_total_tokens_calculation(self):
        """Test that total tokens are calculated correctly"""
        record = UsageRecord(
            tenant_id="test-tenant",
            model="test-model",
            input_tokens=150,
            output_tokens=75
        )
        
        item = UsageClient._to_dynamo_item(record)
        
        # total_tokens should be sum of input and output
        assert item['total_tokens'] == 225
    
    def test_ttl_calculation(self):
        """Test that TTL is calculated correctly"""
        timestamp = int(time.time())
        record = UsageRecord(
            tenant_id="test-tenant",
            model="test-model",
            input_tokens=100,
            output_tokens=50,
            timestamp=timestamp
        )
        
        item = UsageClient._to_dynamo_item(record)
        
        # TTL should be timestamp + 30 days
        expected_ttl = timestamp + (30 * 24 * 60 * 60)
        assert item['ttl'] == expected_ttl 