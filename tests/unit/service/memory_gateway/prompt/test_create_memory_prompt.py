import pytest

from agentic_platform.service.memory_gateway.prompt.create_memory_prompt import (
    CreateMemoryPrompt, SYSTEM_PROMPT, USER_PROMPT
)
from agentic_platform.core.models.prompt_models import BasePrompt


class TestCreateMemoryPrompt:
    """Test CreateMemoryPrompt class and prompt constants"""
    
    def test_create_memory_prompt_inherits_from_base_prompt(self):
        """Test that CreateMemoryPrompt inherits from BasePrompt"""
        assert issubclass(CreateMemoryPrompt, BasePrompt)
    
    def test_create_memory_prompt_instantiation(self):
        """Test that CreateMemoryPrompt can be instantiated"""
        prompt = CreateMemoryPrompt()
        assert isinstance(prompt, CreateMemoryPrompt)
        assert isinstance(prompt, BasePrompt)
    
    def test_system_prompt_content(self):
        """Test that system prompt contains expected content"""
        assert isinstance(SYSTEM_PROMPT, str)
        assert len(SYSTEM_PROMPT.strip()) > 0
        
        # Check for key content elements
        expected_elements = [
            "specialized AI",
            "conversational interactions",
            "searchable memory entries",
            "semantic search",
            "third-person perspective"
        ]
        
        system_prompt_lower = SYSTEM_PROMPT.lower()
        for element in expected_elements:
            assert element.lower() in system_prompt_lower, f"Expected '{element}' not found in system prompt"
    
    def test_user_prompt_content(self):
        """Test that user prompt contains expected content and formatting"""
        assert isinstance(USER_PROMPT, str)
        assert len(USER_PROMPT.strip()) > 0
        
        # Check for template placeholders
        assert "{interaction_json}" in USER_PROMPT
        
        # Check for expected sections
        expected_sections = [
            "Create a searchable memory entry",
            "user_interaction",
            "User preferences",
            "Specific details",
            "Domain-specific knowledge",
            "Format preferences",
            "Feedback",
            "<memory>",
            "</memory>"
        ]
        
        for section in expected_sections:
            assert section in USER_PROMPT, f"Expected section '{section}' not found in user prompt"
    
    def test_prompt_class_attributes(self):
        """Test that CreateMemoryPrompt class has correct attributes"""
        prompt = CreateMemoryPrompt()
        
        # Check that the prompt attributes are set correctly
        assert hasattr(prompt, 'user_prompt')
        assert hasattr(prompt, 'system_prompt')
        
        assert prompt.user_prompt == USER_PROMPT
        assert prompt.system_prompt == SYSTEM_PROMPT
    
    def test_system_prompt_structure(self):
        """Test system prompt structure and formatting"""
        lines = SYSTEM_PROMPT.strip().split('\n')
        
        # Should be multi-line
        assert len(lines) > 1
        
        # Should contain numbered list
        numbered_items = [line for line in lines if line.strip().startswith(('1.', '2.', '3.', '4.', '5.'))]
        assert len(numbered_items) >= 4  # At least 4 numbered items expected
    
    def test_user_prompt_structure(self):
        """Test user prompt structure and formatting"""
        lines = USER_PROMPT.strip().split('\n')
        
        # Should be multi-line
        assert len(lines) > 1
        
        # Should contain XML-like tags
        xml_tags = ['<user_interaction>', '</user_interaction>', '<memory>', '</memory>']
        for tag in xml_tags:
            assert tag in USER_PROMPT, f"Expected XML tag '{tag}' not found"
        
        # Should contain numbered list for focus areas
        numbered_items = [line for line in lines if line.strip().startswith(('1.', '2.', '3.', '4.', '5.'))]
        assert len(numbered_items) >= 4  # At least 4 focus areas expected
    
    def test_prompt_constants_are_strings(self):
        """Test that prompt constants are properly defined as strings"""
        assert isinstance(SYSTEM_PROMPT, str)
        assert isinstance(USER_PROMPT, str)
        
        # Should not be empty
        assert len(SYSTEM_PROMPT.strip()) > 0
        assert len(USER_PROMPT.strip()) > 0
    
    def test_user_prompt_template_formatting(self):
        """Test that user prompt can be formatted with expected parameters"""
        test_interaction = {"user": "Hello", "assistant": "Hi there!"}
        
        # Should be able to format the template
        try:
            formatted_prompt = USER_PROMPT.format(interaction_json=test_interaction)
            assert str(test_interaction) in formatted_prompt
        except KeyError as e:
            pytest.fail(f"User prompt template formatting failed: {e}")
    
    def test_memory_extraction_instructions(self):
        """Test that the prompt contains clear memory extraction instructions"""
        user_prompt_lower = USER_PROMPT.lower()
        
        extraction_keywords = [
            "memory entry",
            "self-contained",
            "context",
            "useful",
            "single paragraph",
            "without additional explanation"
        ]
        
        for keyword in extraction_keywords:
            assert keyword in user_prompt_lower, f"Expected keyword '{keyword}' not found in extraction instructions"
    
    def test_prompt_class_inheritance_behavior(self):
        """Test that CreateMemoryPrompt properly inherits BasePrompt behavior"""
        prompt = CreateMemoryPrompt()
        
        # Should have BasePrompt methods available
        assert hasattr(prompt, 'user_prompt')
        assert hasattr(prompt, 'system_prompt')
        
        # Attributes should be accessible
        assert prompt.user_prompt is not None
        assert prompt.system_prompt is not None 