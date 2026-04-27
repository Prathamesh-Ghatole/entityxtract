# entityxtract

[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Pydantic v2](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v2.json)](https://pydantic.dev)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License MIT](https://img.shields.io/github/license/Prathamesh-Ghatole/entityxtract)](https://opensource.org/licenses/MIT)

**entityxtract simplifies robust, agentic, schema-driven extraction of structured data from unstructured documents**. Define custom entities with schemas, few-shot examples, and instructions, then extract reliably using any local or SOTA LLM.

Built as an **open-source alternative** to Google Cloud Document AI, Azure AI Document Intelligence, and AWS Textract — but even more accurate, provider-agnostic and BYOK by design.

<p align="center">
  <a href="https://github.com/Prathamesh-Ghatole/entityxtract">
    <img alt="entityxtract" src="https://raw.githubusercontent.com/Prathamesh-Ghatole/entityxtract/main/docs/assets/entityxtract_flow.png" width="100%"/>
  </a>
</p>


## Features

* 🎯 **Entity-first extraction** — Smart structured data extraction with pre-defined / auto-identified entities.
* 📄 **Multiple document formats** — Support for PDF, TXT, MD, and images.
* 🔀 **Smart input modes** — Extract information using text, OCR, or hybrid approaches.
* 🌐 **Provider-agnostic design** — Works with any LLM via OpenAI-compatible APIs.
* 🔄 **Robust execution** — Built-in retries, parallel extraction, strictly structured and typed output.
* 📊 **Observability** — Structured logs, token usage tracking, and optional cost tracking.
* 📦 **PyPI Package** — Easily install and use entityxtract in your projects.

### Coming Soon

* 🌐 **FastAPI REST API** for remote extraction services.
* 🖥️ **Web UI** for visual entity/schema management and job monitoring.
* 🔍 **Auto-detect mode** to automatically identify extractable entities in documents.
* 💰 **Cost Optimization** using PDF annotation caching, and smart input data pruning.
* 👁️ **Deepseek OCR** integration for enhanced document processing.
* 🔌 **MCP server** for agentic applications.

## Installation

To use entityxtract, you'll need Python 3.12+ and [uv](https://docs.astral.sh/uv/) (recommended):

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/Prathamesh-Ghatole/entityxtract.git
cd entityxtract

# Install dependencies
uv sync
```

## Getting Started

Extract pre-defined entities:

```python
from pathlib import Path
import polars as pl
from entityxtract.extractor_types import (
    Document, TableToExtract,
    ExtractionConfig, FileInputMode
)
from entityxtract.extractor import extract_objects

# 1. Load your document
doc = Document(Path("document.pdf"))

# 2. Define what to extract
table = TableToExtract(
    name="Events",
    example_table=pl.DataFrame([
        {"Time": "02:05", "Type": "Operation", "Description": "Example event"},
        {"Time": "03:25", "Type": "Transit", "Description": "Another event"}
    ]),
    instructions="Extract the events table with Time, Type, and Description columns.",
    required=True
)

# 3. Configure extraction
config = ExtractionConfig(
    model_name="google/gemini-2.5-flash",  # Recommended
    temperature=0.0,
    file_input_modes=[FileInputMode.FILE]
)

# 4. Extract!
results = extract_objects(doc, [table], config)

# Use your results
for name, result in results.results.items():
    if result.success:
        df = pl.DataFrame(result.extracted_data)
        print(df)
    else:
        print(f"Failed: {result.message}")
```

## Configuration

Copy the sample environment file `.env.sample` to `.env`, or set the following environment variables directly:

```bash
# For all OpenAI-compatible endpoints [OpenAI, OpenRouter, Ollama, lm-studio, etc.]
export OPENAI_API_KEY="your-api-key"
export OPENAI_API_BASE="https://openrouter.ai/api/v1"

# Default model
export OPENAI_DEFAULT_MODEL="google/gemini-2.5-flash"
```

## Usage Examples

### Complete Example with Multiple Entities

```python
from pathlib import Path
import polars as pl

from entityxtract.extractor_types import (
    Document, ExtractionConfig, FileInputMode,
    TableToExtract, StringToExtract
)
from entityxtract.extractor import extract_objects

# Load document
doc = Document(Path("reports/quarterly_summary.pdf"))

# Define entities to extract
table = TableToExtract(
    name="Financial Summary",
    example_table=pl.DataFrame([
        {"Quarter": "Q1 2024", "Revenue": "$1.2M", "Expenses": "$800K", "Profit": "$400K"},
        {"Quarter": "Q2 2024", "Revenue": "$1.5M", "Expenses": "$900K", "Profit": "$600K"}
    ]),
    instructions="Extract the quarterly financial summary table with Quarter, Revenue, Expenses, and Profit columns.",
    required=True
)

report_id = StringToExtract(
    name="Report ID",
    example_string="RPT-2024-Q2-001",
    instructions="Extract the report identifier from the document header.",
    required=False
)

# Configure extraction with cost tracking
config = ExtractionConfig(
    model_name="google/gemini-2.5-flash",
    temperature=0.0,
    file_input_modes=[FileInputMode.FILE],
    parallel_requests=4,
    calculate_costs=True
)

# Run extraction
results = extract_objects(doc, [table, report_id], config)

# Process results
for name, res in results.results.items():
    if res.success:
        print(f"✓ [{name}] extracted successfully")
        print(f"  Tokens: {res.input_tokens} in / {res.output_tokens} out")
        print(f"  Cost: ${res.cost:.4f}")
        
        # Export table to CSV
        if isinstance(res.extracted_data, list):
            df = pl.DataFrame(res.extracted_data)
            df.write_csv(f"{name}.csv")
            print(f"  Saved to {name}.csv")
    else:
        print(f"✗ [{name}] failed: {res.message}")

print(f"\nTotals: {results.total_input_tokens} tokens in, {results.total_output_tokens} tokens out")
print(f"Total cost: ${results.total_cost:.4f}")
```

### Different Input Modes

```python
# Pass document as file attachment
config = ExtractionConfig(
    model_name="google/gemini-2.5-flash",
    file_input_modes=[FileInputMode.FILE]
)

# Pass document as text content
config = ExtractionConfig(
    model_name="google/gemini-2.5-flash",
    file_input_modes=[FileInputMode.TEXT]
)

# Pass document as images (useful for scanned documents)
config = ExtractionConfig(
    model_name="google/gemini-2.5-flash",
    file_input_modes=[FileInputMode.IMAGE]
)

# Combine multiple input modes
config = ExtractionConfig(
    model_name="google/gemini-2.5-flash",
    file_input_modes=[FileInputMode.FILE, FileInputMode.TEXT]
)
```

See `tests/test.py` for more complete examples.

## Roadmap

### Interfaces
- 🌐 FastAPI REST API for remote extraction services
- 🖥️ Web UI for entity management, job runs, and results review
- 🤖 Auto-detect mode: automatically identify entities in documents

### Developer Experience
- 📦 Publish to PyPI for easy `pip install entityxtract`
- ⚡ ENV-first configuration (deprecate YAML)
- 💾 Document annotation caching to reduce token usage
- 🔧 JSON import/export for entity schemas and results
- 📝 Enhanced CLI with `entityxtract` command

### Providers & Models
- 🏠 Local inference via Ollama
- 🔌 Native adapters for OpenAI, Gemini, Claude, and more
- 🌍 Support for additional LLM providers

### Quality & Testing
- ✅ Expanded test coverage
- 📊 Benchmark suite for accuracy and performance
- 📚 Comprehensive documentation site

## Comparisons

entityxtract positions itself as a flexible, open-source alternative to both commercial services and closed-source solutions:

**Key Differentiators:**
- **Provider Agnostic**: Works with any LLM, not locked to a single provider
- **Open Source**: Full transparency, customizable, and community-driven
- **Schema + Examples**: Strong emphasis on structured entity definitions with few-shot learning
- **Complete Stack**: Python SDK today, REST API and Web UI coming soon

## Contributing

We welcome contributions! entityxtract uses modern Python tooling:

```bash
# Use uv for environment management
uv sync

# Run tests
uv run pytest tests/

# Code formatting with Ruff
uv run ruff check .
uv run ruff format .
```

**Guidelines:**
- Follow strict JSON output conventions
- Include tests for new features
- Update documentation as needed
- Use structured logging patterns

Open an issue or PR with a clear description and we'll be happy to review!

## Get Help and Support

- 💬 [GitHub Discussions](https://github.com/Prathamesh-Ghatole/entityxtract/discussions) - Ask questions and share ideas
- 🐛 [Issues](https://github.com/Prathamesh-Ghatole/entityxtract/issues) - Report bugs or request features
- 📧 Contact: prathamesh.s.ghatole@gmail.com

## License

entityxtract is released under the [MIT License](LICENSE). Free for commercial and personal use.

---

**Built with ❤️ by [Prathamesh Ghatole](https://github.com/Prathamesh-Ghatole)**

*entityxtract was built out of the need for intelligent entity extraction from documents using AI with minimal effort. Define what you need, and let AI handle the rest.*
