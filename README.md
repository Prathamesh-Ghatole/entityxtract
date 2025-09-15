# entityxtract

Entity-first, schema-driven extraction of structured data from unstructured documents (PDF, DOCX, TXT, images). Define custom entities with a schema, few-shot examples, and custom instructions, then extract reliably using any LLM.

- Open source and provider-agnostic
- Works today via a Python SDK
- REST API and Web UI planned
- Recommended model currently: Gemini 2.5 Flash

Similar in purpose to Llama Extract, but open source and designed to work with any LLM/provider.

## Table of Contents
- Features
- How it works
- Quick start
- Installation
- Configuration
- Usage examples
- Architecture at a glance
- Providers and models
- Roadmap
- Comparisons
- Contributing
- License

## Features
- Entity-first extraction
  - Define entities (tables, strings, records) via schema, few-shot examples, and custom instructions
- Flexible input modes
  - Pass the document to the LLM as FILE, TEXT, IMAGE, or any combination
- Provider-agnostic design
  - Swap LLM backends without changing application code
- Robust execution
  - Retries with backoff, parallel extraction, strict JSON output
- Observability
  - Structured logs, token usage capture, optional cost lookup
- Clean outputs
  - JSON-compatible structures suitable for DataFrames and CSV/XLSX export

## How it works (Sample flow)
1. Provide a document (txt, pdf, docx, image).
2. Define entities to extract (schema, few-shot examples, custom instructions).
3. The framework assembles a prompt and composes a multimodal message to the LLM.
   - Choose how data is passed to the LLM: as a file, as text, as images, or combinations.
4. entityxtract returns structured data for your entities.

Note: Gemini 2.5 Flash is currently recommended for best results.

## Quick start
Using uv is recommended.

- Clone and set up:
  - `uv sync`
- Run an example:
  - `uv run tests/test_extraction_1.py`

For a minimal YAML setup (transitional while we migrate to ENV-first):
- `cp config.yml.sample config.yml`
- Fill in provider keys and defaults.

## Installation
- Python 3.12
- Install dependencies with uv:
  - `uv sync`

If not using uv, you can install via pip using pyproject constraints, but uv is the recommended flow for this repo.

## Configuration
Configuration precedence:
- Environment variables (preferred, target state)
- YAML (transitional): `config.yml`/`config.yaml` at repo root

Example env vars (OpenRouter/OpenAI compatible):
- `OPENAI_API_KEY`
- `OPENAI_API_BASE`
- `OPENROUTER.API_KEY`
- `OPENROUTER.API_BASE`
- `DEFAULT_MODEL`

Transitional YAML (see `config.yml.sample`):
```yaml
OPENROUTER:
  API_KEY: "YOUR_API_KEY_HERE"
  API_BASE: "https://openrouter.ai/api/v1"
  DEFAULT_MODEL: "google/gemini-2.0-flash-001"
```
Tip: Prefer ENV-first for production; keep YAML only as a bridge during migration.

## Usage examples

Basic extraction with a PDF as file input, using a table entity schema and parallel extraction.

```python
from pathlib import Path
import polars as pl

from entityxtract.extractor_types import (
    Document, ExtractionConfig, FileInputMode,
    TableToExtract, StringToExtract, ObjectsToExtract
)
from entityxtract.extractor import extract_objects

# 1) Load a document
doc = Document(Path("path/to/document.pdf"))

# 2) Define entities
table = TableToExtract(
    name="Summary of Events",
    example_table=pl.DataFrame([
        {"Begin": "02:05", "End": "03:25", "Duration": "01:20", "Type": "Geotechnical operation", "Description": "Example row..."},
        # Add a few representative example rows to anchor structure and types
    ]),
    instructions="Extract the summary table with columns Begin, End, Duration, Type, Description.",
    required=True,
)

string_entity = StringToExtract(
    name="Report ID",
    example_string="RPT-000123",
    instructions="Extract the report identifier from the document header/footer.",
    required=False,
)

# 3) Configure extraction
config = ExtractionConfig(
    model_name="google/gemini-2.5-flash",  # recommended
    temperature=0.0,
    file_input_modes=[FileInputMode.FILE],  # or TEXT / IMAGE / combinations
    parallel_requests=4,
    calculate_costs=True,  # optional, requires provider support
)

objects = ObjectsToExtract(objects=[table, string_entity], config=config)

# 4) Run extraction
results = extract_objects(doc, objects)

# 5) Consume results
for name, res in results.results.items():
    if res.success:
        print(f"[{name}] tokens in/out: {res.input_tokens}/{res.output_tokens}, cost={res.cost}")
        # Tables: construct DataFrame
        try:
            df = pl.DataFrame(res.extracted_data)
            print(df)
            df.write_csv(f"{name}.csv")
        except Exception:
            print(res.extracted_data)
    else:
        print(f"[{name}] failed: {res.message}")

print(f"Totals: input={results.total_input_tokens} output={results.total_output_tokens} cost={results.total_cost}")
```

- See `tests/test_extraction_1.py` for a fuller example, including CSV export helpers (`tests/utils_io.py`).
- To include document TEXT or IMAGE content in prompts, add `FileInputMode.TEXT` and/or `FileInputMode.IMAGE` to `file_input_modes`.

## Architecture at a glance
- `src/entityxtract/`
  - `extractor.py` — Prompt/message construction, model invocation, retries/backoff, token/cost parsing, concurrency.
  - `extractor_types.py` — Pydantic models (`Document`, `FileInputMode`, entity definitions, config, results).
  - `pdf/` — PDF utilities (to text/images).
  - `prompts/` — System and entity templates (`system.txt`, `table.txt`, `string.txt`).
  - `config.py` — Config precedence (ENV > YAML top-level > dotted path > deep search).
  - `logging_config.py` — Centralized logging helpers.

Data flow:
1) Load `Document` (PDF/TEXT/IMAGE). PDFs can lazily derive text and page images.
2) Build prompts from templates + entity definitions (schema + examples + instructions).
3) Compose a multimodal message (text, base64 images, and/or file) according to input modes.
4) Invoke LLM with strict JSON response enforcement; parse/clean.
5) Aggregate per-entity results with totals (tokens, cost).

## Providers and models
- Provider-agnostic via LangChain chat models.
- Recommended today: Gemini 2.5 Flash.
- Attachments (FILE/IMAGE) semantics differ by provider; adapters normalize this where possible.
- Planned additions:
  - Local inference via Ollama
  - Direct provider SDKs for OpenAI, Gemini, Claude, etc.

Environment keys (illustrative):
- `OPENAI_API_KEY`, `OPENAI_API_BASE`
- `OPENROUTER.API_KEY`, `OPENROUTER.API_BASE`
- `DEFAULT_MODEL`

## Roadmap
- Interfaces:
  - FastAPI REST API
  - Web UI for entity/schema management, job runs, and results review/export
  - UI Automatic Mode: detect tabular structures in documents and auto-generate sample entity definitions (JSON) to speed setup
- Developer Experience:
  - ENV-first configuration (deprecate YAML path over time)
  - One-time document annotation to reduce repeated token usage/costs
  - CLI entrypoint (`entityxtract:main`) to match pyproject script
  - JSON import/export support for entity schemas and extraction results
- Providers:
  - Adapters for OpenAI, Gemini, Claude, and Ollama
- Quality:
  - Update and expand tests post-rename and for new features

## Comparisons
- Similar to Llama Extract in intent.
- Differentiators:
  - Open source
  - Provider-agnostic (works with any LLM)
  - Strong emphasis on schema + examples + instructions
  - Roadmap includes polished SDK + REST API + UI

Additional docs to be added:
- Comparative analysis with Llama Extract, DocETL, AWS Bedrock, etc.

## Contributing
- Use uv for environment management.
- Follow strict JSON output and logging conventions.
- Open an issue or PR with a clear description and tests where possible.

## License
TBD. Consider MIT or Apache-2.0. If you choose a license, add a LICENSE file and update this section.

---

Notes
- Current pyproject declares `llm-extractor = "entityxtract:main"`; implement `main()` or update the script mapping.
- Transitional YAML file present as `config.yml.sample`; prefer ENV-first going forward.
- Tests demonstrate CSV export patterns and multi-entity extraction.
