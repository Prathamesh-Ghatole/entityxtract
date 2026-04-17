"""Non-agent Temporal activities for document I/O.

These are registered directly on the Worker (not via TemporalAgent)
because they are infrastructure operations, not agent tools.
"""

from __future__ import annotations

import base64
from pathlib import Path
from urllib.parse import urlparse

from temporalio import activity
from temporalio.exceptions import ApplicationError

from .types import DocumentRef


def _resolve_uri(uri: str) -> Path:
    """Turn a file:// URI into a local Path, or raise for unsupported schemes."""
    parsed = urlparse(uri)
    if parsed.scheme in ("", "file"):
        return Path(parsed.path)
    raise ApplicationError(
        f"Unsupported URI scheme: {parsed.scheme!r}. Only file:// is currently supported.",
        type="UnsupportedURIScheme",
        non_retryable=True,
    )


@activity.defn
async def load_document_activity(doc_ref_json: str) -> str:
    """Materialise a DocumentRef into extracted text content.

    Returns the document text as a JSON string so it fits in history
    without exceeding the 2 MB payload limit for most documents.
    """
    from entityxtract.extractor_types import Document

    doc_ref = DocumentRef.model_validate_json(doc_ref_json)
    path = _resolve_uri(doc_ref.uri)

    if not path.exists():
        raise ApplicationError(
            f"Document not found: {path}",
            type="DocumentNotFound",
            non_retryable=True,
        )

    page_range = tuple(doc_ref.page_range) if doc_ref.page_range else None
    doc = Document(file_path=path, page_range=page_range)
    return doc.text


@activity.defn
async def render_pdf_pages_activity(doc_ref_json: str) -> list[str]:
    """Render PDF pages as base64-encoded JPEG strings.

    Returns a list of base64 strings, one per page.  For very large
    documents, consider splitting into smaller page ranges.
    """
    from entityxtract.pdf.extractor import pdf_to_image

    doc_ref = DocumentRef.model_validate_json(doc_ref_json)
    path = _resolve_uri(doc_ref.uri)

    if doc_ref.doc_type.lower() != "pdf":
        raise ApplicationError(
            f"render_pdf_pages only supports PDFs, got {doc_ref.doc_type!r}",
            type="InvalidDocType",
            non_retryable=True,
        )

    with open(path, "rb") as f:
        pdf_bytes = f.read()

    if doc_ref.page_range:
        from entityxtract.pdf.extractor import trim_pdf_pages
        pdf_bytes = trim_pdf_pages(pdf_bytes, doc_ref.page_range[0], doc_ref.page_range[1])

    images = pdf_to_image(pdf_bytes, scale=2, combine_pages=False)
    if not isinstance(images, list):
        images = [images]

    from io import BytesIO

    result: list[str] = []
    for img in images:
        if getattr(img, "mode", None) != "RGB":
            img = img.convert("RGB")
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=80)
        result.append(base64.b64encode(buf.getvalue()).decode())

    activity.heartbeat(f"Rendered {len(result)} pages")
    return result
