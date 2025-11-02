# Active Context: entityxtract

## Current Focus
- Memory Bank re-initialization complete (v0.5.0)
- All documentation aligned with current project state
- Configuration migration to `.env` fully complete
- Focus on implementing missing features and preparing for public release

## Recent Changes
- ✅ **Configuration migration complete**: Fully moved from YAML to `.env` files
  - `.env` and `.env.sample` files in place
  - config.py updated to read from environment variables only
  - YAML config files (config.yml) fully deprecated and removed
- ✅ Repository at version 0.5.0
- ✅ Memory Bank fully refreshed with accurate documentation
- ✅ README comprehensively updated with usage examples and roadmap
- python-dotenv added to dependencies for automatic .env loading

## Decisions
- **Configuration**: ENV-only approach, no YAML support
- **Provider-agnostic design**: Works with any OpenAI-compatible endpoint
- **Model recommendation**: Gemini 2.5 Flash for best results
- **Input modes**: FILE, TEXT, IMAGE - can be combined per job
- **JSON enforcement**: Pure JSON outputs (no code fences) via response_format + post-cleaning
- **Observability**: Structured logging, token usage tracking, optional cost tracking

## Open Implementation Items

### High Priority
1. **CLI entrypoint** - `main()` function missing in `__init__.py`
   - pyproject.toml declares: `llm-extractor = "entityxtract:main"`
   - Function needs to be implemented for CLI access
2. **REST API** - FastAPI scaffolding not yet implemented
   - Dependency present but endpoints not wired
3. **Web UI** - Not implemented
   - Planned for entity schema management, job monitoring, results preview

### Roadmap Features
1. **Auto-detect mode** - Automatically identify extractable entities in documents
2. **Deepseek OCR integration** - Enhanced document processing capabilities
3. **MCP server** - For agentic applications
4. **PyPI publishing** - Enable `pip install entityxtract`
5. **Local inference** - Native Ollama integration
6. **Provider adapters** - Direct SDKs for OpenAI, Gemini, Claude
7. **Annotation caching** - One-time document annotation to reduce token usage

### Testing & Quality
- Review and update tests post-rename to entityxtract
- Add integration tests for different providers
- Benchmark suite for accuracy and performance

## Current Architecture State
- Core extraction engine: ✅ Working
- Document handling (PDF/TEXT/IMAGE): ✅ Working
- Multi-entity parallel extraction: ✅ Working
- Token/cost tracking: ✅ Working
- Configuration management: ✅ Complete (.env-based)
- CLI interface: ⚠️ Declared but not implemented
- REST API: ⚠️ Dependency present, not implemented
- Web UI: ❌ Not started

## Notes on Configuration
- `.env` file pattern now standard
- Sample provided as `.env.sample`
- python-dotenv handles automatic loading
- Common keys:
  - OPENAI_API_KEY
  - OPENAI_API_BASE
  - OPENAI_DEFAULT_MODEL

## Next Steps (Prioritized)

### Immediate (v0.5.x)
1. Implement CLI `main()` function in `__init__.py`
2. Add comprehensive usage examples in documentation
3. Verify all tests work with .env configuration

### Near-term (v0.6.0)
1. Design REST API structure (FastAPI endpoints)
2. Implement basic API endpoints:
   - POST /extract - Submit extraction job
   - GET /schemas - List entity schemas
   - POST /schemas - Create entity schema
   - GET /jobs/{id} - Get job status/results
3. Add API documentation with OpenAPI/Swagger

### Medium-term (v0.7.0)
1. Plan Web UI architecture
2. Implement Auto-detect mode for entity identification
3. Add Deepseek OCR integration
4. Create MCP server adapter
5. Prepare for PyPI publishing

### Long-term
1. Native provider integrations (OpenAI, Gemini, Claude SDKs)
2. Local inference via Ollama
3. Annotation caching system
4. Advanced cost optimization features
5. Benchmark suite and accuracy testing

## Guidelines and Preferences
- Use uv for environment and dependency management
- Keep prompts template-based under prompts/ directory
- Preserve concurrency (parallel_requests) and retry/backoff semantics
- Maintain strict JSON responses with comprehensive metadata
- All configuration via environment variables
- Structured logging throughout
