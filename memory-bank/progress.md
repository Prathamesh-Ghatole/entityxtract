# Progress: entityxtract

## What Works
- Entity-first extraction via schema + few-shot examples + custom instructions (tables/records/strings).
- Document abstraction supports multi-modal input: FILE, TEXT, IMAGE; PDFs can be converted to text/images.
- Prompt assembly with system + entity-specific templates; enforced pure JSON responses.
- Robust execution:
  - Retries with exponential backoff.
  - Concurrent multi-entity extraction via ThreadPoolExecutor (parallel_requests).
  - Token usage capture (input/output) and optional cost lookup (e.g., OpenRouter/OpenAI).
- Structured results:
  - Per-entity ExtractionResult with metadata.
  - Aggregated ExtractionResults with totals.
  - Downstream export to CSV/XLSX demonstrated in tests.
- Provider-agnostic design; Gemini 2.5 Flash currently recommended.

## What’s Left (Backlog)
- Tests and Examples
  - Update/verify tests post-rename to entityxtract and align with entity-first semantics.
- Cost Efficiency
  - Implement a one-time annotation pass to reduce repeated token usage/costs.
- Configuration
  - Migrate from YAML config to environment variables (ENV-first); keep a minimal transitional path.
- Interfaces
  - Implement CLI entrypoint `main()` to satisfy script declaration.
  - Implement REST API with FastAPI (job submission, entity schema management, status/results).
  - Implement Web UI (schema editor, job runner/monitor, results preview/export).
- Providers
  - Add direct integrations: OpenAI, Gemini, Claude (SDKs/clients).
  - Add local inference via Ollama.
  - Normalize provider-specific attachment semantics (FILE/IMAGE) via adapters.
- Documentation/Comms (external)
  - Comparisons with Llama Extract, DocETL, AWS Bedrock, etc.
  - Posts: Hashnode blog, X, LinkedIn.

## Current Status
- Repository renamed to entityxtract; package path updated to src/entityxtract.
- Memory Bank initialized and aligned with product notes:
  - projectbrief.md, productContext.md, systemPatterns.md, techContext.md, activeContext.md, progress.md created.
- Setup (current):
  - uv recommended: `uv sync`
  - Example run: `uv run tests/test_extraction_1.py`
  - Transitional configuration file present (config.yml.sample); ENV-first migration planned.

## Known Issues / Risks
- Config/Setup
  - Transitional YAML vs ENV-first: absence of either can raise FileNotFoundError via config loader.
  - Sample filenames mismatch risk (config.yml.sample vs config.example.yaml in notes) — reconcile and standardize.
- Entry Points
  - pyproject declares `llm-extractor = "entityxtract:main"` but `main()` not implemented yet.
- Dependencies
  - fastapi[standard] present but API not yet wired (risk of confusion).
- Provider Differences
  - FILE/IMAGE attachment formats vary by provider; ensure adapters and tests across backends.
- JSON Strictness
  - Maintain strict JSON (no code fences) across providers; keep enforcement and post-cleaning.

## Decisions and Direction (Evolution)
- Provider-agnostic core; Gemini 2.5 Flash recommended today.
- ENV-first configuration is the target; YAML support will be phased down.
- Maintain concurrency and robustness (retries/backoff, token/cost metadata).
- Roadmap includes SDK + REST API + UI for a complete platform.

## Next Steps (Prioritized)
1. Implement CLI `main()` to satisfy pyproject script, or update script mapping if deferring CLI.
2. Standardize configuration path:
   - Decide on env var naming.
   - Provide `.env` support and docs; keep minimal YAML bridge until migration completes.
3. Design and scaffold FastAPI REST endpoints (job submission, entity schema CRUD, retrieval).
4. Plan UI MVP (schema editor, run jobs, monitor, preview/export results).
5. Provider adapters:
   - Add OpenAI, Gemini, Claude, and local Ollama support with unified attachment handling.
6. One-time annotation pipeline to reduce repeated token usage.
7. Update and expand tests for renamed package and new features (API/CLI).
