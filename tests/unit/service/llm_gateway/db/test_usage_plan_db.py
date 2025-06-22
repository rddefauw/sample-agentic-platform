import pytest
from unittest.mock import patch, MagicMock
import hashlib
from typing import Dict, List, Any

from agentic_platform.service.llm_gateway.db.usage_plan_db import UsagePlanDB
from agentic_platform.service.llm_gateway.models.usage_types import UsagePlan, UsagePlanEntityType


class TestUsagePlanDB:
    """Test UsagePlanDB - DynamoDB interface for usage plan management"""
    
    def test_hash_key_consistency(self):
        """Test that hash_key produces consistent results"""
        key = "this-is-a-test" # gitleaks:allow
        
        # Hash the key multiple times
        hash1 = UsagePlanDB.hash_key(key)
        hash2 = UsagePlanDB.hash_key(key)
        
        # Should be identical
        assert hash1 == hash2
        
        # Should be SHA256 hex digest
        expected = hashlib.sha256(key.encode()).hexdigest()
        assert hash1 == expected
        
        # Should be 64 characters long (SHA256 hex)
        assert len(hash1) == 64
    
    def test_hash_key_different_inputs(self):
        """Test that different keys produce different hashes"""
        key1 = "api-key-1"
        key2 = "api-key-2"
        
        hash1 = UsagePlanDB.hash_key(key1)
        hash2 = UsagePlanDB.hash_key(key2)
        
        # Should be different
        assert hash1 != hash2
    
    def test_to_dynamo_item_conversion(self):
        """Test conversion from UsagePlan to DynamoDB item"""
        plan = UsagePlan(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["test-model"],
            tenant_id="test-tenant",
            active=True
        )
        
        item = UsagePlanDB._to_dynamo_item(plan)
        
        # Verify basic fields
        assert item['entity_id'] == "test-entity"
        assert item['tenant_id'] == "test-tenant"
        assert item['active'] is True
        assert 'model_permissions' in item
        
        # Verify entity_type is converted to string
        assert item["entity_type"] == str(UsagePlanEntityType.USER)
        assert isinstance(item['entity_type'], str)
    
    def test_from_dynamo_item_conversion(self):
        """Test conversion from DynamoDB item to UsagePlan"""
        item = {
            'entity_id': 'test-entity',
            'entity_type': 'SERVICE',
            'model_permissions': ['test-model'],
            'tenant_id': 'test-tenant',
            'active': True
        }
        
        plan = UsagePlanDB._from_dynamo_item(item)
        
        # Verify conversion
        assert isinstance(plan, UsagePlan)
        assert plan.entity_id == "test-entity"
        assert plan.entity_type == UsagePlanEntityType.SERVICE
        assert plan.model_permissions == ['test-model']
        assert plan.tenant_id == "test-tenant"
        assert plan.active is True
    
    def test_from_dynamo_item_with_minimal_fields(self):
        """Test conversion from DynamoDB item with minimal required fields"""
        item = {
            'entity_id': 'test-entity',
            'entity_type': 'USER',
            'model_permissions': ['test-model']
        }
        
        # Should work with minimal required fields
        plan = UsagePlanDB._from_dynamo_item(item)
        assert isinstance(plan, UsagePlan)
        assert plan.entity_id == "test-entity"
        assert plan.entity_type == UsagePlanEntityType.USER
    
    @patch('agentic_platform.service.llm_gateway.db.usage_plan_db.plans_table')
    def test_get_plan_by_id_success(self, mock_table):
        """Test successful plan retrieval by ID"""
        # Setup mock response
        mock_item = {
            'entity_id': 'test-entity',
            'entity_type': 'USER',
            'model_permissions': ['test-model'],
            'active': True
        }
        mock_table.get_item.return_value = {'Item': mock_item}
        
        # Call method
        result = UsagePlanDB.get_plan_by_id("test-entity", UsagePlanEntityType.USER)
        
        # Verify DynamoDB call
        mock_table.get_item.assert_called_once_with(
            Key={
                'entity_id': 'test-entity',
                'entity_type': str(UsagePlanEntityType.USER)
            }
        )
        
        # Verify result
        assert isinstance(result, UsagePlan)
        assert result.entity_id == "test-entity"
        assert result.entity_type == UsagePlanEntityType.USER
    
    @patch('agentic_platform.service.llm_gateway.db.usage_plan_db.plans_table')
    def test_get_plan_by_id_api_key_hashing(self, mock_table):
        """Test plan retrieval with API key hashing"""
        # Setup mock response
        mock_table.get_item.return_value = {'Item': {
            'entity_id': 'hashed-key',
            'entity_type': 'API_KEY',
            'model_permissions': ['test-model']
        }}
        
        # Call method with raw API key
        UsagePlanDB.get_plan_by_id("raw-api-key", UsagePlanEntityType.API_KEY)
        
        # Verify key was hashed
        expected_hash = hashlib.sha256("raw-api-key".encode()).hexdigest()
        mock_table.get_item.assert_called_once_with(
            Key={
                'entity_id': expected_hash,
                'entity_type': str(UsagePlanEntityType.API_KEY)
            }
        )
    
    @patch('agentic_platform.service.llm_gateway.db.usage_plan_db.plans_table')
    def test_get_plan_by_id_not_found(self, mock_table):
        """Test plan retrieval when plan doesn't exist"""
        # Setup mock response - no item
        mock_table.get_item.return_value = {}
        
        # Call method
        result = UsagePlanDB.get_plan_by_id("nonexistent", UsagePlanEntityType.USER)
        
        # Verify result
        assert result is None
    
    @patch('agentic_platform.service.llm_gateway.db.usage_plan_db.plans_table')
    def test_get_plan_by_id_exception(self, mock_table):
        """Test plan retrieval with DynamoDB exception"""
        # Setup mock to raise exception
        mock_table.get_item.side_effect = Exception("DynamoDB error")
        
        # Call method
        result = UsagePlanDB.get_plan_by_id("test-entity", UsagePlanEntityType.USER)
        
        # Verify result is None on exception
        assert result is None
    
    @patch('agentic_platform.service.llm_gateway.db.usage_plan_db.plans_table')
    def test_create_plan_success(self, mock_table):
        """Test successful plan creation"""
        # Setup mock
        mock_table.put_item.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        
        # Create plan
        plan = UsagePlan(
            entity_id="new-entity",
            entity_type=UsagePlanEntityType.SERVICE,
            model_permissions=["test-model"],
            tenant_id="test-tenant"
        )
        
        # Call method
        result = UsagePlanDB.create_plan(plan)
        
        # Verify DynamoDB call
        mock_table.put_item.assert_called_once()
        put_args = mock_table.put_item.call_args[1]
        
        # Verify item structure
        item = put_args['Item']
        assert item['entity_id'] == "new-entity"
        assert item["entity_type"] == str(UsagePlanEntityType.SERVICE)
        assert 'model_permissions' in item
        
        # Verify success
        assert result is True
    
    @patch('agentic_platform.service.llm_gateway.db.usage_plan_db.plans_table')
    def test_create_plan_api_key_hashing(self, mock_table):
        """Test plan creation with API key hashing"""
        # Setup mock
        mock_table.put_item.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        
        # Create API key plan
        plan = UsagePlan(
            entity_id="raw-api-key",
            entity_type=UsagePlanEntityType.API_KEY,
            model_permissions=["test-model"]
        )
        
        # Call method
        result = UsagePlanDB.create_plan(plan)
        
        # Verify entity_id was hashed
        put_args = mock_table.put_item.call_args[1]
        item = put_args['Item']
        expected_hash = hashlib.sha256("raw-api-key".encode()).hexdigest()
        assert item['entity_id'] == expected_hash
        
        # Verify original plan is unchanged
        assert plan.entity_id == "raw-api-key"  # Original should not be modified
        
        # Verify success
        assert result is True
    
    @patch('agentic_platform.service.llm_gateway.db.usage_plan_db.plans_table')
    def test_create_plan_failure(self, mock_table):
        """Test plan creation failure"""
        # Setup mock to raise exception
        mock_table.put_item.side_effect = Exception("DynamoDB error")
        
        # Create plan
        plan = UsagePlan(
            entity_id="failing-entity",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["test-model"]
        )
        
        # Call method
        result = UsagePlanDB.create_plan(plan)
        
        # Verify failure
        assert result is False
    
    @patch('agentic_platform.service.llm_gateway.db.usage_plan_db.plans_table')
    @pytest.mark.asyncio
    async def test_deactivate_plan_success(self, mock_table):
        """Test successful plan deactivation"""
        # Setup mock
        mock_table.update_item.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        
        # Call method
        result = await UsagePlanDB.deactivate_plan("test-entity", UsagePlanEntityType.USER)
        
        # Verify DynamoDB call
        mock_table.update_item.assert_called_once_with(
            Key={
                'entity_id': 'test-entity',
                'entity_type': str(UsagePlanEntityType.USER)
            },
            UpdateExpression='SET active = :false',
            ExpressionAttributeValues={':false': False}
        )
        
        # Verify success
        assert result is True
    
    @patch('agentic_platform.service.llm_gateway.db.usage_plan_db.plans_table')
    @pytest.mark.asyncio
    async def test_deactivate_plan_failure(self, mock_table):
        """Test plan deactivation failure"""
        # Setup mock to raise exception
        mock_table.update_item.side_effect = Exception("DynamoDB error")
        
        # Call method
        result = await UsagePlanDB.deactivate_plan("test-entity", UsagePlanEntityType.USER)
        
        # Verify failure
        assert result is False
    
    @patch('agentic_platform.service.llm_gateway.db.usage_plan_db.plans_table')
    def test_get_plans_by_tenant_success(self, mock_table):
        """Test successful retrieval of plans by tenant"""
        # Setup mock response
        mock_items = [
            {
                'entity_id': 'entity1',
                'entity_type': 'API_KEY',
                'model_permissions': ['test-model'],
                'tenant_id': 'test-tenant'
            },
            {
                'entity_id': 'entity2',
                'entity_type': 'USER',
                'model_permissions': ['test-model'],
                'tenant_id': 'test-tenant'
            }
        ]
        mock_table.query.return_value = {'Items': mock_items}
        
        # Call method
        result = UsagePlanDB.get_plans_by_tenant("test-tenant")
        
        # Verify DynamoDB call
        mock_table.query.assert_called_once_with(
            IndexName='tenant_index',
            KeyConditionExpression='tenant_id = :tid',
            ExpressionAttributeValues={':tid': 'test-tenant'}
        )
        
        # Verify results
        assert len(result) == 2
        assert all(isinstance(plan, UsagePlan) for plan in result)
        assert result[0].entity_id == "entity1"
        assert result[1].entity_id == "entity2"
    
    @patch('agentic_platform.service.llm_gateway.db.usage_plan_db.plans_table')
    def test_get_plans_by_tenant_empty(self, mock_table):
        """Test retrieval of plans by tenant with no results"""
        # Setup mock response - no items
        mock_table.query.return_value = {}
        
        # Call method
        result = UsagePlanDB.get_plans_by_tenant("empty-tenant")
        
        # Verify result
        assert result == []
        assert isinstance(result, list)
    
    @patch('agentic_platform.service.llm_gateway.db.usage_plan_db.plans_table')
    def test_get_plans_by_tenant_exception(self, mock_table):
        """Test retrieval of plans by tenant with exception"""
        # Setup mock to raise exception
        mock_table.query.side_effect = Exception("DynamoDB error")
        
        # Call method
        result = UsagePlanDB.get_plans_by_tenant("test-tenant")
        
        # Verify result is empty list on exception
        assert result == []
    
    def test_usage_plan_db_class_structure(self):
        """Test the UsagePlanDB class structure"""
        # Should have expected methods
        expected_methods = [
            'hash_key',
            'get_plan_by_id',
            'create_plan',
            'deactivate_plan',
            'get_plans_by_tenant'
        ]
        
        for method in expected_methods:
            assert hasattr(UsagePlanDB, method)
            assert callable(getattr(UsagePlanDB, method))
        
        # Should have private conversion methods
        assert hasattr(UsagePlanDB, '_to_dynamo_item')
        assert hasattr(UsagePlanDB, '_from_dynamo_item')
    
    def test_deactivate_plan_is_async(self):
        """Test that deactivate_plan is async"""
        import inspect
        
        method = getattr(UsagePlanDB, 'deactivate_plan')
        assert inspect.iscoroutinefunction(method)
    
    def test_other_methods_are_sync(self):
        """Test that other methods are synchronous"""
        import inspect
        
        sync_methods = [
            'hash_key',
            'get_plan_by_id',
            'create_plan',
            'get_plans_by_tenant',
            '_to_dynamo_item',
            '_from_dynamo_item'
        ]
        
        for method_name in sync_methods:
            method = getattr(UsagePlanDB, method_name)
            assert not inspect.iscoroutinefunction(method), f"{method_name} should be sync"
    
    def test_dynamodb_initialization(self):
        """Test that DynamoDB resources are properly initialized"""
        # Import should trigger resource creation
        from agentic_platform.service.llm_gateway.db import usage_plan_db
        
        # Should have plans_table available
        assert hasattr(usage_plan_db, 'plans_table')
        assert usage_plan_db.plans_table is not None 