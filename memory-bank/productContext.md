# Product Context: entityxtract

## Why this exists
Organizations routinely need to extract structured information from unstructured documents (PDF, DOCX, TXT, etc.). Manual extraction is slow and error-prone. entityxtract enables users to declaratively define custom entities with a schema, few-shot examples, and custom instructions, then reliably extract them using any LLM.

## Target Users
- Data/analytics engineers embedding extraction into pipelines
- Platform/integration teams exposing extraction as internal services
- Analysts automating repeatable extractions with consistent schemas
- Developers building custom workflows that require provider-agnostic LLM extraction

## How it should work (User Experience)
- Python SDK (current)
  - Create a Document from a file path
  - Define entities to extract (schema, few-shot examples, custom instructions)
  - Choose input modes for the prompt: FILE, TEXT, IMAGE, or combinations
  - Invoke extraction and receive structured JSON results (tables, records, strings)
- REST API (planned/in progress)
  - Endpoints to submit extraction jobs, manage entity schemas, monitor status, and retrieve results
- Web UI (planned/in progress)
  - Define and manage entities/schemas with examples and instructions
  - Run and monitor extraction jobs
  - Preview results and export to CSV/XLSX

## Product Principles
- Entity-first, schema-driven extraction
- Provider-agnostic: works with any LLM via a clean abstraction
- Reproducible and evaluable results (clean JSON without code fences)
- Efficient operation with concurrency and optional cost awareness
- Composable building blocks for SDK, API, and UI

## Similar Tools and Differentiation
- Similar to Llama Extract in intention
- Differentiators:
  - Open source
  - Provider-agnostic (any LLM)
  - Focused on schema + examples + instructions for consistency
  - Roadmap includes UI and REST API alongside the Python SDK

## Recommendations
- Model: Gemini 2.5 Flash is currently recommended for best results

## Future Additions
- Local inference: Ollama support
- Direct provider SDK support: OpenAI, Gemini, Claude, etc.
- One-time annotation phase to reduce repeated token usage and costs
- ENV-first configuration (migration away from YAML)

## Setup (current)
- Use uv for environment management
- Copy example config to active config (transitional; ENV-first migration planned)
- `uv sync` to install
- Run example: `uv run tests/test_extraction_1.py`

As the project evolves, the REST API and UI will formalize and improve end-user experience (job orchestration, visual schema editing, result inspection).
