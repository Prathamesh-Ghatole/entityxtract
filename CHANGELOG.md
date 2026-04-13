# Changelog

All notable changes to **entityxtract** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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