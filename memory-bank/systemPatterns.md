# System Patterns and Architecture: entityxtract

## Architecture Overview
- Modules (src/entityxtract/)
  - extractor.py — message construction, model invocation, retries, token/cost parsing, concurrent fan-out/fan-in.
  - extractor_types.py — Pydantic models for configuration, entities, results, and a `Document` abstraction (PDF/TEXT/IMAGE).
  - config.py — configuration resolution with precedence (ENV > YAML top-level > dotted path > deep search).
  - pdf/ — utilities for converting PDFs to text and images.
  - prompts/ — system and object-specific prompt templates (e.g., system.txt, table.txt, string.txt).
  - logging_config.py — logging setup and shared logger accessors.
- Data Flow
  1) Load `Document` (PDF/TEXT/IMAGE). For PDFs, derive text and page images lazily.
  2) Build prompts from templates and entity definitions (schema + few-shots + instructions).
  3) Compose a multimodal message (text, base64 images, and/or binary file) according to input modes.
  4) Invoke LLM, enforce JSON output, and clean/parse the response.
  5) Aggregate per-entity `ExtractionResult` objects into `ExtractionResults`.

## Key Domain Models (extractor_types.py)
- FileInputMode — {FILE, TEXT, IMAGE} toggles context shape sent to the model.
- ExtractionConfig — model parameters, retries, parallelism, input modes, cost tracking toggle.
- TableToExtract, StringToExtract — entity definitions, including example structures and instructions.
- ObjectsToExtract — collection of entities + shared config for a job.
- Document — lazy loader for file bytes, derived text, and images, with type detection (PDF/IMAGE/TEXT).
- ExtractionResult(s) — structured outputs with metadata (success, message, tokens, cost).

## Prompting and Messages
- Prompt Builders: System + entity-specific templates from prompts/.
- Message Composition (extractor.py):
  - Injects:
    - TEXT: document text appended into prompt.
    - IMAGE: base64-encoded JPEG(s) via `pil_img_to_base64`.
    - FILE: base64-encoded PDF bytes as a file attachment.
  - Produces a single `HumanMessage` payload combining attachments + text instructions.
- JSON Enforcement:
  - Uses LangChain’s ChatOpenAI with `response_format={"type": "json_object"}`.
  - Strips markdown code fences prior to JSON parsing.

## Execution Model and Resilience
- Single-Entity Extraction:
  - Retry with exponential backoff up to `max_retries`.
  - Robust parsing of token usage from `usage_metadata` and `response_metadata`.
- Multi-Entity Extraction:
  - ThreadPoolExecutor with `parallel_requests` to run per-entity in parallel.
  - Fan-in aggregation into `ExtractionResults` with totals (tokens, cost).
- Observability:
  - Centralized logging via `logging_config.py`.
  - Optional generation cost lookup (OpenRouter/OpenAI) for post-run accounting.

## Configuration Strategy
- Precedence: ENV > YAML (config.yaml/config.yml) top-level > dotted-key > deep search.
- Migration Direction: Move to ENV-first configuration while maintaining transitional YAML compatibility.
- Notable Keys (illustrative):
  - DEFAULT_MODEL
  - Provider credentials and bases: OPENAI_*, OPENROUTER_*

## Provider-Agnostic Design
- Primary interface via LangChain’s chat models.
- Works with multiple LLMs; current recommendation: Gemini 2.5 Flash.
- Attachments (FILE/IMAGE) must follow provider-specific semantics; abstraction keeps application code uniform.

## Logging and Diagnostics
- `setup_logging` initializes handlers and levels.
- `get_logger` used across modules for consistent structured logs.
- Metadata captured in results (tokens, cost, raw response payload subset for auditability).

## Extension Points
- New entity types beyond tables/strings (e.g., key-value records, hierarchical schemas).
- Additional input modes or hybrid strategies (first annotate → then extract).
- Provider adapters for local (Ollama) and direct SDK integrations (OpenAI, Gemini, Claude).
- API (FastAPI) and Web UI layers on top of the SDK.

## Risks and Considerations
- Provider Differences:
  - FILE/IMAGE attachment handling may vary; verify across backends and add adapters if needed.
- Config Footguns:
  - Absence of ENV/YAML yields FileNotFoundError; migration to ENV-first should reduce surprises.
- JSON Strictness:
  - Enforcing pure JSON output is essential; defense added via response format and code-fence stripping.
- Cost Efficiency:
  - Add a one-time document annotation step to avoid redundant token usage on repeated jobs.

## Testing and Example Usage
- Example scripts/tests demonstrate:
  - Defining entities (tables) with example data.
  - Choosing input modes.
  - Running extraction and exporting results (CSV/XLSX).
