# PAKTON API Service

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Celery](https://img.shields.io/badge/Celery-37B24D?style=for-the-badge&logo=celery)](https://docs.celeryproject.org/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis)](https://redis.io/)
[![RabbitMQ](https://img.shields.io/badge/RabbitMQ-FF6600?style=for-the-badge&logo=rabbitmq)](https://www.rabbitmq.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker)](https://www.docker.com/)

## Overview

The PAKTON API service provides a RESTful interface for interacting with the PAKTON Multi-Agent Framework. Built with modern technologies, it enables asynchronous processing of complex tasks including document interrogation, research operations, and document indexing through a distributed microservices architecture.

**Key Features:**
- 🚀 **High-Performance API**: FastAPI-powered REST endpoints with automatic OpenAPI documentation
- 🔄 **Asynchronous Processing**: Celery-based distributed task queue for non-blocking operations
- 📊 **Real-time Task Monitoring**: Live status tracking and result retrieval
- 🏗️ **Microservices Architecture**: Containerized services with Docker Compose orchestration
- 🔒 **Production Ready**: Comprehensive error handling, retry logic, and logging

## Architecture

The service implements a modern, scalable microservices architecture:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│             │────▶│             │────▶│             │────▶│              │
│ API Client  │     │   FastAPI   │     │  RabbitMQ   │     │Celery Workers│
│             │     │   Service   │     │   Broker    │     │              │
└─────────────┘     └─────────────┘     └─────────────┘     └──────────────┘
                           │                                        │
                           │              ┌─────────────┐           │
                           └─────────────▶│    Redis    │◀──────────┘
                                          │   Backend   │
                                          └─────────────┘
```

### Core Components

- **FastAPI Service**: High-performance REST API with automatic documentation
- **Celery Workers**: Distributed task processing with retry mechanisms
- **RabbitMQ**: Message broker for reliable task distribution
- **Redis**: Result backend for task status and result storage
- **PAKTON Agents**: Specialized AI agents (Researcher, Interrogator, Archivist)

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Python 3.11+ (for development)
- Minimum 4GB RAM recommended
- Environment configuration files (see [Configuration](#configuration))

### Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd "PAKTON Framework/API"
   ```

2. **Configure environment variables and configuration files** (see [Configuration](#configuration) section):
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
   
   # Edit each config.yaml file with your API keys and configuration
   ```

3. **Start the services**:
   ```bash
   docker-compose up -d --build
   ```

4. **Verify deployment**:
   ```bash
   # Check service health
   curl http://localhost:5001/health
   
   # Access API documentation
   open http://localhost:5001/docs
   ```

## Authentication

The API supports **optional authentication** using Supabase JWT tokens. Authentication can be toggled via environment variable to facilitate development.

### Configuration

Set the `ENABLE_AUTHENTICATION` environment variable in your `.env` file:

```bash
# Production mode - Authentication REQUIRED
ENABLE_AUTHENTICATION=true

# Development mode - Authentication DISABLED
ENABLE_AUTHENTICATION=false
```

**Default**: `true` (authentication enabled)

### When Authentication is Enabled (`true`)

All API endpoints require a valid Supabase JWT token:

```bash
curl -X POST http://localhost:5001/query/sse \
  -H "Authorization: Bearer YOUR_SUPABASE_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello, world!"}'
```

**Protected Endpoints:**
- `POST /query/celery`
- `POST /query/sse`
- `POST /query/stream_steps/sse`
- `POST /index/document/`
- `POST /research/`
- `POST /interrogation/`
- `GET /task_status/{task_id}`

**Public Endpoints** (always accessible):
- `GET /` - Root/welcome
- `GET /health` - Health check

### When Authentication is Disabled (`false`)

No authentication required - useful for local development and testing:

```bash
curl -X POST http://localhost:5001/query/sse \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello, world!"}'
```

**Note**: When disabled, all requests are logged as `"anonymous (auth disabled)"`.

### Supabase Setup (Required if Authentication Enabled)

1. Create a Supabase project at [supabase.com](https://supabase.com)
2. Get your project URL from Settings → API
3. Add to `.env`:
   ```bash
   SUPABASE_URL=https://your-project-id.supabase.co
   ENABLE_AUTHENTICATION=true
   ```

For detailed authentication setup, see the [Authentication Documentation](#authentication-details).

## API Endpoints

### 🔍 Inference Operations

#### POST `/research/`
Execute comprehensive research operations using the Researcher agent.

**Request Body** (`ResearchRequest`):
```json
{
  "query": "What are the latest developments in quantum computing?",
  "instructions": "Focus on practical applications in cryptography",
  "agent_config": {
    "run_name": "Quantum Research Analysis"
  },
  "search_config": {
    "return_chunks": true,
    "max_results": 10
  }
}
```

**Response**:
```json
{
  "message": "Research operation started",
  "statusCode": 202,
  "data": {
    "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }
}
```

#### POST `/interrogation/`
Process queries with contextual analysis using the Interrogator agent.

**Request Body** (`InterrogationRequest`):
```json
{
  "userQuery": "Analyze the contract terms for compliance issues",
  "userContext": "Enterprise software licensing agreement",
  "userInstructions": "Focus on liability and termination clauses"
}
```

### 📄 Document Operations

#### POST `/index/document/`
Index documents with rich metadata for intelligent retrieval.

**Request Format**: `multipart/form-data`

**Example using curl**:
```bash
curl -X POST "http://localhost:5001/index/document/" \
  -F "metadata={\"title\":\"Technical Report\",\"author\":\"John Doe\",\"tags\":[\"research\",\"ai\"]}" \
  -F "file=@document.pdf"
```

**Supported Formats**: `.pdf`, `.docx`, `.txt`

### 📊 Task Management

#### GET `/task_status/{task_id}`
Monitor task progress and retrieve results.

**Response Example**:
```json
{
  "message": "Task status retrieved",
  "statusCode": 200,
  "data": {
    "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "task_status": "SUCCESS",
    "task_response": {
      "status": "SUCCESS",
      "message": "Research completed",
      "data": {
        "response": "Comprehensive research findings...",
        "chunks": [...]
      }
    }
  }
}
```

**Task Status Values**:
- `PENDING`: Task queued but not started
- `STARTED`: Currently processing
- `SUCCESS`: Completed successfully
- `FAILURE`: Task failed
- `RETRY`: Retrying after failure
- `REVOKED`: Cancelled before completion

### 🏥 Health Check

#### GET `/health`
Service health verification endpoint.

**Response**:
```json
{
  "status": "healthy"
}
```

## Configuration

### Environment Variables

Create a `.env` file with the following required variables:

```bash
# Service Configuration
SERVICE_NAME=multiagentframework_service

# Celery Configuration
CELERY_BROKER_URL=amqp://rabbitmq:5672
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Python Configuration
PYTHONUNBUFFERED=1
```

### Docker Compose Configuration

The `docker-compose.yml` file orchestrates the following services:

- **RabbitMQ**: Message broker (ports: 5672, 15672 for management UI)
- **Redis**: Result backend (port: 6379)
- **API Service**: FastAPI application (port: 5001)
- **Celery Workers**: Background task processors

### Service Ports

| Service | Port | Purpose |
|---------|------|---------|
| API Service | 5001 | REST API endpoints |
| RabbitMQ | 5672 | Message broker |
| RabbitMQ Management | 15672 | Web UI (guest/guest) |
| Redis | 6379 | Result backend |

## Development

### Local Development Setup

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Install local PAKTON packages**:
   ```bash
   pip install -e ../Archivist/
   pip install -e ../Researcher/
   pip install -e ../Interrogator/
   ```

3. **Start infrastructure services**:
   ```bash
   # Start only RabbitMQ and Redis
   docker-compose up rabbitmq redis -d
   ```

4. **Run API service locally**:
   ```bash
   uvicorn api:app --host 0.0.0.0 --port 5001 --reload
   ```

5. **Start Celery worker**:
   ```bash
   celery -A tasks.celery_app worker -Q multiagentframework_service_queue --loglevel=debug
   ```

### Testing

Run the test suite to validate API functionality:

```bash
# Run basic endpoint tests
python tests/test_api_calls.py

# Test specific endpoints
python -c "
from tests.test_api_calls import test_health_endpoint
test_health_endpoint()
"
```

### API Documentation

Once the service is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:5001/docs
- **ReDoc**: http://localhost:5001/redoc
- **OpenAPI Schema**: http://localhost:5001/openapi.json

## Project Structure

```
API/
├── api.py                 # FastAPI application and endpoints
├── tasks.py              # Celery task definitions
├── config.py             # Configuration management
├── response_template.py  # Response formatting utilities
├── logger.py             # Logging configuration
├── requirements.txt      # Python dependencies
├── docker-compose.yml    # Service orchestration
├── Dockerfile            # Container image definition
├── tests/
│   └── test_api_calls.py # API integration tests
└── README.md            # This file
```

## Error Handling & Monitoring

### Retry Mechanism
- **Automatic Retries**: Failed tasks are automatically retried up to 3 times
- **Exponential Backoff**: 5-second delay between retry attempts
- **Graceful Degradation**: Detailed error messages returned on final failure

### Logging
- **Structured Logs**: JSON-formatted logs with timestamps and severity levels
- **Docker Integration**: Logs accessible via `docker-compose logs`
- **Debug Mode**: Configurable log levels for development and production

### Monitoring Endpoints
- Health check: `GET /health`
- Task status: `GET /task_status/{task_id}`
- RabbitMQ Management UI: http://localhost:15672

## Production Deployment

### Docker Production Configuration

For production deployments:

1. **Update environment variables**:
   ```bash
   # Use production-ready broker and backend URLs
   CELERY_BROKER_URL=amqp://user:password@broker.example.com:5672
   CELERY_RESULT_BACKEND=redis://redis.example.com:6379/0
   ```

2. **Scale Celery workers**:
   ```bash
   docker-compose up --scale multiagentframework_worker=4
   ```

3. **Configure reverse proxy** (nginx example):
   ```nginx
   server {
       listen 80;
       server_name api.yourdomain.com;
       
       location / {
           proxy_pass http://localhost:5001;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

### Performance Tuning

- **Worker Concurrency**: Adjust `--concurrency` parameter based on CPU cores
- **Connection Pooling**: Configure Redis and RabbitMQ connection pools
- **Resource Limits**: Set Docker memory and CPU limits for containers

## Troubleshooting

### Common Issues

1. **Connection Refused Errors**:
   ```bash
   # Check if services are running
   docker-compose ps
   
   # Restart services if needed
   docker-compose restart
   ```

2. **Task Timeout Issues**:
   ```bash
   # Check Celery worker logs
   docker-compose logs multiagentframework_worker
   ```

3. **Memory Issues**:
   ```bash
   # Monitor resource usage
   docker stats
   ```

### Debug Mode

Enable debug logging:
```bash
# Set environment variable
export LOG_LEVEL=DEBUG

# Or modify logger.py
logging.basicConfig(level=logging.DEBUG)
```

## License

This project is licensed under the terms specified in the main PAKTON repository.

## Support

For issues and questions:
- **Email**: petrosrapto@gmail.com
- **Documentation**: http://localhost:5001/docs (when running)
- **Issues**: Create an issue in the repository
