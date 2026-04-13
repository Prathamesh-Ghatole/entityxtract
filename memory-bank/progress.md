# Progress: entityxtract

## What Works (v0.5.0)
- ✅ Entity-first extraction via schema + few-shot examples + custom instructions (tables/records/strings)
- ✅ Document abstraction supports multi-modal input: FILE, TEXT, IMAGE; PDFs converted to text/images
- ✅ PDF page-range filtering via `Document(..., page_range=(start, end))` with in-memory PDF trimming
- ✅ Prompt assembly with system + entity-specific templates; enforced pure JSON responses
- ✅ Robust execution:
  - Retries with exponential backoff
  - Concurrent multi-entity extraction via ThreadPoolExecutor (parallel_requests)
  - Token usage capture (input/output) and optional cost lookup (OpenRouter/OpenAI)
- ✅ Structured results:
  - Per-entity ExtractionResult with metadata
  - Aggregated ExtractionResults with totals
  - Downstream export to CSV/XLSX working
- ✅ Provider-agnostic design; works with any OpenAI-compatible endpoint
- ✅ Gemini 2.5 Flash recommended and tested
- ✅ **Configuration fully migrated to .env** - YAML deprecated and removed
- ✅ python-dotenv integration for automatic environment loading
- ✅ README comprehensively updated with examples, comparisons, and roadmap
- ✅ Memory Bank fully documented and aligned

## What's Left (Backlog)

### Critical Items
- **CLI entrypoint**: Implement `main()` function in `__init__.py` (declared in pyproject.toml but missing)
- **Tests verification**: Update/verify tests work with .env configuration and entityxtract naming

### Near-term Features (v0.6.0)
- **REST API Implementation**:
  - Design FastAPI endpoint structure
  - POST /extract - Submit extraction jobs
  - GET /schemas - List entity schemas
  - POST /schemas - Create entity schema
  - GET /jobs/{id} - Job status and results
  - OpenAPI/Swagger documentation

### Medium-term Features (v0.7.0)
- **Web UI**: Entity schema editor, job runner/monitor, results preview/export
- **Auto-detect mode**: Automatically identify extractable entities in documents
- **Deepseek OCR integration**: Enhanced document processing
- **MCP server**: Enable agentic application integration
- **PyPI publishing**: Enable `pip install entityxtract`

### Long-term Features
- **Provider adapters**: Native SDKs for OpenAI, Gemini, Claude
- **Local inference**: Direct Ollama integration
- **Annotation caching**: One-time document annotation to reduce repeated token usage
- **Cost optimization**: Advanced cost tracking and reduction strategies
- **Benchmarking**: Accuracy and performance test suite
- **Additional entity types**: Beyond tables/strings (hierarchical schemas, key-value records)

### Testing & Quality
- Integration tests for multiple providers
- E2E test coverage expansion
- Performance benchmarks
- Accuracy evaluation framework
- Provider compatibility matrix

### Documentation
- API reference documentation
- More usage examples and tutorials
- Provider-specific setup guides
- Cost optimization best practices
- Migration guides for updates

## Current Status (v0.5.0)
- Repository: entityxtract at version 0.5.0
- Package path: src/entityxtract
- Configuration: ✅ .env-based (migration complete)
- Setup:
  - Environment manager: uv recommended
  - Install: `uv sync`
  - Configure: Copy `.env.sample` to `.env` and fill values
  - Run example: `uv run tests/test.py`
- Core SDK: ✅ Fully functional
- CLI: ⚠️ Declared but not implemented
- REST API: ❌ Not implemented (fastapi dependency present)
- Web UI: ❌ Not implemented

## Known Issues / Risks

### Implementation Gaps
- **CLI entrypoint missing**: pyproject.toml declares `llm-extractor = "entityxtract:main"` but function not implemented
- **Empty __init__.py**: Main package file has no exports or CLI entrypoint

### Testing
- Tests may need updates for .env configuration
- Need provider-specific test coverage
- Integration test suite incomplete

### Provider Compatibility
- FILE/IMAGE attachment formats vary by provider
- Need adapters to normalize provider-specific behavior
- Testing needed across multiple LLM backends

### Documentation
- Need more real-world usage examples
- Cost estimation/optimization guide needed
- Provider setup documentation could be expanded

## Completed Milestones

### v0.5.0
- ✅ Configuration migration from YAML to .env complete
- ✅ python-dotenv integration
- ✅ Comprehensive README update
- ✅ Memory Bank documentation complete
- ✅ Version bump and metadata update

### v0.4.x
- ✅ Repository renamed to entityxtract
- ✅ Package path updated to src/entityxtract
- ✅ Core extraction engine implementation
- ✅ Multi-entity parallel extraction
- ✅ Token and cost tracking
- ✅ PDF/TEXT/IMAGE document handling
- ✅ Provider-agnostic design with LangChain

## Decisions and Direction

### Configuration
- ✅ ENV-first approach adopted
- ✅ YAML config fully deprecated
- ✅ python-dotenv for automatic loading

### Architecture
- Provider-agnostic core via OpenAI-compatible APIs
- Gemini 2.5 Flash as recommended model
- Concurrent execution with configurable parallelism
- Strict JSON enforcement across all providers
- Comprehensive observability (logs, tokens, costs)

### Roadmap Priority
1. CLI implementation (v0.5.x)
2. REST API (v0.6.0)
3. Web UI + Advanced features (v0.7.0)
4. Provider adapters + Optimization (v0.8.0+)

## Next Steps (Immediate)
1. Implement CLI `main()` function for command-line access
2. Verify all tests work with .env configuration
3. Plan REST API endpoint structure
4. Begin FastAPI implementation
5. Document API design decisions
