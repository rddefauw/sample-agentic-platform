# 🚀 Agentic Program Labs

Welcome to the Agentic Program Labs! This repository contains a series of hands-on labs designed to teach you how to build agentic applications using Large Language Models (LLMs) through Amazon Bedrock and other AWS services.

## 🏗️ Workshop Structure

The workshop consists of 5 progressive modules that build upon each other:

### Module 1: Prompt Engineering & Evaluation
- Master fundamental prompt engineering techniques
- Work with Bedrock's Converse API
- Learn chain-of-thought reasoning and few-shot examples
- Implement simple RAG systems and function calling
- Evaluate your prompts systematically

### Module 2: Common Agentic Patterns
- Explore various workflow techniques working with LLMs
- Implement parallelization strategies
- Build orchestration patterns
- Create reusable workflows
- Manage agent execution flows

### Module 3: Building Agentic Applications
- Implement an agent from scratch
- Understanding memory 
- Understanding and adding tools
- Adding retrieval
- Introducing frameworks and interoperability

### Module 4: Multi-Agent Systems & MCP
- Intro to MCP and build your own MCP Server / Client
- Build systems with multiple cooperating agents
- Implement agent communication protocols
- Create systems that leverage agent specialization

### Module 5: Deployment and Infrastructure
- Observability in agentic systems
- LLM Gateway & how to manage tenancy
- Memory Gateway & and how to manage short / long term memory
- Scale your agent infrastructure

## 📋 Prerequisites

Before starting these labs, you'll need:

- An AWS account with access to Amazon Bedrock
- Python 3.12 (these labs were tested with Python 3.12)
- Basic knowledge of Python programming

## 🏁 Getting Started

### 1. Set up your environment

We recommend using [uv](https://github.com/astral-sh/uv) for managing Python dependencies as it's faster and more reliable.

```bash
# Install uv if you don't have it already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone this repository and navigate to it
git clone <repository-url>
cd agentic-program-technical-assets

# Install dependencies from pyproject.toml
uv sync
```

### 2. Configure AWS Credentials

```bash
# Use AWS CLI
aws configure

# Ensure you have the right permissions for Amazon Bedrock
# You'll need model access enabled for Claude models
```

### 3. Start the Jupyter Lab environment

```bash
# Start Jupyter Lab with uv to ensure all dependencies are available
uv run jupyter lab
```

This will automatically:
- Install all required dependencies
- Make the `agentic_platform` code importable from your lab notebooks
- Start the Jupyter Lab interface

## 📂 Repository Structure

```
agentic-program-technical-assets/
├── src/
│   └── agentic_platform/  # Core utilities used across labs
│       ├── agent/         # Agent implementations
│       ├── tool/          # Tool utilities
│       ├── service/       # Service integrations
│       └── ...
├── labs/
│   ├── module1/          # Prompt Engineering & Evaluation
│   ├── module2/          # Common Agentic Patterns
│   ├── module3/          # Building Agentic Applications
│   ├── module4/          # Multi-Agent Systems
│   └── module5/          # Deployment and Infrastructure
├── pyproject.toml        # Project dependencies
└── README.md
```

## ℹ️ Additional Notes

- **Framework Interoperability**: Throughout the labs, we'll be using multiple frameworks (LangChain, LangGraph, CrewAI, etc.) to demonstrate how different tools can work together in the same application.
- **Terraform**: You don't need Terraform installed until Module 5, and it's optional for most of the labs.
- **Code Reuse**: The `agentic_platform` package in the `src/` directory is automatically available in all lab notebooks, so you can import components without copying code between modules.
- **Dependencies**: All required dependencies are specified in the `pyproject.toml` file and will be installed when you run `uv sync`.

## 🧭 Workshop Flow

1. Start with Module 1 to ensure your environment is configured correctly
2. Follow the modules in numerical order as each builds upon concepts from previous modules
3. Complete the exercises in each notebook
4. Review the example solutions provided

## 🆘 Getting Help

If you encounter issues:

1. Check your AWS credentials and permissions
2. Verify Bedrock model access (especially for Claude models)
3. Ensure all required packages are installed via `uv sync`
4. Review error messages carefully

Happy building! 🎉
