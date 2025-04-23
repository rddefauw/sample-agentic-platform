from agentic_platform.core.models.prompt_models import BasePrompt

# Define troubleshooting prompts inheriting from BasePrompt
class PlanningPrompt(BasePrompt):
    system_prompt: str = "You are an expert OpenSearch diagnostician. Your role is to identify potential causes for issues."
    user_prompt: str = """
    Plan the diagnostic steps needed for this OpenSearch issue:
    {problem}
    
    Analyze the issue and return a list of specific potential problems 
    that could be causing this issue. Be specific and thorough.
    
    For example, instead of just "configuration issues", specify "incorrect 
    shard allocation settings" or "memory allocation problems".
    
    Return each potential issue as a separate line. At most return 3 potential issues.
    """

class InvestigationPrompt(BasePrompt):
    system_prompt: str = "You are an expert OpenSearch troubleshooter. Provide detailed diagnostic and resolution information."
    user_prompt: str = """
    Regarding OpenSearch problem: 
    {question}
    
    Here's the context provided for the problem.
    {context}
    
    Explain how to diagnose if this is the actual problem and how to fix it.
    Include:
    1. Diagnostic commands or API calls
    2. Expected symptoms if this is the issue
    3. Step-by-step resolution steps
    4. Preventive measures
    """
    model_id: str = "us.amazon.nova-micro-v1:0"

class SynthesisPrompt(BasePrompt):
    system_prompt: str = "You are an expert OpenSearch engineer. Create a comprehensive, well-structured troubleshooting report."
    user_prompt: str = """
    Create a comprehensive troubleshooting report for this OpenSearch issue:
    {problem}
    
    Here are the findings from our investigation of potential causes:
    
    {issues_summary}
    
    Synthesize these findings into:
    1. Most likely root causes (ranked)
    2. Complete diagnostic steps
    3. Recommended resolution approach
    4. Verification steps to confirm the fix worked
    """