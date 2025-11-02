# Tech Context: entityxtract

## Languages and Runtime
- Python: 3.12+

## Core Dependencies (from pyproject.toml v0.5.0)
- langchain, langchain-openai — LLM orchestration and OpenAI-compatible chat models
- pydantic (v2) — data models for configuration, entities, and results
- polars — columnar DataFrame operations and CSV export
- pillow (PIL) — image handling
- pypdfium2 — PDF processing (text/image extraction helpers)
- python-dotenv — environment variable management
- requests — HTTP calls (e.g., cost lookup)
- xlsxwriter — optional spreadsheet export
- fastapi[standard] — planned REST API layer (not wired end-to-end yet)

## Repository Layout (src/entityxtract/)
- extractor.py — constructs prompts/messages, invokes model, retries/backoff, token/cost parsing, concurrency
- extractor_types.py — Pydantic models:
  - FileInputMode: FILE, TEXT, IMAGE
  - ExtractionConfig: model, temperature, retries, parallelism, input modes, cost tracking
  - TableToExtract, StringToExtract: entity definitions (schema/examples/instructions)
  - ObjectsToExtract: collection of entities + shared config
  - Document: lazy loading of binary/text/images, type detection (PDF/IMAGE/TEXT)
  - ExtractionResult(s): structured results with metadata
- config.py — configuration resolution with precedence: ENV variables only
- pdf/ — PDF to text/image utilities
- prompts/ — prompt templates: system.txt, table.txt, string.txt
- logging_config.py — logging setup helpers

## Configuration Strategy (✅ Migration Complete)
- ✅ **Environment variables ONLY** - YAML config deprecated and removed
- `.env` file at project root with `.env.sample` as template
- Configuration keys (examples):
  - OPENAI_API_KEY — API key for OpenAI-compatible endpoints
  - OPENAI_API_BASE — Base URL (e.g., https://openrouter.ai/api/v1, https://api.openai.com/v1)
  - OPENAI_DEFAULT_MODEL — Default model name (e.g., google/gemini-2.5-flash)
- python-dotenv automatically loads `.env` file on startup
- No more YAML config files (config.yml/config.yaml) - fully deprecated

## Provider Model Guidance
- Provider-agnostic by design; works with any OpenAI-compatible LLM endpoint
- Current recommendation: Gemini 2.5 Flash for best results
- Supported providers:
  - OpenRouter (multi-provider gateway)
  - OpenAI
  - Any OpenAI-compatible endpoint (Ollama, LM Studio, etc.)
- Roadmap:
  - Local inference via Ollama (direct integration)
  - Native adapters for OpenAI, Gemini, Claude SDKs
  - Deepseek OCR integration

## Build and Run
- Package metadata: name=entityxtract, version=0.5.0
- Script entry point: `llm-extractor = "entityxtract:main"` (function `main()` not yet implemented)
- Environment management: uv recommended
  - Setup: Copy `.env.sample` to `.env` and fill values
  - Install: `uv sync`
  - Run example: `uv run tests/test.py`

## Data Flow Overview
1) Input document (PDF/DOCX/TXT/IMAGE) → `Document` abstraction
2) Optional derivations: PDF → text/images
3) Prompt assembly: system + entity-specific template with schema, few-shots, instructions
4) Message composition based on input modes (FILE/TEXT/IMAGE)
5) LLM invocation with JSON response enforcement
6) JSON parse and normalization → `ExtractionResult(s)` aggregation
7) Optional export (CSV/XLSX) via downstream utilities

## Observability
- Centralized logging (`setup_logging`, `get_logger`)
- Token usage capture (input/output)
- Optional cost lookup (e.g., OpenRouter/OpenAI generation endpoint) when enabled

## Current Gaps and Considerations
- REST API (FastAPI) and Web UI not implemented end-to-end yet
- Script entrypoint `entityxtract:main` declared but `main()` function missing from `__init__.py`
- Provider differences in FILE/IMAGE attachments may require adapter logic
- One-time annotation workflow to reduce repeated token usage is planned

## Roadmap Highlights
- 🖥️ Web UI for visual entity/schema management and job monitoring
- 🔍 Auto-detect mode to automatically identify extractable entities
- 👁️ Deepseek OCR integration for enhanced document processing
- 🔌 MCP server for agentic applications
- 📦 PyPI publishing for `pip install entityxtract`
