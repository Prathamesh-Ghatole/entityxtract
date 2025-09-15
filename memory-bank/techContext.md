# Tech Context: entityxtract

## Languages and Runtime
- Python: 3.12

## Core Dependencies (from pyproject.toml)
- langchain, langchain-openai — LLM orchestration and OpenAI-compatible chat models
- pydantic (v2) — data models for configuration, entities, and results
- polars — columnar DataFrame operations and CSV export
- pillow (PIL) — image handling
- pypdfium2 — PDF processing (text/image extraction helpers)
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
- config.py — configuration resolution with precedence: ENV > YAML top-level > dotted path > deep search
- pdf/ — PDF to text/image utilities
- prompts/ — prompt templates: system.txt, table.txt, string.txt
- logging_config.py — logging setup helpers

## Configuration Strategy
- Preferred: Environment variables (migration in progress)
- Transitional: YAML config (config.yaml/config.yml) at project root; ENV overrides YAML
- Example keys (illustrative):
  - DEFAULT_MODEL
  - OPENAI_API_KEY, OPENAI_API_BASE
  - OPENROUTER.API_KEY, OPENROUTER.API_BASE

## Provider Model Guidance
- Provider-agnostic by design; works with multiple LLMs
- Current recommendation: Gemini 2.5 Flash for best results
- Roadmap:
  - Local inference via Ollama
  - Direct provider integrations for OpenAI, Gemini, Claude, etc.

## Build and Run
- Package metadata: name=entityxtract, version=0.4.4
- Script entry point: `llm-extractor = "entityxtract:main"` (function `main` not implemented yet)
- Environment management: uv recommended
  - Create config (transitional): copy example to active config and fill values
  - Install: `uv sync`
  - Run example: `uv run tests/test_extraction_1.py`

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
- Script entrypoint `entityxtract:main` pending
- YAML→ENV migration planned; prefer ENV-first to avoid YAML dependency
- Provider differences in FILE/IMAGE attachments may require adapter logic
- One-time annotation workflow to reduce repeated token usage is planned
