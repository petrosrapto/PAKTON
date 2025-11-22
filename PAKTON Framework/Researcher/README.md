# Researcher Agent

A sophisticated RAG (Retrieval-Augmented Generation) agent that leverages multiple information retrieval sources and advanced reranking techniques to provide comprehensive, accurate answers to complex queries. The Researcher agent is part of the PAKTON framework and uses a StateGraph architecture for intelligent information retrieval and synthesis.

## 🚀 Features

### Multi-Source Retrieval
- **Web Search**: Real-time web search via Tavily API
- **Wikipedia**: Comprehensive Wikipedia article retrieval
- **Vector Databases**: Support for Pinecone and ChromaDB
- **BM25**: Traditional keyword-based search with relevance scoring
- **Hybrid Search**: Combines vector and BM25 retrieval methods
- **LightRAG**: Knowledge graph-based retrieval system
- **MySQL Database**: Direct database querying capabilities

### Advanced Reranking & Filtering
- **Cross-Encoder Reranking**: High-precision document relevance scoring
- **FLAG Reranker**: Efficient reranking with FP16 support
- **LLM-based Reranking**: Context-aware reranking using language models
- **LLM Filtering**: Additional content filtering for optimal relevance

### Flexible Model Configuration
- **Multiple AI Providers**: OpenAI, AWS Bedrock, Local deployments (vLLM), Google AI
- **Configurable Models**: Different models for query extraction, response generation
- **Temperature Control**: Fine-tune response creativity and determinism
- **Custom Endpoints**: Support for self-hosted model servers

### Robust System Design
- **StateGraph Architecture**: Modular, extensible graph-based processing
- **Comprehensive Logging**: Detailed logging with rotation and retention
- **Error Handling**: Graceful degradation and detailed error reporting
- **Memory Management**: Efficient state management and caching
- **Optional Visualization**: Graph visualization for debugging and analysis

## 📋 Requirements

- **Python**: 3.11 or higher
- **Operating System**: macOS, Linux, Windows
- **Memory**: Minimum 8GB RAM (16GB recommended for optimal performance)

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/petrosrapto/PAKTON.git
cd "PAKTON/PAKTON Framework/Researcher"
```

### 2. Create Virtual Environment

```bash
python -m venv researcher_env
source researcher_env/bin/activate  # On Windows: researcher_env\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install the Package

```bash
pip install -e .
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the `src/Researcher/` directory using the provided template:

```bash
cp src/Researcher/.env.example src/Researcher/.env
```

Edit the `.env` file with your API keys and configuration:

```env
# Required API Keys
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key
HUGGINGFACE_TOKEN=your_huggingface_token

# AWS Configuration (for Bedrock)
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION_NAME=us-west-2

# Vector Database (Pinecone)
PINECONE_API_KEY=your_pinecone_api_key

# Google AI (optional)
GOOGLE_API_KEY=your_google_api_key

# LangSmith Tracing (optional)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=researcher_project
LANGCHAIN_API_KEY=your_langchain_api_key
```

### System Configuration

The main configuration is handled through `config.yaml`. Key sections include:

#### Retriever Configuration

```yaml
retrievers:
  wikipedia:
    load_max_docs: 2
    lang: "en"
    
  web:
    search_client: "tavily"
    max_results: 5
    
  vectordb:
    top_k: 100
    use_vector_store: "chroma"  # or "pinecone"
    
  hybrid:
    top_k: 64
    bm25_weight: 0.5
    vector_weight: 0.5
```

#### Model Configuration

```yaml
models:
  default:
    API: "OPENAI"  # OPENAI, BEDROCK, LOCAL, or GOOGLE
    model_id: "gpt-4o"
    args:
      temperature: 0
      
  query_extractor:
    API: "OPENAI"
    model_id: "gpt-4o-mini"  # Use a faster model for query processing
    
  response_generator:
    API: "OPENAI"
    model_id: "gpt-4o"  # Use a more powerful model for responses
```

#### Reranking Configuration

```yaml
reranking:
  use_reranker: true
  top_k: 64
  reranker_type: "llm-reranker"  # cross-encoder, flag-reranker, llm-reranker
  model: "BAAI/bge-reranker-v2-minicpm-layerwise"
  use_fp16: true
```

## 🚦 Quick Start

### Basic Usage

```python
from Researcher import Researcher

# Configure which retrievers to use
config = {
    "enable_web": True,
    "enable_wikipedia": True,
    "enable_hybrid": True,
    "run_name": "My Research Query"
}

# Initialize the researcher
researcher = Researcher(config)

# Run a search query
results = researcher.search(
    query="What are the latest developments in large language models?",
    instructions="Focus on recent breakthroughs and applications"
)

# Access the results
print("Response:", results.get("response"))
print("Sources:", results.get("sources", []))
```

### Advanced Configuration

```python
from Researcher import Researcher
from langgraph.checkpoint.memory import MemorySaver

# Advanced configuration with custom settings
config = {
    "enable_web": True,
    "enable_vectordb": True,
    "enable_hybrid": True,
    "memory_saver": MemorySaver(),
    "run_name": "Advanced Research Session"
}

researcher = Researcher(config)

# Multi-turn conversation with specific instructions
results = researcher.search(
    query="Explain quantum computing principles",
    instructions="Provide technical details but make it accessible",
    max_num_turns=3,
    config={"reranker_top_k": 32}  # Runtime configuration override
)
```

## 📁 Project Structure

```
Researcher/
├── README.md                    # This file
├── setup.py                     # Package installation setup
├── requirements.txt             # Project dependencies
├── examples/                    # Usage examples
│   ├── simple_query.py         # Basic usage example
│   └── notebooks/              # Jupyter notebooks
│       └── testing.ipynb       # Interactive testing
├── src/Researcher/             # Main source code
│   ├── __init__.py             # Package initialization
│   ├── agent.py                # Main Researcher agent class
│   ├── config.yaml             # Configuration settings
│   ├── .env.example            # Environment template
│   ├── graph/                  # StateGraph implementation
│   │   ├── builder.py          # Graph construction
│   │   └── nodes/              # Graph node implementations
│   ├── models/                 # LLM model interfaces
│   │   ├── llm.py              # Base LLM interface
│   │   ├── openai.py           # OpenAI integration
│   │   ├── bedrock.py          # AWS Bedrock integration
│   │   └── google.py           # Google AI integration
│   ├── retrievers/             # Retrieval implementations
│   │   ├── base.py             # Base retriever class
│   │   ├── web.py              # Web search retriever
│   │   ├── wikipedia.py        # Wikipedia retriever
│   │   ├── vectordb.py         # Vector database retriever
│   │   ├── bm25.py             # BM25 retriever
│   │   ├── hybrid.py           # Hybrid retrieval
│   │   └── lightrag.py         # LightRAG retriever
│   ├── types/                  # Type definitions
│   │   ├── search_query.py     # Query type definitions
│   │   └── state.py            # State management types
│   └── utils/                  # Utility functions
│       ├── config.py           # Configuration utilities
│       ├── formatters.py       # Response formatting
│       ├── logging.py          # Logging configuration
│       └── prompts.py          # System prompts
└── tests/                      # Test suite
    ├── test_agent.py           # Agent tests
    ├── test_retrievers.py      # Retriever tests
    └── test_graph.py           # Graph tests
```

## 🔧 Customization

### Adding Custom Retrievers

Create a new retriever by inheriting from `BaseRetriever`:

```python
from Researcher.retrievers.base import BaseRetriever
from Researcher.types.search_query import SearchQuery

class MyCustomRetriever(BaseRetriever):
    def __init__(self):
        super().__init__(name="my_custom_retriever")
    
    def retrieve(self, query: SearchQuery) -> List[Dict[str, Any]]:
        # Implement your custom retrieval logic
        return search_results
```

### Custom Model Providers

Extend the LLM interface for new providers:

```python
from Researcher.models.llm import BaseLLM

class MyCustomLLM(BaseLLM):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def invoke(self, messages, **kwargs):
        # Implement your model invocation logic
        return response
```

## 📊 Performance Optimization

### Memory Optimization
- Adjust `top_k` parameters in retrievers to balance recall and memory usage
- Enable `use_fp16` for rerankers to reduce memory footprint
- Configure log rotation to manage disk space

### Speed Optimization
- Use faster models for query extraction (e.g., `gpt-4o-mini`)
- Enable `use_fp16` for FLAG rerankers
- Reduce `cutoff_layers` for layerwise rerankers
- Optimize `similarity_threshold` values

### Quality Optimization
- Increase `top_k` values for better recall
- Use more sophisticated reranking models
- Enable LLM filtering for critical applications
- Fine-tune hybrid search weights

## 🔍 Monitoring and Debugging

### Logging Configuration

```yaml
logging:
  level: "DEBUG"
  file: "researcher.log"
  format: "[%(asctime)s] [%(name)s] [%(levelname)s] [%(message)s]"
  rotation: "10MB"
  retention: "10 days"
  console_output: true
```

### LangSmith Integration

Enable tracing for detailed monitoring:

```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=researcher_project
LANGCHAIN_API_KEY=your_api_key
```

### Graph Visualization

Enable graph visualization for debugging:

```yaml
visualization: true
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
python -m pytest tests/

# Run specific test files
python -m pytest tests/test_agent.py -v

# Run with coverage
python -m pytest tests/ --cov=Researcher
```