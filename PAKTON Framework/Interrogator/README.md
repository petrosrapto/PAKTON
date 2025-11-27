# Interrogator

## Overview

The **Interrogator** is the component responsible for generating the final report presented to the user by orchestrating a multi-step reasoning process. It iteratively questions the Researcher to refine its understanding and draft response, continuing until the answer is sufficiently complete or the maximum number of interrogation turns is reached.

The system excels at:
- **Iterative Knowledge Extraction**: Conducting multi-turn conversations to uncover deeper insights
- **Gap Identification**: Recognizing and addressing knowledge gaps in initial responses  
- **Ambiguity Resolution**: Clarifying unclear or contradictory information through targeted follow-up questions
- **Consistency Validation**: Cross-referencing responses for accuracy and coherence
- **Structured Analysis**: Generating comprehensive reports with reasoning chains and confidence metrics

## 🏗️ Architecture

Interrogator utilizes a state-based graph architecture powered by LangGraph, enabling sophisticated conversation flow control and memory management:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Question        │    │ Answer          │    │ Answer          │
│ Generation      │───▶│ Retrieval       │───▶│ Refinement      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                                              │
         │              ┌─────────────────┐             │
         └──────────────│ Router          │◀────────────┘
                        │ (Turn Control)  │
                        └─────────────────┘
                                 │
                        ┌─────────────────┐    ┌─────────────────┐
                        │ Interrogation   │───▶│ Report          │
                        │ Storage         │    │ Generation      │
                        └─────────────────┘    └─────────────────┘
```

### Core Components

- **Question Generator**: Creates strategic follow-up questions based on conversation context
- **Answer Retrieval**: Interfaces with external knowledge sources and RAG systems
- **Answer Refinement**: Processes and enhances retrieved information
- **Router**: Controls conversation flow and determines when to conclude interrogation
- **Report Generator**: Synthesizes findings into comprehensive, structured outputs
- **State Management**: Maintains conversation context and metadata throughout the process

## 🚀 Features

### Advanced Questioning Strategies
- **Context-Aware Question Generation**: Adapts questioning style based on domain and conversation history
- **Multi-Turn Conversation Management**: Maintains coherent dialogue across multiple exchanges
- **Strategic Follow-up**: Generates targeted questions to fill knowledge gaps
- **Dynamic Depth Control**: Adjusts questioning depth based on response quality and completeness

### Flexible Configuration
- **Multi-Model Support**: Compatible with OpenAI, Google Gemini, AWS Bedrock, and local models
- **Customizable Parameters**: Configurable turn limits, temperature settings, and model selection
- **Domain Adaptation**: Specialized prompts and strategies for different knowledge domains
- **Mode Selection**: Choose between exploratory, critical, or validating interrogation styles

### Robust Integration
- **API-Ready**: Built for seamless integration with REST APIs and microservices
- **Memory Management**: Persistent conversation state with checkpointing capabilities
- **Error Handling**: Comprehensive error recovery and logging mechanisms
- **Performance Monitoring**: Built-in metrics and tracing through LangSmith integration

## 📋 Prerequisites

Before installing Interrogator, ensure you have:

- **Python 3.11 or higher**
- **pip** (Python package installer)
- **API keys** for your chosen language model provider(s)

## 🛠️ Installation

### Method 1: Development Installation (Recommended)

1. **Clone the PAKTON repository**:
   ```bash
   git clone https://github.com/petrosrapto/PAKTON.git
   cd PAKTON/PAKTON\ Framework/Interrogator
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install the package in development mode**:
   ```bash
   pip install -e .
   ```

### Method 2: Direct Installation
```bash
pip install git+https://github.com/petrosrapto/PAKTON.git#subdirectory=PAKTON\ Framework/Interrogator
```

### Verify Installation
```python
from Interrogator.agent import Interrogator
print("Interrogator installed successfully!")
```

## ⚙️ Configuration

### Environment Setup

1. **Create environment file**:
   ```bash
   cp src/Interrogator/.env.example src/Interrogator/.env
   ```

2. **Configure API keys in `.env`**:
   ```dotenv
   # Choose your preferred model provider
   OPENAI_API_KEY=your_openai_api_key_here
   GOOGLE_API_KEY=your_google_api_key_here
   AWS_ACCESS_KEY_ID=your_aws_access_key_here
   AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key_here
   
   # Optional: LangChain tracing
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_PROJECT=interrogator_project
   LANGCHAIN_API_KEY=your_langchain_api_key_here
   ```

### Model Configuration

Create config file:
```bash
cp src/Interrogator/config.example.yaml src/Interrogator/config.yaml
```

Edit `src/Interrogator/config.yaml` to customize model settings:

```yaml
models:
  default:
    API: "GOOGLE"  # Options: OPENAI, GOOGLE, BEDROCK, LOCAL
    model_id: "gemini-2.0-flash"
    args:
      temperature: 0.2
      max_tokens: 8192

  question_generator:
    API: "GOOGLE"
    model_id: "gemini-2.0-flash"
    args:
      temperature: 0.5

interrogation:
  max_num_turns: 3  # Maximum conversation turns

logging:
  level: "INFO"
  file: "interrogator.log"
  console_output: true
```

### Supported Models

#### OpenAI
- `gpt-4o`, `gpt-4-turbo`, `gpt-3.5-turbo`

#### Google
- `gemini-2.0-flash`, `gemini-1.5-pro`, `gemma-3-27b-it`

#### AWS Bedrock
- `anthropic.claude-3-5-sonnet-20241022-v2:0`
- `meta.llama3-1-70b-instruct-v1:0`
- `mistral.mistral-7b-instruct-v0:2`

#### Local Models (via vLLM)
- Llama 3.1, Qwen 2.5, DeepSeek, and other compatible models

## 🎯 Quick Start

### Basic Usage

```python
from Interrogator.agent import Interrogator

# Initialize with default configuration
interrogator = Interrogator()

# Conduct an interrogation
result = interrogator.interrogation(
    userQuery="Explain the transformer architecture in neural networks",
    userContext="I'm a graduate student studying machine learning",
    userInstructions="Focus on the attention mechanism and provide technical details"
)

# Access results
print("Final Answer:", result.get("conclusion", ""))
print("Conversation Report:", result.get("report", ""))
```

### Advanced Configuration

```python
from Interrogator.agent import Interrogator

# Custom configuration
config = {
    "run_name": "Advanced_ML_Interrogation",
    "memory_saver": None  # Use default MemorySaver
}

# Per-interrogation settings
interrogation_config = {
    "max_num_turns": 5,  # Extended conversation
}

interrogator = Interrogator(config)

result = interrogator.interrogation(
    userQuery="How do attention mechanisms work in transformers?",
    userContext="Research context for paper writing",
    userInstructions="Provide detailed mathematical formulations",
    config=interrogation_config
)
```

### Working with Different Domains

```python
# Legal domain interrogation
legal_result = interrogator.interrogation(
    userQuery="What are the key elements of contract formation?",
    userContext="Legal research for case analysis",
    userInstructions="Focus on common law principles and precedents"
)

# Technical domain interrogation  
technical_result = interrogator.interrogation(
    userQuery="Explain distributed system consensus algorithms",
    userContext="System architecture design",
    userInstructions="Compare Raft and PBFT algorithms"
)
```

## 📊 Response Structure

Interrogator returns structured responses with comprehensive metadata:

```python
{
    "status": "success",  # "success" or "error"
    "conclusion": "Final comprehensive answer...",
    "report": "Detailed conversation analysis...",
    "interrogation": "Raw conversation history...",
    "messages": [  # Full conversation chain
        {"role": "human", "content": "Question 1..."},
        {"role": "ai", "content": "Answer 1..."},
        # ... additional turns
    ],
    "config": {...},  # Applied configuration
    "userQuery": "Original user query",
    "userContext": "Provided context",
    "userInstructions": "Given instructions"
}
```

## 🔧 Advanced Usage

### Custom Memory Management

```python
from langgraph.checkpoint.memory import MemorySaver

# Custom memory configuration
memory_saver = MemorySaver()
config = {"memory_saver": memory_saver}

interrogator = Interrogator(config)

# Conversations maintain state across calls
result1 = interrogator.interrogation("What is machine learning?")
result2 = interrogator.interrogation("How does it relate to AI?")  # Context preserved
```

### Model Selection per Component

```yaml
# In config.yaml
models:
  question_generator:
    API: "OPENAI"
    model_id: "gpt-4o"
    
  report_generator:
    API: "GOOGLE" 
    model_id: "gemini-2.0-flash"
    
  write_conclusion:
    API: "BEDROCK"
    model_id: "anthropic.claude-3-5-sonnet-20241022-v2:0"
```

### Integration with External RAG Systems

```python
# Example integration pattern
class CustomRAGInterrogator(Interrogator):
    def __init__(self, rag_system, config=None):
        super().__init__(config)
        self.rag_system = rag_system
    
    def enhanced_interrogation(self, query, context=None):
        # Pre-populate with RAG system knowledge
        rag_response = self.rag_system.query(query)
        
        # Use Interrogator to refine and expand
        return self.interrogation(
            userQuery=query,
            userContext=f"RAG Context: {rag_response}\n{context or ''}",
            userInstructions="Expand and verify the provided information"
        )
```

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure proper installation
   pip install -e .
   
   # Check Python path
   python -c "import sys; print(sys.path)"
   ```

2. **API Key Issues**
   ```bash
   # Verify environment variables
   echo $OPENAI_API_KEY
   echo $GOOGLE_API_KEY
   
   # Check .env file location
   ls -la src/Interrogator/.env
   ```

3. **Model Configuration Errors**
   ```python
   # Test model availability
   from Interrogator.models import get_default_llm
   llm = get_default_llm()
   print(llm.invoke("Test message"))
   ```

4. **Memory Issues**
   ```python
   # Use memory-efficient settings
   config = {
       "max_num_turns": 2,  # Reduce conversation length
   }
   ```

### Debugging

Enable detailed logging:

```yaml
# In config.yaml
logging:
  level: "DEBUG"
  console_output: true
```

### Performance Optimization

```python
# Optimize for speed
speed_config = {
    "max_num_turns": 1,  # Single turn for faster responses
}

# Optimize for quality  
quality_config = {
    "max_num_turns": 5,  # Extended interrogation
}
```

## 🤝 Integration with PAKTON Framework

Interrogator is designed as a core component of the PAKTON ecosystem:

- **API Integration**: Seamlessly deployable via PAKTON API service
- **Archivist Connection**: Automatic conversation storage and retrieval
- **Researcher Integration**: Enhanced with external knowledge sources
- **Frontend Compatibility**: Direct integration with PAKTON web interfaces

```python
# Example PAKTON integration
from PAKTON.API import create_interrogation_endpoint
from Interrogator.agent import Interrogator

interrogator = Interrogator()
app = create_interrogation_endpoint(interrogator)
```

## 📝 API Reference

### Core Classes

#### `Interrogator`

**Constructor**: `Interrogator(config: Optional[Dict[str, Any]] = None)`

**Methods**:
- `interrogation(userQuery: str, userContext: Optional[str] = None, userInstructions: Optional[str] = None, config: Optional[Dict[str, Any]] = {}) -> Dict[str, Any]`

#### `GraphBuilder`

**Constructor**: `GraphBuilder()`

**Methods**:
- `build() -> StateGraph`
- `compile(memory_saver: Optional[MemorySaver] = None, run_name: str = "Interrogator")`

### Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_num_turns` | int | 1 | Maximum conversation turns |
| `run_name` | str | "Interrogator" | Execution run identifier |
| `memory_saver` | MemorySaver | MemorySaver() | Conversation state manager |
