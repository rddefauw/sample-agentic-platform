from agentic_platform.core.models.prompt_models import BasePrompt


class DIYAgentPrompt(BasePrompt):
    system_prompt: str = "You are a helpful assistant. You are given tools to help you accomplish your task. You can choose to use them or not."
    user_prompt: str = "{user_message}"
