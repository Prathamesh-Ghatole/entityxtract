# Product Context: entityxtract

## Why this exists
Organizations routinely need to extract structured information from unstructured documents (PDF, DOCX, TXT, images, etc.). Manual extraction is slow and error-prone. entityxtract enables users to declaratively define custom entities with a schema, few-shot examples, and custom instructions, then reliably extract them using any LLM.

Built as an **open-source alternative** to commercial solutions like Google Cloud Document AI, Azure AI Document Intelligence, and Adobe PDF Extract — but provider-agnostic and designed to work with any LLM.

## Target Users
- Data/analytics engineers embedding extraction into pipelines
- Platform/integration teams exposing extraction as internal services
- Analysts automating repeatable extractions with consistent schemas
- Developers building custom workflows requiring provider-agnostic LLM extraction
- Teams seeking alternatives to expensive proprietary document AI services

## How it should work (User Experience)

### Python SDK (Current - v0.5.0)
```python
# 1. Load document
doc = Document(Path("document.pdf"))

# 2. Define entities with schema + examples + instructions
table = TableToExtract(
    name="Events",
    example_table=pl.DataFrame([...]),
    instructions="Extract the events table...",
    required=True
)

# 3. Configure extraction
config = ExtractionConfig(
    model_name="google/gemini-2.5-flash",
    file_input_modes=[FileInputMode.FILE]
)

# 4. Extract and get structured results
results = extract_objects(doc, ObjectsToExtract(objects=[table], config=config))
```

Features:
- Create Document from file path (auto-detects format)
- Define entities to extract (schema, few-shot examples, custom instructions)
- Choose input modes: FILE, TEXT, IMAGE, or combinations
- Invoke extraction and receive structured JSON results (tables, records, strings)
- Export to CSV/XLSX with token/cost tracking

### REST API (Planned - v0.6.0)
- POST /extract - Submit extraction jobs with documents and entity definitions
- GET /schemas - List and manage entity schemas
- POST /schemas - Create reusable entity schemas
- GET /jobs/{id} - Monitor status and retrieve results
- OpenAPI/Swagger documentation for easy integration

### Web UI (Planned - v0.7.0)
- Visual entity schema editor with example data
- Drag-and-drop document upload
- Real-time extraction job monitoring
- Results preview with table display
- Export to CSV/XLSX
- Cost tracking dashboard

## Product Principles
- **Entity-first, schema-driven extraction**: Define what you need with examples
- **Provider-agnostic**: Works with any LLM via OpenAI-compatible APIs
- **Reproducible and evaluable**: Clean JSON output without code fences
- **Efficient operation**: Concurrent extraction with cost awareness
- **Composable building blocks**: SDK → API → UI progressive enhancement
- **Open source**: MIT licensed, community-driven development

## Similar Tools and Differentiation

### Comparisons

| Feature               | entityxtract       | Llama Extract   | Google Document AI | Azure AI Document Intelligence |
| --------------------- | ------------------ | --------------- | ------------------ | ------------------------------ |
| **Open Source**       | ✅ MIT License      | ❌ Closed        | ❌ Closed           | ❌ Closed                       |
| **Provider Choice**   | ✅ Any LLM          | ❌ Llama only    | ❌ Google only      | ❌ Azure only                   |
| **Schema-Driven**     | ✅ Full support     | ✅ Yes           | ⚠️ Limited          | ⚠️ Limited                      |
| **Few-Shot Examples** | ✅ Built-in         | ✅ Yes           | ❌ No               | ❌ No                           |
| **Local Execution**   | ✅ Planned (Ollama) | ❌ API only      | ❌ Cloud only       | ❌ Cloud only                   |
| **Cost**              | 💰 Pay-per-token    | 💰 Pay-per-token | 💰💰 Enterprise      | 💰💰 Enterprise                  |
| **Self-Hosted**       | ✅ Yes              | ❌ No            | ❌ No               | ❌ No                           |

### Key Differentiators
- **Provider Agnostic**: Not locked to a single LLM provider
- **Open Source**: Full transparency, customizable, community-driven
- **Schema + Examples**: Strong emphasis on structured entity definitions with few-shot learning
- **Complete Stack**: Python SDK today, REST API and Web UI coming soon
- **Local Option**: Planned Ollama integration for offline/private extraction

## Recommendations
- **Model**: Gemini 2.5 Flash currently recommended for best results
- **Setup**: Use `.env` file for configuration (`.env.sample` provided)
- **Environment**: uv for Python environment management
- **Providers**: OpenRouter recommended for multi-model access

## Setup (Current - v0.5.0)

### Quick Start
```bash
# 1. Install dependencies
uv sync

# 2. Configure environment
cp .env.sample .env
# Edit .env with your API credentials

# 3. Run example
uv run tests/test.py
```

### Environment Configuration
Create `.env` file with:
```bash
OPENAI_API_KEY=your-api-key
OPENAI_API_BASE=https://openrouter.ai/api/v1
OPENAI_DEFAULT_MODEL=google/gemini-2.5-flash
```

Works with:
- OpenRouter (multi-provider gateway)
- OpenAI
- Any OpenAI-compatible endpoint (Ollama, LM Studio, etc.)

## Roadmap

### Coming Soon (v0.6.0)
- 🌐 **REST API**: FastAPI-based extraction service
- 📊 **Job Management**: Async extraction with status tracking
- 📝 **Schema Management**: CRUD API for entity schemas

### Near Future (v0.7.0)
- 🖥️ **Web UI**: Visual entity/schema management and job monitoring
- 🔍 **Auto-detect mode**: Automatically identify extractable entities
- 👁️ **Deepseek OCR**: Enhanced document processing
- 🔌 **MCP server**: Enable agentic application integration

### Future Enhancements
- 📦 **PyPI publishing**: `pip install entityxtract`
- 🏠 **Local inference**: Native Ollama integration
- 🔧 **Provider adapters**: Direct OpenAI, Gemini, Claude SDK support
- 💾 **Annotation caching**: Reduce repeated token usage
- 📈 **Advanced analytics**: Cost optimization and accuracy benchmarking

## Success Metrics
- Documents successfully processed with structured output
- JSON responses parseable by downstream tools (CSV/XLSX export)
- Token and cost tracking accuracy
- Provider compatibility across multiple LLMs
- Community adoption and contributions

## Future Additions (Technical)
- Additional entity types beyond tables/strings
- Hierarchical schema support
- Document chunking strategies for large files
- Multi-document extraction jobs
- Result validation and confidence scoring
- A/B testing framework for prompt/model comparison

As the project evolves, the REST API and Web UI will formalize and improve end-user experience for job orchestration, visual schema editing, and comprehensive result management.
