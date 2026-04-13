# System Patterns and Architecture: entityxtract

## Architecture Overview
- Modules (src/entityxtract/)
  - extractor.py — message construction, model invocation, retries, token/cost parsing, concurrent fan-out/fan-in
  - extractor_types.py — Pydantic models for configuration, entities, results, and a `Document` abstraction (PDF/TEXT/IMAGE)
  - config.py — configuration resolution from environment variables only
  - pdf/ — utilities for converting PDFs to text and images
  - prompts/ — system and object-specific prompt templates (e.g., system.txt, table.txt, string.txt)
  - logging_config.py — logging setup and shared logger accessors
- Data Flow
  1) Load `Document` (PDF/TEXT/IMAGE). For PDFs, derive text and page images lazily
-  2) Optionally trim PDF bytes in-memory during `Document` construction using `page_range`
  3) Build prompts from templates and entity definitions (schema + few-shots + instructions)
  4) Compose a multimodal message (text, base64 images, and/or binary file) according to input modes
  5) Invoke LLM, enforce JSON output, and clean/parse the response
  6) Aggregate per-entity `ExtractionResult` objects into `ExtractionResults`

## Key Domain Models (extractor_types.py)
- FileInputMode — {FILE, TEXT, IMAGE} toggles context shape sent to the model
- ExtractionConfig — model parameters, retries, parallelism, input modes, cost tracking toggle
- TableToExtract, StringToExtract — entity definitions, including example structures and instructions
- ObjectsToExtract — collection of entities + shared config for a job
- Document — loader for file bytes, derived text, and images, with type detection (PDF/IMAGE/TEXT) and optional in-memory PDF page trimming
- ExtractionResult(s) — structured outputs with metadata (success, message, tokens, cost)

## Prompting and Messages
- Prompt Builders: System + entity-specific templates from prompts/
- Message Composition (extractor.py):
  - Injects:
    - TEXT: document text appended into prompt
    - IMAGE: base64-encoded JPEG(s) via `pil_img_to_base64`
    - FILE: base64-encoded PDF bytes as a file attachment
  - Produces a single `HumanMessage` payload combining attachments + text instructions
- JSON Enforcement:
  - Uses LangChain's ChatOpenAI with `response_format={"type": "json_object"}`
  - Strips markdown code fences prior to JSON parsing

## Execution Model and Resilience
- Single-Entity Extraction:
  - Retry with exponential backoff up to `max_retries`
  - Robust parsing of token usage from `usage_metadata` and `response_metadata`
- Multi-Entity Extraction:
  - ThreadPoolExecutor with `parallel_requests` to run per-entity in parallel
  - Fan-in aggregation into `ExtractionResults` with totals (tokens, cost)
- Observability:
  - Centralized logging via `logging_config.py`
  - Optional generation cost lookup (OpenRouter/OpenAI) for post-run accounting

## Configuration Strategy (✅ v0.5.0 - Migration Complete)

### Environment Variables Only
- ✅ **YAML config fully deprecated** - No more config.yml/config.yaml files
- Configuration via `.env` file at project root
- python-dotenv automatically loads environment variables on startup
- `.env.sample` provided as template

### Key Configuration Variables
```bash
# Required
OPENAI_API_KEY=your-api-key
OPENAI_API_BASE=https://openrouter.ai/api/v1  # or https://api.openai.com/v1
OPENAI_DEFAULT_MODEL=google/gemini-2.5-flash

# Optional (with sensible defaults)
OPENAI_TEMPERATURE=0.0
OPENAI_MAX_TOKENS=4096
```

### Configuration Resolution (config.py)
- Reads directly from environment variables
- No fallback to YAML
- Clear error messages if required variables missing
- Uses os.getenv() with python-dotenv pre-loading

### Benefits of ENV-First Approach
- Standard practice across development/production
- Better security (no committed credentials)
- Easier Docker/container deployment
- Simpler CI/CD integration
- Native support in cloud platforms
- No config file parsing overhead

## Provider-Agnostic Design
- Primary interface via LangChain's chat models (ChatOpenAI)
- Works with any OpenAI-compatible endpoint:
  - OpenRouter (multi-provider gateway)
  - OpenAI
  - Ollama (local)
  - LM Studio
  - Any compatible API
- Current recommendation: Gemini 2.5 Flash via OpenRouter
- Attachments (FILE/IMAGE) follow OpenAI message format; abstraction keeps application code uniform

## Logging and Diagnostics
- `setup_logging` initializes handlers and levels
- `get_logger` used across modules for consistent structured logs
- Metadata captured in results (tokens, cost, raw response payload subset for auditability)
- Logs include extraction job details, retry attempts, errors, and performance metrics

## Extension Points

### 1. New Entity Types
- Beyond tables/strings: key-value records, hierarchical schemas
- Custom entity classes extending base extraction models
- Type-specific prompt templates and validation

### 2. Input Mode Variations
- Hybrid strategies (annotate → extract workflow)
- Document chunking for large files
- Multi-page processing strategies
- PDF page subsetting at document load time via in-memory trimming before FILE/TEXT/IMAGE conversion

### 3. Provider Adapters
- Direct SDK integrations (OpenAI, Gemini, Claude native clients)
- Local inference (Ollama native support)
- Provider-specific optimizations
- Unified attachment handling across providers

### 4. API and UI Layers
- FastAPI REST endpoints (v0.6.0)
- Web UI for visual management (v0.7.0)
- Job queue and async processing
- Schema management CRUD operations

### 5. Advanced Features
- Auto-detect mode for entity identification
- Deepseek OCR integration
- MCP server for agentic applications
- Annotation caching to reduce token usage
- Cost optimization strategies

## Risks and Considerations

### Provider Differences
- FILE/IMAGE attachment handling may vary across backends
- Some providers may not support certain input modes
- Need adapters to normalize provider-specific behavior
- Testing required across multiple LLM providers

### Configuration
- ✅ ENV-only approach reduces complexity
- Missing environment variables will raise clear errors
- Need proper .env setup documentation
- Security: .env files should never be committed

### JSON Strictness
- Enforcing pure JSON output is essential
- Defense via response_format and code-fence stripping
- Some models may not respect json_object format perfectly
- Robust parsing and validation required

### Cost Efficiency
- Token usage can be high for large documents
- Multiple input modes multiply token costs
- Planned: One-time annotation step to reduce redundancy
- Cost tracking helps identify optimization opportunities

### Performance
- Parallel extraction improves throughput
- Rate limits vary by provider
- Need backoff/retry for reliability
- Large documents may require chunking strategies

## Testing and Example Usage
- Example scripts/tests demonstrate:
  - Defining entities (tables, strings) with example data
  - Choosing input modes (FILE/TEXT/IMAGE)
  - Running extraction with different providers
  - Exporting results (CSV/XLSX)
  - Token and cost tracking
- Tests use .env configuration
- Integration tests needed for provider compatibility

## Architecture Evolution

### Current (v0.5.0)
- Solid core SDK
- ENV-based configuration
- Multi-entity parallel extraction
- Token/cost tracking

### Near-term (v0.6.0)
- REST API layer (FastAPI)
- Job submission and management
- Entity schema CRUD
- Async processing

### Medium-term (v0.7.0)
- Web UI for visual management
- Auto-detect mode
- Enhanced OCR integration
- MCP server adapter

### Long-term (v0.8.0+)
- Native provider integrations
- Local inference optimization
- Annotation caching system
- Advanced analytics and benchmarking

## Code Organization Principles
- Clean separation of concerns
- Type-safe with Pydantic v2
- Functional core with side effects at edges
- Template-based prompting
- Comprehensive error handling
- Structured logging throughout
- Testable components
