import pytest
from typing import Dict, Any
from pydantic import ValidationError

from agentic_platform.service.llm_gateway.models.usage_types import (
    UsagePlanEntityType, RateLimits, UsagePlan, RateLimitResult, UsageRecord
)


class TestUsagePlanEntityType:
    """Test UsagePlanEntityType enum"""
    
    pass


class TestRateLimits:
    """Test RateLimits model"""
    
    def test_default_rate_limits(self):
        """Test default rate limits creation"""
        limits = RateLimits()
        
        # Should have reasonable defaults
        assert limits.input_tpm > 0
        assert limits.output_tpm > 0
        assert limits.rpm > 0
    

    
    def test_negative_values_validation(self):
        """Test validation of negative values"""
        # RateLimits should accept any integer values including negative
        limits = RateLimits(
            input_tpm=-100,
            output_tpm=-50,
            rpm=-10
        )
        
        assert limits.input_tpm == -100
        assert limits.output_tpm == -50
        assert limits.rpm == -10
    
    # Removed basic serialization test - tests Pydantic functionality, not business logic


class TestUsagePlan:
    """Test UsagePlan model"""
    
    def test_minimal_usage_plan(self):
        """Test creating usage plan with minimal fields"""
        plan = UsagePlan(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["claude-3", "gpt-4"]
        )
        
        assert plan.entity_id == "test-entity"
        assert plan.entity_type == UsagePlanEntityType.USER
        assert plan.usage_id is not None  # Auto-generated
        
        # Should have defaults
        assert plan.active is True
        assert plan.tenant_id == 'SYSTEM'
    
    # Removed trivial constructor test - just testing field assignment
    
    def test_missing_required_fields(self):
        """Test validation error with missing required fields"""
        with pytest.raises(ValidationError):
            UsagePlan()  # Missing all required fields
        
        with pytest.raises(ValidationError):
            UsagePlan(entity_id="test")  # Missing entity_type and model_permissions
    
    def test_get_limits_for_model_method(self):
        """Test getting rate limits for specific model"""
        custom_limits = RateLimits(input_tpm=1000, output_tpm=500, rpm=60)
        plan = UsagePlan(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["test-model"],
            default_limits=custom_limits
        )
        
        # Should return the plan's default limits
        limits = plan.get_limits_for_model("any-model")
        assert limits.input_tpm == 1000
        assert limits.output_tpm == 500
        assert limits.rpm == 60
    
    def test_get_limits_for_model_with_defaults(self):
        """Test getting rate limits when none specified"""
        plan = UsagePlan(
            entity_id="test-entity",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["test-model"]
            # No custom default_limits
        )
        
        # Should return default rate limits
        limits = plan.get_limits_for_model("any-model")
        assert isinstance(limits, RateLimits)
        assert limits.input_tpm > 0
        assert limits.output_tpm > 0
        assert limits.rpm > 0
    
    def test_entity_type_validation(self):
        """Test entity type validation"""
        for entity_type in [UsagePlanEntityType.USER, UsagePlanEntityType.API_KEY, UsagePlanEntityType.SERVICE, UsagePlanEntityType.DEPARTMENT, UsagePlanEntityType.PROJECT]:
            plan = UsagePlan(
                entity_id="test",
                entity_type=entity_type,
                model_permissions=["test-model"]
            )
            assert plan.entity_type == entity_type
    
    # Removed nested serialization test - tests Pydantic nested object handling


class TestRateLimitResult:
    """Test RateLimitResult model"""
    
    def test_allowed_result(self):
        """Test creating allowed rate limit result"""
        result = RateLimitResult(
            allowed=True,
            tenant_id="test-tenant",
            model_id="test-model",
            current_usage=RateLimits(input_tpm=100, output_tpm=50, rpm=5),
            model_usage=RateLimits(input_tpm=200, output_tpm=100, rpm=10),
            applied_limits=RateLimits(input_tpm=1000, output_tpm=500, rpm=60),
            model_limits=RateLimits(input_tpm=1000, output_tpm=500, rpm=60)
        )
        
        assert result.allowed is True
        assert result.tenant_id == "test-tenant"
        assert result.model_id == "test-model"
        assert result.current_usage.input_tpm == 100
        assert result.model_usage.input_tpm == 200
        assert result.applied_limits.input_tpm == 1000
        assert result.model_limits.input_tpm == 1000
    
    def test_blocked_result(self):
        """Test creating blocked rate limit result"""
        result = RateLimitResult(
            allowed=False,
            tenant_id="blocked-tenant",
            model_id="blocked-model",
            current_usage=RateLimits(input_tpm=950, output_tpm=475, rpm=58),
            model_usage=RateLimits(input_tpm=800, output_tpm=400, rpm=48),
            applied_limits=RateLimits(input_tpm=1000, output_tpm=500, rpm=60),
            model_limits=RateLimits(input_tpm=1000, output_tpm=500, rpm=60)
        )
        
        assert result.allowed is False
        assert result.tenant_id == "blocked-tenant"
        assert result.current_usage.input_tpm == 950  # Close to limit
    
    def test_missing_required_fields(self):
        """Test validation error with missing required fields"""
        with pytest.raises(ValidationError):
            RateLimitResult()  # Missing all required fields
        
        with pytest.raises(ValidationError):
            RateLimitResult(allowed=True)  # Missing other required fields


class TestUsageRecord:
    """Test UsageRecord model"""
    
    def test_minimal_usage_record(self):
        """Test creating usage record with minimal fields"""
        record = UsageRecord(
            tenant_id="test-tenant",
            model="test-model",
            input_tokens=100,
            output_tokens=50
        )
        
        assert record.input_tokens == 100
        assert record.output_tokens == 50
        assert record.model == "test-model"
        assert record.tenant_id == "test-tenant"
    
    # Removed trivial constructor test - just testing field assignment
    
    def test_usage_record_timestamp_default(self):
        """Test that timestamp has a default value"""
        record = UsageRecord(
            tenant_id="test-tenant",
            model="compute-test",
            input_tokens=75,
            output_tokens=25
        )
        
        assert record.timestamp > 0  # Should have a timestamp
    
    def test_usage_record_with_explicit_timestamp(self):
        """Test usage record with explicitly set timestamp"""
        record = UsageRecord(
            tenant_id="test-tenant",
            model="explicit-test",
            input_tokens=80,
            output_tokens=40,
            timestamp=1234567890
        )
        
        assert record.timestamp == 1234567890
    
    def test_missing_required_fields(self):
        """Test validation error with missing required fields"""
        with pytest.raises(ValidationError):
            UsageRecord()  # Missing all required fields
        
        with pytest.raises(ValidationError):
            UsageRecord(input_tokens=100)  # Missing tenant_id, model, and output_tokens
    
    def test_negative_token_values(self):
        """Test usage record with negative token values"""
        # Should allow negative values for correction records
        record = UsageRecord(
            tenant_id="test-tenant",
            model="correction-test",
            input_tokens=-50,
            output_tokens=-25
        )
        
        assert record.input_tokens == -50
        assert record.output_tokens == -25
    
    # Removed basic serialization test - tests Pydantic framework functionality


class TestUsageTypesIntegration:
    """Test integration between different usage types"""
    
    def test_usage_plan_with_rate_limit_result(self):
        """Test usage plan integration with rate limit result"""
        plan = UsagePlan(
            entity_id="integration-entity",
            entity_type=UsagePlanEntityType.USER,
            model_permissions=["integration-model"],
            tenant_id="integration-tenant",
            default_limits=RateLimits(input_tpm=1000, output_tpm=500, rpm=60)
        )
        
        # Get limits for model
        limits = plan.get_limits_for_model("integration-model")
        
        # Create rate limit result using plan data
        result = RateLimitResult(
            allowed=True,
            tenant_id=plan.tenant_id,
            model_id="integration-model",
            current_usage=RateLimits(input_tpm=100, output_tpm=50, rpm=5),
            model_usage=RateLimits(input_tpm=200, output_tpm=100, rpm=10),
            applied_limits=limits,
            model_limits=limits
        )
        
        # Verify integration
        assert result.tenant_id == plan.tenant_id
        assert result.applied_limits.input_tpm == plan.default_limits.input_tpm
        assert result.model_limits.rpm == plan.default_limits.rpm
    
    # Removed redundant serialization test - tests Pydantic framework, not business logic 