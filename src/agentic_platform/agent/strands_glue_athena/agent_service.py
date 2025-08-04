"""
Strands agent service for AWS Glue and Athena.
"""
from strands_agents import Agent
from typing import Dict, Any, Optional

from agentic_platform.agent.strands_glue_athena.tools import (
    search_glue_catalog,
    get_table_details,
    list_databases,
    list_tables,
    run_athena_query,
    generate_sql_query,
    list_query_executions,
    get_query_results
)

# System prompt for the agent
SYSTEM_PROMPT = """
You are a helpful assistant that helps users search for tables in the AWS Glue catalog and run queries on them using Amazon Athena.

You have access to the following tools:
1. search_glue_catalog - Search for tables in the AWS Glue catalog based on table name, columns, and description
2. get_table_details - Get detailed information about a specific table in the AWS Glue catalog
3. list_databases - List all databases in the AWS Glue catalog
4. list_tables - List all tables in a specific AWS Glue database
5. run_athena_query - Run a SQL query on Amazon Athena
6. generate_sql_query - Generate a SQL query from a natural language description
7. list_query_executions - List recent query executions in Athena
8. get_query_results - Get results for a previously executed Athena query

When a user asks about data or tables:
1. First, search the Glue catalog to find relevant tables
2. If needed, get more details about specific tables
3. Help the user formulate and run Athena queries on these tables
4. Present the query results in a clear, readable format

Always explain what you're doing and why. If you encounter any errors, explain them clearly and suggest solutions.
"""


class StrandsGlueAthenaAgent:
    """
    Strands agent for AWS Glue and Athena operations.
    """
    
    def __init__(self, model_id: str = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"):
        """
        Initialize the Strands Glue/Athena agent.
        
        Args:
            model_id: The model ID to use for the agent
        """
        self.agent = Agent(
            model=model_id,  # Using model ID directly will use Bedrock by default
            system_prompt=SYSTEM_PROMPT,
            tools=[
                search_glue_catalog,
                get_table_details,
                list_databases,
                list_tables,
                run_athena_query,
                generate_sql_query,
                list_query_executions,
                get_query_results
            ]
        )
        
    def process_message(self, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a user message and return a response.
        
        Args:
            message: The user message to process
            session_id: Optional session ID for conversation continuity
            
        Returns:
            A dictionary containing the agent's response
        """
        # Call the agent directly with the message
        response = self.agent(message)
        
        # Extract the response content
        return {
            "text": response.message if hasattr(response, "message") else str(response),
            "tool_calls": getattr(response, "tool_calls", []),
            "tool_outputs": getattr(response, "tool_outputs", [])
        }
        
    def stream_message(self, message: str, session_id: Optional[str] = None):
        """
        Stream a response to a user message.
        
        Args:
            message: The user message to process
            session_id: Optional session ID for conversation continuity
            
        Returns:
            A generator that yields response chunks
        """
        # For simplicity, we'll use a non-streaming approach for now
        # and return the full response as a single chunk
        response = self.process_message(message, session_id)
        yield {
            "text": response["text"],
            "event_type": "text",
            "tool_call": None,
            "tool_output": None
        }
