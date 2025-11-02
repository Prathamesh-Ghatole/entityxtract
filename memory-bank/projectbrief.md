# Project Brief: entityxtract

## Purpose
Extract structured information from unstructured documents (PDF, DOCX, TXT, images, etc.) by defining custom entities with a schema, few-shot examples, and custom instructions. The framework is open source, provider-agnostic, and can work with any LLM.

## Product Positioning
Built as an **open-source alternative** to commercial solutions like:
- Google Cloud Document AI
- Azure AI Document Intelligence  
- Adobe PDF Extract
- Llama Extract (closed-source)

**Key Differentiators:**
- Open source (MIT License)
- Works with any LLM provider (not locked to single vendor)
- Schema + few-shot examples for consistent extraction
- Complete stack: Python SDK → REST API → Web UI

## Sample Flow (User Journey)
1. User provides a document (PDF, DOCX, TXT, image, etc.)
2. User defines entities to extract, each with:
   - Schema (fields and types)
   - Few-shot examples
   - Custom instructions
3. Choose input modes for processing:
   - FILE: Pass document as binary file attachment
   - TEXT: Extract and pass as plain text
   - IMAGE: Convert to images (useful for scanned docs)
   - Or combine multiple modes
4. Document is processed and sent to LLM using a prompt template
5. entityxtract returns structured JSON data for the requested entities
6. Results include token usage, costs (when enabled), and export to CSV/XLSX

**Recommended Model:** Gemini 2.5 Flash for best results

## Core Requirements

### Entity-First Extraction
- Users pre-define entities (tables/records/strings) with:
  - Schema (typed fields)
  - Few-shot examples (sample data)
  - Custom instructions (domain-specific guidance)

### Flexible Input Modes
- FILE: Pass document as binary attachment
- TEXT: Extract and pass plain text content
- IMAGE: Convert to images (PDF → page images)
- Support combinations of modes per job

### Provider-Agnostic Design
- Must work with any LLM via OpenAI-compatible APIs
- Common abstraction via LangChain
- Support for:
  - OpenRouter (multi-provider gateway)
  - OpenAI
  - Ollama (planned)
  - Any OpenAI-compatible endpoint

### Configuration (✅ v0.5.0)
- ✅ Environment-based configuration via `.env` files
- python-dotenv for automatic loading
- Required variables:
  - OPENAI_API_KEY
  - OPENAI_API_BASE
  - OPENAI_DEFAULT_MODEL
- `.env.sample` provided as template

### Interfaces
- ✅ Python SDK (current - v0.5.0)
- 🔄 REST API (planned - v0.6.0)
- 🔄 Web UI (planned - v0.7.0)
- ⚠️ CLI entrypoint declared but not implemented

### Reliability & Quality
- ✅ Enforce JSON output (no code fences)
- ✅ Retry with exponential backoff
- ✅ Token usage capture
- ✅ Optional cost estimation/tracking
- Clean, parseable JSON suitable for dataframes

### Concurrency
- ✅ Parallel extraction for multiple entities
- ThreadPoolExecutor with configurable `parallel_requests`
- Safe concurrent execution with result aggregation

### Outputs
- ✅ JSON-compatible structured outputs
- ✅ Export to CSV/XLSX
- ✅ Comprehensive metadata (tokens, costs, timestamps)
- Suitable for downstream data processing

### Observability
- ✅ Structured logging throughout
- ✅ Durable diagnostics
- ✅ Token and cost usage metrics
- Helpful for debugging and optimization

## Non-Goals (for now)
- Training/fine-tuning models
- Long-term storage or complex ETL orchestration beyond providing clean outputs
- Full OCR pipeline beyond current helpers
- Real-time streaming extraction
- Multi-tenant user management (single-user SDK focus)

## Success Criteria
- ✅ Example runs extract defined entities into structured JSON/CSV from sample documents
- ✅ Deterministic JSON payloads (no fenced code) that downstream tools can reliably parse
- ✅ Token and (optionally) cost reporting available when enabled
- ✅ Works with multiple providers; can switch models without major code changes
- Clean, documented codebase enabling community contributions
- Growing adoption and ecosystem

## Current Status (v0.5.0)
- ✅ Core SDK fully functional
- ✅ Configuration migrated to `.env`
- ✅ Comprehensive documentation
- ✅ PDF/TEXT/IMAGE support working
- ✅ Multi-entity parallel extraction
- ✅ Token/cost tracking operational
- ⚠️ CLI entrypoint missing implementation
- ❌ REST API not yet implemented
- ❌ Web UI not yet implemented

## Roadmap Highlights

### v0.6.0 - REST API
- FastAPI-based extraction service
- Job submission and management endpoints
- Entity schema CRUD operations
- Async extraction with status tracking
- OpenAPI/Swagger documentation

### v0.7.0 - Web UI & Advanced Features
- Visual entity schema editor
- Drag-and-drop document upload
- Real-time job monitoring
- Results preview and export
- Auto-detect mode for entity identification
- Deepseek OCR integration
- MCP server for agentic applications

### v0.8.0+ - Optimization & Expansion
- PyPI publishing
- Native Ollama integration
- Direct provider SDKs (OpenAI, Gemini, Claude)
- Annotation caching to reduce token usage
- Advanced cost optimization
- Benchmarking suite
- Additional entity types (hierarchical, key-value)

## Technical Foundations
- **Language**: Python 3.12+
- **Environment**: uv for package management
- **LLM Abstraction**: LangChain
- **Data Processing**: Polars (DataFrames)
- **PDF Processing**: pypdfium2
- **Configuration**: python-dotenv + .env files
- **Web Framework**: FastAPI (for API layer)
- **Type Safety**: Pydantic v2

## Setup Requirements (v0.5.0)
```bash
# 1. Clone repository
git clone https://github.com/Prathamesh-Ghatole/entityxtract.git
cd entityxtract

# 2. Install dependencies
uv sync

# 3. Configure environment
cp .env.sample .env
# Edit .env with your API credentials:
# - OPENAI_API_KEY
# - OPENAI_API_BASE
# - OPENAI_DEFAULT_MODEL

# 4. Run example
uv run tests/test.py
```

## License
MIT License - Free for commercial and personal use
