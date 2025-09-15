# Project Brief: entityxtract

## Purpose
Extract structured information from unstructured documents (PDF, DOCX, TXT, etc.) by defining custom entities with a schema, few-shot examples, and custom instructions. The framework is open source, provider-agnostic, and can work with any LLM.

## Product Positioning
- Similar to Llama Extract in goals, but open source and designed to work with any LLM/provider.
- Provides a Python SDK today, with a REST API and Web UI planned/in progress.

## Sample Flow (User Journey)
1. User provides a document (txt, pdf, docx, etc.).
2. User defines a list of entities to extract, each with:
   - Schema (fields and types)
   - Few-shot examples
   - Custom instructions
3. The document is processed and sent to the LLM using a prompt template.
   - The user can choose how input is passed to the LLM: as binary file, as text, as image, or combinations of these.
4. entityxtract returns structured data for the requested entities.

Recommendation: Gemini 2.5 Flash is currently recommended for best results.

## Core Requirements
- Entity-first extraction:
  - Users pre-define entities (tables/records/strings) with schema, few-shot examples, and instructions.
- Flexible input modes:
  - Support passing the document as file binary, plain text, images, or combinations thereof.
- Provider-agnostic:
  - Must support multiple LLM backends. Works via a common abstraction and/or provider-specific adapters.
- Interfaces:
  - Python SDK initially; REST API and Web UI are part of the roadmap.
- Reliability & Quality:
  - Enforce JSON output, implement retries with backoff, capture token usage, optionally estimate/track generation costs.
- Concurrency:
  - Parallelize extraction for multiple entities in the same job where safe.
- Configuration:
  - Prefer environment variables; maintain transitional YAML support until migration completes.
- Outputs:
  - JSON-compatible structured outputs suitable for dataframes and export (CSV/XLSX).
- Observability:
  - Structured logging, durable diagnostics, and metrics for token/cost usage.

## Non-Goals (for now)
- Training/finetuning models.
- Long-term storage or complex ETL orchestration beyond providing clean extraction outputs.
- Full OCR pipeline beyond current helpers.

## Success Criteria
- Example runs extract defined entities into structured JSON/CSV from sample documents.
- Deterministic JSON payloads (no fenced code) that downstream tools can reliably parse.
- Token and (optionally) cost reporting available when enabled.
- Works with multiple providers; can switch models without major code changes.

## Roadmap Highlights (from product direction)
- Providers:
  - Future additions: native Ollama; direct integrations for OpenAI, Gemini, Claude, etc.
- Platform:
  - Implement REST API using FastAPI.
  - Implement a Web UI for managing entities, running jobs, and reviewing results.
- Developer Experience:
  - Migrate configuration from YAML to environment variables.
  - Add annotation workflows to reduce repeated token usage and overall cost for multi-pass extraction.
