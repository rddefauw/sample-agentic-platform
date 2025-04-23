# 🚀 Module 1: Prompt Engineering & Evaluation with Amazon Bedrock

Welcome to Module 1 of the A2B Workshop series! In this module, you'll learn how to effectively work with Large Language Models (LLMs) through Amazon Bedrock, with a focus on prompt engineering and evaluation.

## 🎯 What You'll Learn

In this hands-on workshop, you'll:

- 🛠️ Set up and use the Amazon Bedrock Converse API
- 🔄 Create and run basic model invocations using LangGraph
- 📝 Learn fundamental prompt engineering techniques
- 🧠 Implement chain-of-thought reasoning
- 📊 Work with few-shot examples
- 🔍 Build a simple RAG (Retrieval Augmented Generation) system
- 🧩 Use function calling to get structured outputs
- 📊 Evaluate your prompts systematically

## 📋 Prerequisites

Before starting this workshop, you'll need:

- An AWS account with access to Amazon Bedrock
- Python 3.12 (this workshop was tested with Python 3.12)
- Basic knowledge of Python programming

## 🏁 Getting Started
To get started, see the parent readme file in the lab for instructions on how to get the lab and dependencies stood up


## 📚 Workshop Notebooks

The workshop consists of 7 notebooks that build upon each other:

### 1. Setup and Basics (`1_setup_and_basics.ipynb`)
- 🔧 Setting up the Bedrock environment
- 💬 Using the Converse API
- 🚀 First conversations with the model

### 2. LangGraph Basics (`2_langgraph_basics.ipynb`)
- 📊 Introduction to LangGraph
- 🔄 Creating structured conversation flows
- 💾 Managing conversation state

### 3. Chain of Thought (`3_chain_of_thought.ipynb`)
- 🧠 Understanding chain-of-thought reasoning
- 🪜 Implementing step-by-step problem solving
- 📈 Comparing basic vs. chain-of-thought prompts

### 4. Few-Shot Examples (`4_few_shot_examples.ipynb`)
- 🎓 Learning from examples
- 📝 Implementing few-shot learning
- 📋 Creating effective example templates

### 5. RAG Basics (`5_rag_basics.ipynb`)
- 📚 Setting up a knowledge base
- 🔍 Implementing document retrieval
- 🔗 Combining context with prompts

### 6. Function Calling (`6_function_calling.ipynb`)
- 🧩 Working with structured outputs
- 📞 Implementing function calling
- ⚠️ Error handling and validation

### 7. Evaluation (`7_evaluation.ipynb`)
- 📊 Evaluating prompt performance
- 📏 Measuring accuracy and relevance
- 🔄 Iterative improvement techniques

## 📂 Folder Structure

```
module1/
├── README.md
├── notebooks/
│   ├── 1_setup_and_basics.ipynb
│   ├── 2_langgraph_basics.ipynb
│   ├── 3_chain_of_thought.ipynb
│   ├── 4_few_shot_examples.ipynb
│   ├── 5_rag_basics.ipynb
│   ├── 6_function_calling.ipynb
│   └── 7_evaluation.ipynb
├── data/
└── assets/
```

## 🧭 Workshop Flow

1. Start with the setup notebook to ensure your environment is configured correctly
2. Follow the notebooks in numerical order
3. Complete the exercises in each notebook
4. Review the example solutions provided

Each notebook includes:
- Clear explanations of concepts
- Step-by-step instructions
- Code examples you can run
- Practice exercises to reinforce learning

## 🆘 Getting Help

If you encounter issues:

1. Check your AWS credentials and permissions
2. Verify Bedrock model access (especially for Claude models)
3. Ensure all required packages are installed via `uv sync`
4. Review error messages carefully

Start with `1_setup_and_basics.ipynb` and proceed through each notebook in sequence. Each builds upon the concepts learned in the previous notebooks.

Happy learning! 🎉

```

```
