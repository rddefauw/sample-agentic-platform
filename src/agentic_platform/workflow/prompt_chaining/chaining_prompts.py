from agentic_platform.core.models.prompt_models import BasePrompt

SYSTEM_PROMPT = """
You are a helpful assistant that can explain OpenSearch documentation in simple terms.
"""

# Define reusable prompt templates as constants
EXTRACT_CONCEPTS_PROMPT_TEMPLATE = """
Using the users query, extract and list the key concepts from this OpenSearch documentation:

<query>
{question}
</query>

<documentation>
{context}
</documentation>

Focus on core principles and important technical details.
Format as a bulleted list.
"""

SIMPLIFY_EXPLANATION_PROMPT_TEMPLATE = """
Explain these OpenSearch concepts in simple, clear terms:
{concepts}

Write as if explaining to someone new to OpenSearch.
Include analogies where helpful.
"""

GENERATE_EXAMPLES_PROMPT_TEMPLATE = """
Create practical examples for implementing these OpenSearch concepts:
Concepts: {concepts}
Explanation: {explanation}

Include:
- Code snippets where relevant
- Step-by-step instructions
- Common pitfalls to avoid
"""

FORMAT_OUTPUT_TEMPLATE = """
# OpenSearch Documentation Breakdown

## Key Concepts
{concepts}

## Simple Explanation
{explanation}

## Implementation Examples
{examples}
"""

class ExtractConceptPrompt(BasePrompt):
    system_prompt: str = SYSTEM_PROMPT
    user_prompt: str = EXTRACT_CONCEPTS_PROMPT_TEMPLATE

class SimplifyExplanationPrompt(BasePrompt):
    system_prompt: str = SYSTEM_PROMPT
    user_prompt: str = SIMPLIFY_EXPLANATION_PROMPT_TEMPLATE

class GenerateExamplesPrompt(BasePrompt):
    system_prompt: str = SYSTEM_PROMPT
    user_prompt: str = GENERATE_EXAMPLES_PROMPT_TEMPLATE

class FormatOutputPrompt(BasePrompt):
    system_prompt: str = SYSTEM_PROMPT
    user_prompt: str = FORMAT_OUTPUT_TEMPLATE