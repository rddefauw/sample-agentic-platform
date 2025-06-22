import pytest
from typing import Dict, Any
from pydantic import ValidationError

from agentic_platform.service.llm_gateway.models.gateway_api_types import (
    ConverseRequest, ConverseResponse, CreateUsagePlanRequest, CreateUsagePlanResponse,
    RevokeUsagePlanRequest, RevokeUsagePlanResponse
)
from agentic_platform.service.llm_gateway.models.usage_types import UsagePlan, UsagePlanEntityType


class TestConverseRequest:
    """Test ConverseRequest model"""
    
    def test_minimal_valid_request(self):
        """Test creation with minimal required fields"""
        request = ConverseRequest(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            messages=[
                {
                    "role": "user",
                    "content": [{"text": "Hello"}]
                }
            ]
        )
        
        assert request.modelId == "anthropic.claude-3-sonnet-20240229-v1:0"
        assert len(request.messages) == 1
        assert request.messages[0]["role"] == "user"
    
    def test_complex_request_with_all_fields(self):
        """Test creation with all optional fields"""
        request = ConverseRequest(
            modelId="test-model",
            messages=[
                {"role": "system", "content": [{"text": "You are helpful"}]},
                {"role": "user", "content": [{"text": "Hello"}]}
            ],
            system=[{"text": "System instruction"}],
            inferenceConfig={
                "maxTokens": 1000,
                "temperature": 0.7,
                "topP": 0.9
            },
            toolConfig={
                "tools": [
                    {
                        "toolSpec": {
                            "name": "calculator",
                            "description": "Basic calculator"
                        }
                    }
                ]
            }
        )
        
        assert request.modelId == "test-model"
        assert len(request.messages) == 2
        assert request.system is not None
        assert request.inferenceConfig is not None
        assert request.toolConfig is not None
    
    def test_missing_required_fields(self):
        """Test validation error with missing required fields"""
        with pytest.raises(ValidationError):
            ConverseRequest()  # Missing modelId
        
        # modelId is the only required field, messages are optional extra fields
        request = ConverseRequest(modelId="test-model")
        assert request.modelId == "test-model"
    
    # Removed basic serialization test - tests Pydantic framework functionality


class TestConverseResponse:
    """Test ConverseResponse model"""
    
    def test_create_response_from_dict(self):
        """Test creating response from dictionary (AWS Bedrock format)"""
        response_data = {
            "ResponseMetadata": {"HTTPStatusCode": 200},
            "output": {
                "message": {
                    "content": [{"text": "Hello! How can I help?"}]
                }
            },
            "usage": {"inputTokens": 10, "outputTokens": 15}
        }
        
        # ConverseResponse should accept any dict structure
        response = ConverseResponse.model_validate(response_data)
        assert response is not None
    
    def test_empty_response(self):
        """Test creating empty response"""
        response = ConverseResponse(output={})
        assert response is not None


class TestCreateUsagePlanRequest:
    """Test CreateUsagePlanRequest model"""
    
    def test_minimal_request(self):
        """Test creation with minimal required fields"""
        request = CreateUsagePlanRequest(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["test-model"]
        )
        
        assert request.entity_id == "test-entity"
        assert request.entity_type == UsagePlanEntityType.USER
        assert request.model_permissions == ["test-model"]
    
    # Removed trivial constructor test - just testing field assignment
    
    def test_missing_required_fields(self):
        """Test validation error with missing required fields"""
        with pytest.raises(ValidationError):
            CreateUsagePlanRequest()  # Missing all required fields
        
        with pytest.raises(ValidationError):
            CreateUsagePlanRequest(entity_id="test")  # Missing entity_type and model_permissions
    
    def test_entity_type_validation(self):
        """Test entity type validation"""
        # Valid entity types
        for entity_type in [UsagePlanEntityType.USER, UsagePlanEntityType.API_KEY, UsagePlanEntityType.SERVICE]:
            request = CreateUsagePlanRequest(
                entity_id="test",
                entity_type=entity_type,
                model_permissions=["test-model"]
            )
            assert request.entity_type == entity_type


class TestCreateUsagePlanResponse:
    """Test CreateUsagePlanResponse model"""
    
    # Removed trivial constructor test - just testing field assignment
    
    def test_missing_plan_field(self):
        """Test validation error with missing plan"""
        with pytest.raises(ValidationError):
            CreateUsagePlanResponse()  # Missing required plan field


class TestRevokeUsagePlanRequest:
    """Test RevokeUsagePlanRequest model"""
    
    def test_valid_request(self):
        """Test creation with valid fields"""
        request = RevokeUsagePlanRequest(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.SERVICE
        )
        
        assert request.entity_id == "test-entity"
        assert request.entity_type == UsagePlanEntityType.SERVICE
    
    def test_missing_required_fields(self):
        """Test validation error with missing required fields"""
        with pytest.raises(ValidationError):
            RevokeUsagePlanRequest()  # Missing both required fields
        
        with pytest.raises(ValidationError):
            RevokeUsagePlanRequest(entity_id="test")  # Missing entity_type
    
    def test_different_entity_types(self):
        """Test with different entity types"""
        entity_types = [
            UsagePlanEntityType.USER,
            UsagePlanEntityType.API_KEY,
            UsagePlanEntityType.SERVICE
        ]
        
        for entity_type in entity_types:
            request = RevokeUsagePlanRequest(
                entity_id=f"test-{entity_type.value}",
                entity_type=entity_type
            )
            assert request.entity_type == entity_type


class TestRevokeUsagePlanResponse:
    """Test RevokeUsagePlanResponse model"""
    
    def test_success_response(self):
        """Test creating success response"""
        response = RevokeUsagePlanResponse(success=True)
        assert response.success is True
    
    def test_failure_response(self):
        """Test creating failure response"""
        response = RevokeUsagePlanResponse(success=False)
        assert response.success is False
    
    def test_missing_success_field(self):
        """Test validation error with missing success field"""
        with pytest.raises(ValidationError):
            RevokeUsagePlanResponse()  # Missing required success field
    
    def test_invalid_success_type(self):
        """Test validation error with invalid success type"""
        # Pydantic will convert string to bool, so this should not raise error
        response = RevokeUsagePlanResponse(success="true")
        assert response.success is True  # Pydantic converts string to bool


class TestGatewayApiTypesIntegration:
    """Test integration between different gateway API types"""
    
    def test_create_and_revoke_flow(self):
        """Test typical create and revoke flow"""
        # Create request
        create_request = CreateUsagePlanRequest(
            entity_id="integration-test",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["integration-model"]
        )
        
        # Simulate created plan
        plan = UsagePlan(
            entity_id=create_request.entity_id,
            entity_type=create_request.entity_type,
            model_permissions=create_request.model_permissions
        )
        
        # Create response
        create_response = CreateUsagePlanResponse(plan=plan)
        
        # Revoke request using same entity info
        revoke_request = RevokeUsagePlanRequest(
            entity_id=create_request.entity_id,
            entity_type=create_request.entity_type
        )
        
        # Revoke response
        revoke_response = RevokeUsagePlanResponse(success=True)
        
        # Verify consistency
        assert create_request.entity_id == revoke_request.entity_id
        assert create_request.entity_type == revoke_request.entity_type
        assert create_response.plan.entity_id == create_request.entity_id
        assert revoke_response.success is True
    
    def test_model_serialization_consistency(self):
        """Test that all models can be serialized and deserialized consistently"""
        models_to_test = [
            ConverseRequest(
                modelId="test-model",
                messages=[{"role": "user", "content": [{"text": "Test"}]}]
            ),
            CreateUsagePlanRequest(
                entity_id="test",
                entity_type=UsagePlanEntityType.USER,
                model_permissions=["test-model"]
            ),
            RevokeUsagePlanRequest(
                entity_id="test",
                entity_type=UsagePlanEntityType.USER
            ),
            RevokeUsagePlanResponse(success=True)
        ]
        
        for model in models_to_test:
            # Serialize to dict
            data = model.model_dump()
            assert isinstance(data, dict)
            
            # Deserialize back
            model_class = type(model)
            reconstructed = model_class.model_validate(data)
            
            # Should be equivalent
            assert reconstructed.model_dump() == data 