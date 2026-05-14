# Changelog

All notable changes to **entityxtract** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] — 2026-05-05

### Fixed
- **Thread-safety / PDFium crashes under parallel load.** PDFium (the C
  library behind `pypdfium2`) is not thread-safe; using entityxtract from
  multiple threads in a single process (e.g. a web server handling
  several requests concurrently) could previously segfault the
  interpreter or produce corrupted output. All `pypdfium2` calls inside
  `entityxtract.pdf.extractor` are now serialized via a single
  process-wide `threading.RLock` (`_PDFIUM_LOCK`) held for the full
  lifecycle of each PDFium document.

### Changed
- **`Document` is now eagerly materialised.** `Document.__init__` does
  all PDFium and PIL work up front — text extraction for PDF/TEXT files
  and, for PDFs, page-image rendering — so subsequent reads of
  `.binary`, `.text`, and `.image` from any number of threads are plain
  attribute accesses against immutable / read-only objects. This makes a
  constructed `Document` safe to share across threads.
- `Document` no longer uses class-level attribute defaults; all state is
  initialised per-instance in `__init__`.
- **`.text` / `.image` fast-path now uses explicit `_text_materialized` /
  `_image_materialized` flags** (instead of truthy-checks on the cached
  value). This matters in two previously-broken cases: (a) legitimately
  empty results (scan-only PDF, empty text file, failed PIL decode) are
  now cached rather than retried on every access; (b) doc-type/content-type
  combinations with no work to do (e.g. `.image` on a TEXT doc, `.text`
  on an IMAGE doc) hit the fast path instead of taking the lazy lock on
  every read.
- **`render_images=False` now also applies to `DocType.IMAGE` files**
  (previously PIL decode ran eagerly regardless). The lazy fallback path
  in `.image` is exercised symmetrically for PDF and IMAGE docs.
- **`pdf.close()` in `pdf_to_image` no longer silently swallows
  exceptions**, matching the other helpers in `pdf/extractor.py`. Close
  failures (a real bug signal) will now surface rather than hide.

### Behavioral Changes
- **`Document(...)` may now raise at construction time** for malformed
  PDFs / images that previously would only fail on first `.text` / `.image`
  access. This is intentional — we want construction to fail loudly on the
  calling thread rather than inside a later worker. Wrap `Document(...)`
  in a try/except if your caller relied on the old late-failure behavior.

### Added
- `Document(..., render_images: bool = True)` — pass `render_images=False`
  to skip the (more expensive) page-image render at construction time
  when using only `FileInputMode.FILE` / `FileInputMode.TEXT`. A later
  `.image` access falls back to a lock-guarded lazy render.
- `entityxtract.pdf.extractor.pdfium_lock()` — exposes the process-wide
  PDFium lock for advanced callers that want to cooperate with the same
  serialisation (e.g. if they do their own `pypdfium2` work alongside
  entityxtract).
- `tests/test_thread_safety.py` — concurrency regression test covering
  concurrent PDFium helpers, concurrent `Document` construction (from
  both bytes and file path, with and without `page_range`), and
  concurrent reads against a shared `Document`.
- "Concurrency & Thread-Safety" section in `README.md` documenting the
  contract.

## [1.0.0] — 2026-04-14

### Breaking Changes
- **Simplified `extract_objects()` API** — The function now accepts a plain list of extractable objects and an `ExtractionConfig` as separate arguments:
  ```python
  # Before (deprecated)
  objects = ObjectsToExtract(objects=[table, string], config=config)
  results = extract_objects(doc, objects)

  # After (v1.0.0)
  results = extract_objects(doc, [table, string], config)
  ```

### Deprecated
- **`ObjectsToExtract`** — This wrapper class now emits a `DeprecationWarning` on instantiation and will be removed in a future release. Use a plain `list[ExtractableObjectTypes]` with a separate `ExtractionConfig` instead.

### Changed
- Updated all internal call sites, tests, and examples to use the new API pattern.