

from agentic_platform.core.models.prompt_models import BasePrompt

# Define the system prompt
CLASSIFY_SYSTEM_PROMPT = """
You are a helpful assistant specializing in OpenSearch documentation and support.
"""

RAG_SYSTEM_PROMPT = """
You are a helpful assistant specializing in OpenSearch documentation and support.
<instructions>
1. Answer the question using only the documentation provided
2. Be clear and concise with your answer. Your answers should be short, direct, and to the point
3. Avoid saying "based on the context provided"
4. If the answer isn't in the documentation, say "I don't know".
</instructions>
"""

# Define reusable prompt templates as constants
CLASSIFY_PROMPT_TEMPLATE = """
Classify this OpenSearch question into exactly one category:

Question: {question}

Categories:
- INSTALL: Installation, setup, cluster configuration
- SECURITY: Security, authentication, access control
- QUERY: Querying, indexing, search operations
- PERFORMANCE: Optimization, scaling, monitoring

Respond with only the category code (e.g., 'INSTALL').
"""

INSTALLATION_PROMPT_TEMPLATE = """
Using the users qusetions below and provided context, provide detailed installation and setup guidance for OpenSearch:

<question>
{question}
</question>

<context>
{context}
</context>

Include:
- Step-by-step instructions
- System requirements
- Configuration options
- Common issues and solutions

Remember, your answers should be short, direct, and to the point. DO NOT include any preamble or introduction and DO NOT say "based on the context provided" or anything similar.
"""

SECURITY_PROMPT_TEMPLATE = """
Using the users qusetions below and provided context, provide security guidance for OpenSearch:

<question>
{question}
</question>

<context>
{context}
</context>

Include:
- Security best practices
- Authentication setup
- Access control configuration
- Security implications

Remember, your answers should be short, direct, and to the point. DO NOT include any preamble or introduction and DO NOT say "based on the context provided" or anything similar.

"""

QUERY_PROMPT_TEMPLATE = """
Using the users qusetions below and provided context, provide guidance on OpenSearch querying and indexing:

<question>
{question}
</question>

<context>
{context}
</context>

Include:
- Query examples
- Index configuration
- Best practices
- Performance considerations

Remember, your answers should be short, direct, and to the point. DO NOT include any preamble or introduction and DO NOT say "based on the context provided" or anything similar.

"""

PERFORMANCE_PROMPT_TEMPLATE = """
Using the users qusetions below and provided context, provide performance optimization guidance for OpenSearch:

<question>
{question}
</question>

<context>
{context}
</context>

Include:
- Optimization strategies
- Scaling considerations
- Monitoring tips
- Resource management

Remember, your answers should be short, direct, and to the point. DO NOT include any preamble or introduction and DO NOT say "based on the context provided" or anything similar.
"""

# Define prompt classes that inherit from BasePrompt
class ClassifyPrompt(BasePrompt):
    system_prompt: str = CLASSIFY_SYSTEM_PROMPT
    user_prompt: str = CLASSIFY_PROMPT_TEMPLATE

class InstallationPrompt(BasePrompt):
    system_prompt: str = RAG_SYSTEM_PROMPT
    user_prompt: str = INSTALLATION_PROMPT_TEMPLATE

class SecurityPrompt(BasePrompt):
    system_prompt: str = RAG_SYSTEM_PROMPT
    user_prompt: str = SECURITY_PROMPT_TEMPLATE

class QueryPrompt(BasePrompt):
    system_prompt: str = RAG_SYSTEM_PROMPT
    user_prompt: str = QUERY_PROMPT_TEMPLATE

class PerformancePrompt(BasePrompt):
    system_prompt: str = RAG_SYSTEM_PROMPT
    user_prompt: str = PERFORMANCE_PROMPT_TEMPLATE