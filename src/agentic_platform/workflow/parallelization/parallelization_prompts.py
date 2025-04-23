from agentic_platform.core.models.prompt_models import BasePrompt

# Define the system prompt
SOLUTION_SYSTEM_PROMPT = """
You are a helpful assistant specializing in OpenSearch documentation and support.
"""

# Define reusable prompt templates as constants
BEGINNER_PROMPT_TEMPLATE = """
Create a beginner-friendly solution for this OpenSearch question:
{question}

Focus on:
- Simple, step-by-step instructions
- Basic concepts and terminology
- Common pitfalls to avoid
- Default configurations
"""

EXPERT_PROMPT_TEMPLATE = """
Create an advanced, expert-level solution for this OpenSearch question:
{question}

Include:
- Advanced configurations
- Performance optimizations
- Best practices
- Edge cases and considerations
"""

COST_PROMPT_TEMPLATE = """
Create a cost-optimized solution for this OpenSearch question:
{question}

Focus on:
- Resource efficiency
- Infrastructure costs
- Performance/cost tradeoffs
- Cost monitoring and optimization
"""

# Define prompt classes that inherit from BasePrompt
class BeginnerPrompt(BasePrompt):
    system_prompt: str = SOLUTION_SYSTEM_PROMPT
    user_prompt: str = BEGINNER_PROMPT_TEMPLATE

class ExpertPrompt(BasePrompt):
    system_prompt: str = SOLUTION_SYSTEM_PROMPT
    user_prompt: str = EXPERT_PROMPT_TEMPLATE

class CostPrompt(BasePrompt):
    system_prompt: str = SOLUTION_SYSTEM_PROMPT
    user_prompt: str = COST_PROMPT_TEMPLATE