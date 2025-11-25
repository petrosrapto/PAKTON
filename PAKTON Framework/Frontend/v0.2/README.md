# PAKTON Frontend v0.2

---

## Overview

PAKTON's Frontend v0.2 is built on the Open Canvas framework, providing an intuitive interface for interacting with PAKTON's AI-powered legal research system. This frontend connects seamlessly with the PAKTON API backend, enabling document upload, intelligent querying, and interactive chat capabilities.

> **🔗 Original Open Canvas**: The original framework can be found at [opencanvas.langchain.com](https://opencanvas.langchain.com/)

---

## 📸 Visual Showcase

### Original Open Canvas Interface
*The original frontend*

![Screenshot of the original frontend](./static/screenshot.png)

### PAKTON's Enhanced Interface
*Our custom implementation*

<div align="center">

<img src="./static/PAKTON_UI_1.png" alt="PAKTON UI - Main Interface" style="border-radius: 12px; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12); border: 1px solid rgba(0, 0, 0, 0.08); margin: 10px 0; max-width: 100%; height: auto;">

*Main PAKTON's page*

<img src="./static/PAKTON_UI_2.png" alt="PAKTON UI - Advanced Features" style="border-radius: 12px; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12); border: 1px solid rgba(0, 0, 0, 0.08); margin: 10px 0; max-width: 100%; height: auto;">

*Document upload and chat*

</div>

## Key Differences from Open Canvas

PAKTON's frontend implementation differs from the original Open Canvas in several ways:

1. **Custom Backend Integration**: Removed LangGraph server dependencies and integrated with PAKTON's custom API backend (Archivist, Interrogator, Researcher modules)
2. **Document-Centric Workflow**: Enhanced document upload and management capabilities tailored for legal research
3. **Simplified Architecture**: Streamlined to focus on core PAKTON functionality without the full LangGraph agent infrastructure
4. **Authentication**: Supabase-based authentication with support for Google OAuth

## Features

- **Document Upload & Management**: Upload legal documents and build a searchable knowledge base
- **Interactive Chat Interface**: Query documents and get AI-powered responses from PAKTON's backend
- **Authentication**: Secure user authentication via Supabase (Email/Password, Google OAuth)
- **Markdown & Code Support**: View and edit both markdown and code artifacts
- **Live Markdown Rendering**: Real-time markdown preview while editing
- **LangSmith Integration**: Optional tracing and observability for debugging (feedback and run sharing)

## Architecture

The frontend communicates with the following PAKTON backend services:

- **PAKTON API (Archivist)**: Document ingestion, indexing, and query processing
- **Supabase**: User authentication and document storage
- **LangSmith** (Optional): Tracing and feedback collection

## Setup locally

This guide will cover how to setup and run PAKTON's Frontend locally.

### Prerequisites

PAKTON Frontend requires the following:

#### Package Manager

- [Yarn](https://yarnpkg.com/)

#### Backend Services

- **PAKTON API**: The backend API must be running (see `PAKTON Framework/API/README.md`)
  - Default: `http://localhost:5001`
  
#### APIs (Optional Features)

- [OpenAI API key](https://platform.openai.com/signup/) - Required for AI features
- [Anthropic API key](https://console.anthropic.com/) - Alternative LLM provider
- (optional) [Google GenAI API key](https://aistudio.google.com/apikey)
- (optional) [Fireworks AI API key](https://fireworks.ai/login)
- (optional) [Groq AI API key](https://groq.com) - Audio/video transcription
- (optional) [FireCrawl API key](https://firecrawl.dev) - Web scraping
- (optional) [ExaSearch API key](https://exa.ai) - Web search

#### Authentication

- [Supabase](https://supabase.com/) account for user authentication
- [Supabase](https://supabase.com/) account/project for document uploads (can be the same or separate)

#### Observability (Optional)

- [LangSmith](https://smith.langchain.com/) for tracing, feedback, and run sharing

### Installation

First, ensure you have the **PAKTON API backend running** (see `PAKTON Framework/API/README.md`).

Next, install the frontend dependencies:

```bash
yarn install
```

After installing dependencies, copy the `.env.example` file into `.env` and set the required values:

```bash
cp .env.example .env
```

Edit the `.env` file with your configuration:

```bash
# Set to "true" when running locally
LOCAL_DEVELOPMENT="true"

# PAKTON API URL (Archivist backend)
NEXT_PUBLIC_ARCHIVIST_API_URL=http://localhost:5001

# Supabase for authentication
NEXT_PUBLIC_SUPABASE_URL=<your-supabase-url>
NEXT_PUBLIC_SUPABASE_ANON_KEY=<your-supabase-anon-key>

# Supabase for document storage (can be same as above)
NEXT_PUBLIC_SUPABASE_URL_DOCUMENTS=<your-supabase-url-documents>
NEXT_PUBLIC_SUPABASE_ANON_KEY_DOCUMENTS=<your-supabase-anon-key-documents>

```

Then, setup authentication with Supabase.

### Setup Authentication

After creating a Supabase account, visit your [dashboard](https://supabase.com/dashboard/projects) and create a new project.

Next, navigate to the `Project Settings` page inside your project, and then to the `API` tag. Copy the `Project URL`, and `anon public` project API key. Paste them into the `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` environment variables in the `apps/web/.env` file.

After this, navigate to the `Authentication` page, and the `Providers` tab. Make sure `Email` is enabled (also ensure you've enabled `Confirm Email`). You may also enable `GitHub`, and/or `Google` if you'd like to use those for authentication. (see these pages for documentation on how to setup each provider: [GitHub](https://supabase.com/docs/guides/auth/social-login/auth-github), [Google](https://supabase.com/docs/guides/auth/social-login/auth-google))

#### Test authentication

To verify authentication works, run `yarn dev` from the `apps/web` directory and visit [localhost:3000](http://localhost:3000). This should redirect you to the [login page](http://localhost:3000/auth/login). From here, you can either login with Google (if configured), or navigate to the [signup page](http://localhost:3000/auth/signup) and create a new account with an email and password. After confirming your email, you should be redirected to the [home page](http://localhost:3000).

### Running the Application

**Important**: Before starting the frontend, ensure the PAKTON API backend is running on `http://localhost:5001` (or your configured URL).

From the `apps/web` directory, run:

```bash
yarn dev
```

The application will be available at [localhost:3000](http://localhost:3000).

On initial load, compilation may take a little bit of time.

## LLM Models

PAKTON is designed to work with multiple LLM providers. Configure your preferred models in the environment:

- **Anthropic Claude**: Haiku, Sonnet, and Opus models for various tasks. Sign up at [console.anthropic.com](https://console.anthropic.com/)
- **OpenAI**: GPT-4o, GPT-4o Mini, and other models. Sign up at [platform.openai.com](https://platform.openai.com/signup/)
- **Fireworks AI**: Access to Llama and other open source models. Sign up at [fireworks.ai](https://fireworks.ai/login)
- **Google GenAI**: Gemini models. Get an API key at [aistudio.google.com](https://aistudio.google.com/apikey)

### Local Ollama models

PAKTON supports calling local LLMs running on Ollama. This is not enabled in hosted deployments but can be used in your own local instance.

To use a local Ollama model:

1. Install [Ollama](https://ollama.com)
2. Pull a model that supports tool calling: `ollama pull llama3.3`
3. Start the Ollama server: `ollama run llama3.3`
4. Set environment variables:
   - `NEXT_PUBLIC_OLLAMA_ENABLED=true`
   - `OLLAMA_API_URL=http://host.docker.internal:11434` (or your custom URL)

> [!NOTE]
> Open source LLMs typically have weaker instruction following than proprietary models like GPT-4o or Claude Sonnet, which may result in errors or unexpected behavior.

## Troubleshooting

Below are some common issues you may encounter:

- **Cannot connect to backend API**: Ensure the PAKTON API is running on the configured URL (default: `http://localhost:5001`). Check the `NEXT_PUBLIC_ARCHIVIST_API_URL` environment variable.

- **Authentication errors**: Verify your Supabase credentials are correctly set in the `.env` file. Make sure you've enabled the authentication providers (Email, Google) in your Supabase project settings.

- **Document upload failures**: Check that your Supabase documents project is configured correctly and the storage bucket exists. Verify the `NEXT_PUBLIC_SUPABASE_URL_DOCUMENTS` and `NEXT_PUBLIC_SUPABASE_ANON_KEY_DOCUMENTS` are correct.

- **"Missing API key" errors**: Some features require API keys (OpenAI, Anthropic, etc.). Make sure these are configured in your PAKTON API backend environment.

- **Port already in use**: If port 3000 is already in use, you can specify a different port: `yarn dev --port 3001`

## Docker Deployment

PAKTON Frontend can be deployed using Docker. See the `docker-compose.yml` and `Dockerfile` in the root directory for configuration details.

## Additional Resources

- **PAKTON API Documentation**: See `PAKTON Framework/API/README.md`
- **Archivist Module**: See `PAKTON Framework/Archivist/README.md`
- **Interrogator Module**: See `PAKTON Framework/Interrogator/README.md`
- **Researcher Module**: See `PAKTON Framework/Researcher/README.md`
