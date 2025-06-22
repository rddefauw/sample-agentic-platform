from agentic_platform.core.models.api_models import AgenticRequest, AgenticResponse
from typing import List, Callable
from agentic_platform.agent.pydanticai_agent.pyai_agent import PyAIAgent
from agentic_platform.tool.retrieval.retrieval_tool import retrieve_and_answer
from agentic_platform.tool.weather.weather_tool import weather_report
from agentic_platform.tool.calculator.calculator_tool import handle_calculation
from agentic_platform.core.decorator.toolspec_decorator import tool_spec

# Pull the tools from our tool directory into the agent. Description is pulled from the docstring.
tools: List[Callable] = [retrieve_and_answer, weather_report, handle_calculation]
agent = PyAIAgent(tools=tools)

class PyAIAgentController:

    @classmethod
    async def invoke(cls, request: AgenticRequest) -> AgenticResponse:
        """
        Invoke the DIY agent. 
        """
        return await agent.invoke(request)