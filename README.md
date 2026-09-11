# AI Codebase Analyzer — Backend Engine

A high-performance backend system for comprehensive codebase intelligence, AST parsing, call and dependency graph analysis, semantic vector indexing, and grounded AI question answering.

---

## Architecture Overview

```
                        +---------------------------------------------+
                        |           FastAPI Web Service               |
                        +---------------------------------------------+
                               /              |             \
                              /               |              \
                             v                v               v
            +--------------------+  +------------------+  +--------------------+
            | AST Code Analysis  |  | Graph Processing |  |  Vector Indexing   |
            |   (Tree-sitter)    |  |  & Dependencies  |  |   & Embeddings     |
            +--------------------+  +------------------+  +--------------------+
                     |                        |                     |
                     |                        |                     v
                     v                        v            +-------------------+
            +--------------------+  +------------------+   | ChromaDB Storage  |
            | Hierarchical LLM   |  | Import & Call    |   +-------------------+
            |   Summarization    |  | Graph Engine     |            |
            +--------------------+  +------------------+            v
                     \                        /            +-------------------+
                      \                      /             | Hybrid Retrieval  |
                       v                    v              +-------------------+
            +------------------------------------------+            |
            | Grounded Q&A Service with Line Citations |<-----------+
            +------------------------------------------+
```

---

## Key Features

1. **Repository Ingestion & Discovery**
   - Automated cloning of remote Git repositories or ingestion of local projects.
   - Intelligent file discovery respecting `.gitignore`, binary exclusions, and vendor paths.

2. **AST Parsing & Code Entity Extraction**
   - Powered by Tree-sitter for multi-language parsing (Python, JavaScript/TypeScript, Go, Java, Rust).
   - Extracts functions, classes, methods, parameters, return types, docstrings, imports, and call signatures.

3. **Call & Dependency Graph Analysis**
   - Reconstructs internal import trees and inter-file dependency topologies.
   - Maps callers to callees across project modules.

4. **Hierarchical Code Summarization**
   - Multi-tier summarization: `Function -> File -> Module -> Project Architecture`.
   - Batched LLM processing with rate-limiting and fallback support across multiple providers.

5. **Semantic Vector Indexing (ChromaDB + Gemini Embeddings)**
   - Smart code chunking enriched with file, module, and AST metadata.
   - 768-dimensional vector embeddings generated via `gemini-embedding-001`.
   - Fast, persistent vector storage via ChromaDB.

6. **Contextual Retrieval & Grounded Q&A (RAG)**
   - Question classification engine identifying intent (architectural, lookup, debugging, implementation).
   - Multi-strategy hybrid search combining semantic similarity and AST entity matching.
   - Grounded answering system with file and line-range citations.

7. **Multi-Provider LLM Flexibility**
   - Out-of-the-box support for **Groq** (Llama 3.3 / compound models), **Google Gemini** (Gemini 1.5/2.0 Flash), **OpenAI** (GPT-4o/mini), and local **Ollama** models.

---

## Tech Stack

- **Framework**: FastAPI, Uvicorn, Starlette
- **Data Validation & Schemas**: Pydantic v2
- **Vector Database**: ChromaDB
- **Embeddings**: Google Generative AI (`google-genai` / `gemini-embedding-001`)
- **LLM Integrations**: Groq SDK, Google Gemini SDK, OpenAI SDK, Ollama REST
- **AST Parsing**: Tree-sitter
- **Git Operations**: GitPython

---

## Prerequisites

- **Python 3.10+**
- **Git** installed and available in your `PATH`
- API Key(s) for your desired model provider:
  - **Google Gemini API Key** (required for vector embeddings)
  - **Groq API Key** (recommended for ultra-fast summarization and chat)
  - *Optional*: OpenAI API Key or a local Ollama instance

---

## Installation & Setup

### 1. Clone the repository
```bash
git clone <repository_url>
cd backend
```

### 2. Set up virtual environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your keys:
```bash
# Windows PowerShell
Copy-Item .env.example .env

# macOS / Linux
cp .env.example .env
```

Edit `.env`:
```env
# Selected LLM provider: groq | gemini | openai | ollama
LLM_PROVIDER=groq

# Groq API Key (for LLM inference)
GROQ_API_KEY=gsk_your_groq_api_key

# Google Gemini API Key (required for embeddings)
GEMINI_API_KEY=AIzaSy_your_gemini_api_key

# Optional keys
OPENAI_API_KEY=sk_your_openai_api_key
OLLAMA_BASE_URL=http://localhost:11434
```

---

## Running the Server

Start the FastAPI application using Uvicorn:
```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at:
- **Base URL**: `http://localhost:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## API Endpoints Reference

### 1. Repository Management & Analysis
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/repository/clone` | Clones a GitHub repo and registers it |
| `POST` | `/api/repository/local` | Ingests and registers a local directory |
| `POST` | `/api/repository/analyze` | Runs AST parsing, metric extraction, and file discovery |

### 2. Dependency & Call Graphs
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/graphs/dependencies/{project_id}` | Returns file-level import dependency graph |
| `GET` | `/api/graphs/call-graph/{project_id}` | Returns function-level caller-callee call graph |

### 3. Codebase Understanding & Summarization
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/understanding/summarize` | Triggers hierarchical LLM code summarization |
| `GET` | `/api/understanding/project/{project_id}` | Fetches project-level architecture overview |
| `GET` | `/api/understanding/modules/{project_id}` | Fetches module-level summaries |
| `GET` | `/api/understanding/files/{project_id}` | Fetches file-level summaries and function breakdowns |

### 4. Vector Indexing & Search
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/search/index` | Chunks codebase and stores embeddings in ChromaDB |
| `POST` | `/api/search/query` | Executes semantic or hybrid search across code chunks |

### 5. Grounded Q&A (RAG)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/retrieval/context` | Retrieves ranked code slices for a question |
| `POST` | `/api/answer/ask` | Answers technical queries with line citations and references |

---

## Project Structure

```
backend/
├── app/
│   ├── api/                   # FastAPI route controllers
│   │   ├── answer.py          # Grounded AI Q&A endpoints
│   │   ├── graphs.py          # Dependency and call graph endpoints
│   │   ├── repository.py      # Repository ingestion & analysis endpoints
│   │   ├── retrieval.py       # Context retrieval endpoints
│   │   ├── search.py          # Vector search endpoints
│   │   └── understanding.py   # Hierarchical summarization endpoints
│   ├── prompts/               # Prompt templates for LLMs
│   ├── schemas/               # Pydantic request/response validation models
│   ├── services/              # Core business and computational services
│   │   ├── answer_service.py      # Synthesizes answers with citations
│   │   ├── call_extractor.py      # AST call extraction
│   │   ├── code_chunker.py        # Semantic chunking engine
│   │   ├── document_enricher.py   # AST metadata enrichment
│   │   ├── embedding_service.py   # Vector embedding generator
│   │   ├── function_extractor.py  # Function extraction & AST parsing
│   │   ├── indexing_service.py    # ChromaDB indexing pipeline
│   │   ├── llm_client.py          # Unified multi-provider LLM interface
│   │   ├── question_classifier.py # Query intent classifier
│   │   ├── search_service.py      # Hybrid vector search service
│   │   └── vector_store.py        # ChromaDB client wrapper
│   └── main.py                # Application entrypoint & CORS middleware
├── chroma_db/                 # Local vector store data (ignored in git)
├── repositories/              # Cloned repositories cache (ignored in git)
├── .env.example               # Template environment configuration
├── .gitignore                 # Git ignore rules
└── requirements.txt           # Python package requirements
```

---

## License

This project is licensed under the MIT License.
