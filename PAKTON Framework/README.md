# PAKTON Framework: Multi-Agent Framework for Question Answering in Long Legal Agreements

## 🏗️ System Architecture

PAKTON is structured as a modular system with the following key components:

```
PAKTON Framework/
├── API/                   # FastAPI service for REST endpoints
├── Archivist/             # Document indexing and management
├── Interrogator/          # Query processing and analysis
├── Researcher/            # Information gathering and synthesis
└── Frontend/              # User interface implementations
    ├── v0.1/              # Streamlit-based interface
    └── v0.2/              # Open Canvas-based interface (Beta)
```

## 📋 Component Descriptions

### API
**FastAPI-based RESTful service providing centralized access to all PAKTON components**

**Location:** `API/`

**Key Features:**
- **Research Operations**: Execute research queries using the Researcher agent
- **Interrogation Operations**: Process complex user queries via the Interrogator agent
- **Document Indexing**: Upload and index documents with metadata
- **Asynchronous Task Processing**: Handle long-running operations with Celery
- **Task Status Tracking**: Monitor operation progress with unique task IDs
- **Health Monitoring**: Service health check endpoints

**Key Files:**
- `api.py` - Main FastAPI application with endpoints
- `tasks.py` - Celery task definitions for async processing
- `config.py` - Configuration management
- `response_template.py` - Standardized API response formatting
- `docker-compose.yml` - Container orchestration

**Dependencies:**
- FastAPI, Uvicorn for web framework
- Celery, Redis for async task processing
- RabbitMQ for message queuing
- Python-multipart for file uploads

**API Endpoints:**
- `POST /research/` - Execute research operations
- `POST /interrogation/` - Process user queries
- `POST /index/document/` - Index documents with metadata
- `GET /task_status/{task_id}` - Check task status
- `GET /health` - Health check

---

### 📚 Archivist
**Document management system for storage, indexing, and retrieval of information sources**

**Location:** `Archivist/`

**Architecture:**
```
src/Archivist/
├── agent.py              # Main Archivist agent
├── config.example.yaml   # Configuration settings
├── graph/                # LangGraph workflow definitions
│   ├── builder.py        # Graph construction
│   └── nodes/            # Individual processing nodes
├── indexers/             # Document indexing implementations
│   ├── base.py           # Base indexer interface
│   ├── vectordb.py       # Vector database indexing
│   └── lightrag.py       # LightRAG integration
├── models/               # AI model integrations
│   ├── openai.py         # OpenAI models
│   ├── bedrock.py        # AWS Bedrock models
│   ├── local.py          # Local model support
│   └── bert.py           # BERT support
├── parser/               # Document parsing
│   ├── naiveParser.py    # Basic text extraction
│   └── structuralParser.py # Advanced structure parsing
├── types/                # Type definitions
└── utils/                # Utility functions
```

**Key Capabilities:**
- Multi-format document processing (PDF, DOCX, TXT)
- Vector database indexing with Pinecone integration
- LightRAG knowledge graph construction
- Flexible indexer architecture supporting multiple backends
- Structural and semantic document parsing
- Configurable AI model support (OpenAI, AWS Bedrock, Local models)

**Dependencies:**
- LangChain ecosystem for AI workflows
- Pinecone for vector storage
- PyPDF and python-docx for document parsing
- Multiple AI model providers

---

### 🔍 Interrogator
**Specialized agent for processing and analyzing complex user queries with contextual understanding**

**Location:** `Interrogator/`

**Architecture:**
```
src/Interrogator/
├── agent.py              # Main Interrogator agent
├── config.example.yaml   # Configuration settings
├── graph/                # LangGraph workflow for query processing
├── models/               # AI model integrations
├── types/                # Type definitions and state management
└── utils/                # Utility functions and logging
```

**Key Capabilities:**
- Complex query understanding and intent analysis
- Contextual query processing with user instructions
- Multi-step reasoning workflows using LangGraph
- Memory-aware conversation handling
- Integration with knowledge retrieval systems
- Configurable response generation

**Core Functionality:**
- **Query Analysis**: Breaks down complex user queries into processable components
- **Context Integration**: Incorporates user-provided context and instructions
- **Reasoning Workflow**: Executes multi-step analysis using graph-based workflows
- **Response Synthesis**: Generates comprehensive answers with conclusions and reports

---

### 🔬 Researcher
**Agent responsible for conducting thorough information gathering and synthesis across various knowledge sources**

**Location:** `Researcher/`

**Architecture:**
```
src/Researcher/
├── agent.py              # Main Researcher agent
├── config.example.yaml   # Configuration settings
├── graph/                # LangGraph workflow for research operations
├── models/               # AI model integrations
├── retrievers/           # Information retrieval implementations
│   ├── wikipedia.py      # Wikipedia search
│   ├── web.py            # Web search capabilities
│   ├── vectordb.py       # Vector database retrieval
│   ├── bm25.py           # BM25 text search
│   ├── hybrid.py         # Hybrid retrieval strategies
│   └── lightrag.py       # LightRAG integration
├── types/                # Type definitions
└── utils/                # Utility functions
```

**Key Capabilities:**
- **Multi-Source Retrieval**: Wikipedia, web search, vector databases, BM25
- **Hybrid Search Strategies**: Combines multiple retrieval methods
- **LightRAG Integration**: Advanced knowledge graph retrieval
- **Configurable Retrieval**: Flexible search configuration options
- **Information Synthesis**: Processes and combines information from multiple sources
- **Research Workflow**: Systematic approach to information gathering

**Supported Retrievers:**
- WikipediaRetriever: Encyclopedia knowledge access
- WebRetriever: Real-time web search
- VectorDBRetriever: Semantic similarity search
- BM25RetrieverWrapper: Traditional text search
- HybridRetriever: Combined retrieval strategies
- LightRAGRetriever: Knowledge graph-based retrieval

---

### 🖥️ Frontend
**User interface implementations for interacting with the PAKTON system**

**Location:** `Frontend/`

#### v0.1 - Streamlit Interface
**Stable production interface built with Streamlit**

**Location:** `Frontend/v0.1/`

**Features:**
- Clean, intuitive chat interface
- Document upload functionality with metadata
- Real-time task status monitoring
- Support for PDF, DOCX, and TXT files
- Light theme with professional styling
- Integrated with PAKTON API endpoints

**Key Files:**
- `chat.py` - Main Streamlit application
- `requirements.txt` - Python dependencies
- `docker-compose.yml` - Container setup
- `.streamlit/config.toml` - Streamlit configuration

#### v0.2 - Open Canvas Interface (Beta)
**Advanced interface built on the Open Canvas framework**

**Location:** `Frontend/v0.2/`

**Features:**
- Modern React-based user interface
- Enhanced visualization capabilities
- Advanced document interaction features
- Improved user experience design
- Mobile-responsive layout

**Architecture:**
- React/TypeScript frontend
- LangGraph API integration
- Containerized deployment
- Nginx reverse proxy setup

**Status:** Beta - Under active development

## 🚀 Setup Instructions

### Prerequisites
- Docker and Docker Compose
- Python 3.10 or higher
- Node.js 16+ (for Frontend v0.2)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "PAKTON Framework"
   ```

2. **Set up environment variables and configuration files**
   ```bash
   # Copy example environment files
   cp Archivist/src/Archivist/.env.example Archivist/src/Archivist/.env
   cp Interrogator/src/Interrogator/.env.example Interrogator/src/Interrogator/.env
   cp Researcher/src/Researcher/.env.example Researcher/src/Researcher/.env
   
   # Edit each .env file with your API keys and configuration

   # Copy example configuration files
   cp Archivist/src/Archivist/config.example.yaml Archivist/src/Archivist/config.yaml
   cp Interrogator/src/Interrogator/config.example.yaml Interrogator/src/Interrogator/config.yaml
   cp Researcher/src/Researcher/config.example.yaml Researcher/src/Researcher/config.yaml
   
   # Edit each config.yaml file with your configuration settings
   ```

3. **Start the API service**
   ```bash
   cd API
   docker-compose up -d --build
   ```

4. **Launch the Frontend (v0.1)**
   ```bash
   cd Frontend/v0.1
   docker-compose up -d --build
   ```

### Component-Specific Setup

Each component contains detailed setup instructions:
- **API**: See `API/README.md`
- **Archivist**: See `Archivist/README.md`
- **Interrogator**: See `Interrogator/README.md`
- **Researcher**: See `Researcher/README.md`
- **Frontend v0.1**: See `Frontend/v0.1/README.md`
- **Frontend v0.2**: See `Frontend/v0.2/README.md`

### Setting up LIGHT_RAG (Optional)

If you enable LIGHT_RAG retrieval in PAKTON, you can set it up as follows:

```bash
# Clone the LIGHT_RAG repository
git clone https://github.com/HKUDS/LightRAG.git
cd LightRAG

# Create environment file from template and add your API keys
cp env.example .env
# Edit .env file with your preferred text editor to add API keys

# Build and start the LIGHT_RAG services
docker-compose up -d --build
```

## 🔧 Configuration

Each component uses YAML configuration files and environment variables:

- **API**: REST endpoint configuration, Celery settings
- **Archivist**: Indexer settings, model configurations
- **Interrogator**: Query processing parameters, model selection
- **Researcher**: Retriever configurations, search parameters

## 🤝 Contributing

Please read `CONTRIBUTING.md` for details on our code of conduct and the process for submitting pull requests.

## 📄 License

This project is licensed under the terms specified in the `LICENSE` file.

## 📧 Contact

**Author**: Petros Raptopoulos  
**Email**: petrosrapto@gmail.com

---

*For detailed technical documentation, API specifications, and usage examples, please refer to the individual component README files.*