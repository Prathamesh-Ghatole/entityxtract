"""
entityxtract — A provider-agnostic, entity-centric LLM-powered document entity extraction tool.
"""

from .extractor_types import (
    Document,
    DocType,
    ExtractionConfig,
    ExtractionResult,
    ExtractionResults,
    ExtractableObjectTypes,
    FileInputMode,
    ObjectsToExtract,
    StringToExtract,
    TableToExtract,
)
from .extractor import extract_object, extract_objects

__all__ = [
    # Core document
    "Document",
    "DocType",
    # Extraction config & results
    "ExtractionConfig",
    "ExtractionResult",
    "ExtractionResults",
    "ExtractableObjectTypes",
    "FileInputMode",
    "ObjectsToExtract",
    # Extractable object types
    "StringToExtract",
    "TableToExtract",
    # Functions
    "extract_object",
    "extract_objects",
]
