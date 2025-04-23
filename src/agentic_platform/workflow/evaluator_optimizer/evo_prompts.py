
from agentic_platform.core.models.prompt_models import BasePrompt
# Define system prompt
SYSTEM_PROMPT = """
You are an expert OpenSearch troubleshooter who provides accurate, comprehensive solutions.
"""

DECISION_SYSTEM_PROMPT = "You make clear decisions based on feedback quality."

# Define prompt templates as constants
GENERATE_SOLUTION_TEMPLATE = """
Provide a comprehensive troubleshooting solution for this OpenSearch issue:

<query>
{question}
</query>

<documentation>
{context}
</documentation>

Include:
- Potential root causes
- Diagnostic steps
- Resolution instructions
- Verification methods
"""

EVALUATE_SOLUTION_TEMPLATE = """
Evaluate if this OpenSearch troubleshooting solution fully addresses the problem:

<question>
{question}
</question>

<context>
{context}
</context>

<answer>
{answer}
</answer>

Assess:
- Completeness
- Technical accuracy
- Practical applicability
- Clarity of explanation

Provide specific feedback for improvement.
"""

IMPROVE_SOLUTION_TEMPLATE = """
Improve this OpenSearch troubleshooting solution based on feedback:

<problem>
{question}
</problem>

<context>
{context}
</context>

<current_solution>
{answer}
</current_solution>

<feedback>
{feedback}
</feedback>

Provide an improved solution that addresses all feedback points.
"""

DECISION_PROMPT_TEMPLATE = """
Based on this feedback, does the OpenSearch troubleshooting solution need improvement?

<feedback>
{feedback}
</feedback>

Reply with ONLY with 'IMPROVE' or 'DONE'.
"""

# Define prompt classes
class GenerateSolutionPrompt(BasePrompt):
    system_prompt: str = SYSTEM_PROMPT
    user_prompt: str = GENERATE_SOLUTION_TEMPLATE

class EvaluateSolutionPrompt(BasePrompt):
    system_prompt: str = SYSTEM_PROMPT
    user_prompt: str = EVALUATE_SOLUTION_TEMPLATE

class ImproveSolutionPrompt(BasePrompt):
    system_prompt: str = SYSTEM_PROMPT
    user_prompt: str = IMPROVE_SOLUTION_TEMPLATE

class DecisionPrompt(BasePrompt):
    system_prompt: str = DECISION_SYSTEM_PROMPT
    user_prompt: str = DECISION_PROMPT_TEMPLATE