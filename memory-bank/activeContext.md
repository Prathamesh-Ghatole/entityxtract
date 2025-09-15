# Active Context: entityxtract

## Current Focus
- Initialize and persist the Memory Bank reflecting the entityxtract architecture and product direction.
- Ensure documentation aligns with product notes: entity-first extraction with schema, few-shots, and custom instructions; provider-agnostic; Python SDK now, REST API + UI planned.

## Recent Changes
- Repository renamed to entityxtract (pyproject updated; package path is src/entityxtract).
- Memory Bank initialized; three core files completed so far:
  - projectbrief.md
  - productContext.md
  - systemPatterns.md
  - techContext.md
- Remaining Memory Bank files: activeContext.md (this file) and progress.md.

## Decisions
- Provider-agnostic design; current model recommendation is Gemini 2.5 Flash.
- Input modes: FILE, TEXT, IMAGE; can be combined per job.
- Enforce pure JSON outputs (no code fences) via model response_format + post-cleaning.
- Config precedence: ENV > YAML (transitional); long-term goal is ENV-first and minimizing YAML reliance.
- Observability: structured logging, token usage tracking, optional cost lookup (OpenRouter/OpenAI).

## Open Implementation Items (High-Level)
- CLI entrypoint function `entityxtract:main` missing (declared in pyproject).
- REST API (FastAPI) scaffolding not yet implemented.
- UI not implemented.
- Tests may need verification/updates post-rename and to align with entity-first semantics.
- Standardize configuration: migrate from YAML to environment variables; keep a clean .env/.envrc approach.

## Notes on Configuration Files
- Repo currently contains config.yml.sample.
- Product setup notes mention copying config.example.yaml to config.yaml — reconcile naming and move toward ENV-first configuration.

## Next Steps (Execution-Oriented)
1. Complete Memory Bank by adding progress.md.
2. Create migration plan for configuration (ENV-first; deprecate YAML in stages).
3. Implement missing CLI entrypoint `main()` matching script declaration.
4. Design and scaffold FastAPI endpoints for extraction jobs and entity schema management.
5. Plan UI requirements (entity schema editor, job submission/monitoring, results preview/export).
6. Add provider adapters (OpenAI, Gemini, Claude) and local inference (Ollama).
7. Research and implement a one-time annotation pass to reduce repeated token usage.
8. Review and update tests to reflect entityxtract naming and APIs.

## Guidelines and Preferences
- Use uv for environment setup.
- Keep prompts template-based under prompts/ (system, entity-specific).
- Preserve concurrency (parallel_requests) and robust retry/backoff semantics.
- Maintain strict JSON responses and comprehensive result metadata (tokens, costs when enabled).
