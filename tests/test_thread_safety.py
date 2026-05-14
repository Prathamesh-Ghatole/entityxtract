"""
Concurrency regression tests for entityxtract's PDF / Document plumbing.

Why this exists
---------------
PDFium (the C library behind ``pypdfium2``) is not thread-safe. Before the
``_PDFIUM_LOCK`` and the eager-materialisation design of ``Document`` were
introduced, these tests would segfault the interpreter or produce corrupted
output under concurrent load. The assertions below are intentionally
conservative:

- All threads must complete without raising.
- All threads must see *identical* output for identical inputs (PDFium work
  is deterministic when correctly serialised; divergence = memory
  corruption).
- After a ``Document`` is constructed, readers must observe stable
  ``.binary`` / ``.text`` / ``.image`` across any number of concurrent
  accesses.

These tests do NOT make LLM calls — they exercise only the PDF/Document
layer, so they run offline and are cheap enough for CI.

Run with:
    uv run pytest tests/test_thread_safety.py -v
or:
    uv run python tests/test_thread_safety.py
"""

from __future__ import annotations

import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pytest
from PIL.Image import Image as PILImageType

from entityxtract.extractor_types import Document, DocType
from entityxtract.pdf.extractor import (
    get_pdf_page_count,
    pdf_to_image,
    pdf_to_text,
    pdfium_lock,
    trim_pdf_pages,
)

SAMPLE_PDF_PATH = Path(__file__).parent / "data" / "attention-is-all-you-need.pdf"

# How many worker threads to spawn. High enough to reliably surface data
# races on multi-core machines but still fast (< ~5s on a laptop).
N_THREADS = 16


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def pdf_bytes() -> bytes:
    assert SAMPLE_PDF_PATH.exists(), f"sample PDF missing: {SAMPLE_PDF_PATH}"
    return SAMPLE_PDF_PATH.read_bytes()


def _run_concurrently(fn, n: int = N_THREADS):
    """Run ``fn(i)`` on ``n`` threads; return list of results in submit order.

    Re-raises any worker exception on the main thread so pytest sees it.
    """
    results = [None] * n
    with ThreadPoolExecutor(max_workers=n) as pool:
        future_to_idx = {pool.submit(fn, i): i for i in range(n)}
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            results[idx] = future.result()  # re-raises on failure
    return results


def _image_fingerprint(img) -> str:
    """Stable fingerprint of a PIL image (or list of them) for equality checks."""
    if isinstance(img, list):
        return "|".join(_image_fingerprint(i) for i in img)
    if not isinstance(img, PILImageType):
        return repr(img)
    # tobytes() of a fully-decoded RGB image is deterministic.
    return hashlib.sha256(img.tobytes()).hexdigest()


# ---------------------------------------------------------------------------
# 1. PDFium helper functions under concurrent load
# ---------------------------------------------------------------------------


def test_concurrent_get_pdf_page_count(pdf_bytes: bytes):
    """Every thread must agree on the page count, and none may crash."""
    page_counts = _run_concurrently(lambda _i: get_pdf_page_count(pdf_bytes))
    assert len(set(page_counts)) == 1, (
        f"divergent page counts across threads: {page_counts}"
    )
    assert page_counts[0] > 0


def test_concurrent_pdf_to_text(pdf_bytes: bytes):
    texts = _run_concurrently(lambda _i: pdf_to_text(pdf_bytes))
    # All threads must produce byte-identical output; otherwise something
    # in PDFium raced.
    unique = {hashlib.sha256(t.encode()).hexdigest() for t in texts}
    assert len(unique) == 1, f"pdf_to_text diverged across threads: {len(unique)} variants"
    assert len(texts[0]) > 0


def test_concurrent_pdf_to_image(pdf_bytes: bytes):
    # scale=1 to keep this test cheap; correctness, not resolution, is what
    # we're validating.
    images = _run_concurrently(lambda _i: pdf_to_image(pdf_bytes, scale=1))
    fingerprints = {_image_fingerprint(img) for img in images}
    assert len(fingerprints) == 1, (
        f"pdf_to_image diverged across threads: {len(fingerprints)} variants"
    )


def test_concurrent_trim_pdf_pages(pdf_bytes: bytes):
    trimmed = _run_concurrently(lambda _i: trim_pdf_pages(pdf_bytes, 0, 2))
    unique = {hashlib.sha256(b).hexdigest() for b in trimmed}
    # trim_pdf_pages scrubs non-deterministic metadata, so all threads must
    # produce byte-identical output.
    assert len(unique) == 1, (
        f"trim_pdf_pages diverged across threads: {len(unique)} variants"
    )


def test_concurrent_mixed_helpers(pdf_bytes: bytes):
    """Intermix every helper across threads — the RLock must handle the mix."""

    def worker(i: int):
        if i % 4 == 0:
            return ("count", get_pdf_page_count(pdf_bytes))
        if i % 4 == 1:
            return ("text_len", len(pdf_to_text(pdf_bytes)))
        if i % 4 == 2:
            return ("img_fp", _image_fingerprint(pdf_to_image(pdf_bytes, scale=1)))
        return ("trim_len", len(trim_pdf_pages(pdf_bytes, 0, 1)))

    # Just asserting no exception is raised is the main contract here.
    results = _run_concurrently(worker, n=N_THREADS * 2)
    assert len(results) == N_THREADS * 2


# ---------------------------------------------------------------------------
# 2. Document construction under concurrent load
# ---------------------------------------------------------------------------


def test_concurrent_document_construction_from_path():
    docs = _run_concurrently(lambda _i: Document(SAMPLE_PDF_PATH))
    text_hashes = {hashlib.sha256(d.text.encode()).hexdigest() for d in docs}
    assert len(text_hashes) == 1, (
        f"Document.text diverged across concurrent constructions: {len(text_hashes)}"
    )
    # All should be PDFs with non-empty text and an image rendered.
    for d in docs:
        assert d.file_type == DocType.PDF
        assert len(d.text) > 0
        assert d.image is not None


def test_concurrent_document_construction_from_bytes(pdf_bytes: bytes):
    docs = _run_concurrently(
        lambda _i: Document(file_bytes=pdf_bytes, file_type="pdf")
    )
    text_hashes = {hashlib.sha256(d.text.encode()).hexdigest() for d in docs}
    assert len(text_hashes) == 1


def test_concurrent_document_construction_with_page_range(pdf_bytes: bytes):
    docs = _run_concurrently(
        lambda _i: Document(file_bytes=pdf_bytes, file_type="pdf", page_range=(0, 2))
    )
    binary_hashes = {hashlib.sha256(d.binary).hexdigest() for d in docs}
    # trim_pdf_pages scrubs metadata, so output bytes must match.
    assert len(binary_hashes) == 1, (
        f"page_range trim diverged across threads: {len(binary_hashes)}"
    )
    text_hashes = {hashlib.sha256(d.text.encode()).hexdigest() for d in docs}
    assert len(text_hashes) == 1


def test_concurrent_document_construction_render_images_false(pdf_bytes: bytes):
    """render_images=False should still produce consistent text; image stays lazy."""
    docs = _run_concurrently(
        lambda _i: Document(file_bytes=pdf_bytes, file_type="pdf", render_images=False)
    )
    text_hashes = {hashlib.sha256(d.text.encode()).hexdigest() for d in docs}
    assert len(text_hashes) == 1
    # Each doc's .image should be None (not yet rendered) OR a rendered
    # image if the test itself happened to read it — but we didn't read it
    # here, so the private flag should still be False.
    for d in docs:
        assert d._image_materialized is False


# ---------------------------------------------------------------------------
# 3. Shared Document, many readers
# ---------------------------------------------------------------------------


def test_shared_document_concurrent_reads(pdf_bytes: bytes):
    """Construct once, read from many threads. Readers must see stable data."""
    doc = Document(file_bytes=pdf_bytes, file_type="pdf")

    text_ref = doc.text
    bin_ref = doc.binary
    img_ref_fp = _image_fingerprint(doc.image)

    def reader(_i: int):
        # Touch all three properties many times from each thread.
        t = doc.text
        b = doc.binary
        fp = _image_fingerprint(doc.image)
        return (t, b, fp)

    results = _run_concurrently(reader, n=N_THREADS)
    for t, b, fp in results:
        assert t == text_ref
        assert b == bin_ref
        assert fp == img_ref_fp


def test_shared_document_lazy_image_concurrent(pdf_bytes: bytes):
    """
    With render_images=False, the first .image access lazily renders under
    _lazy_lock. N concurrent readers must all end up with the same image
    and must not trigger multiple render passes (double-checked locking).
    """
    doc = Document(file_bytes=pdf_bytes, file_type="pdf", render_images=False)
    assert doc._image_materialized is False

    # Gate all threads behind a barrier so they race into .image simultaneously.
    barrier = threading.Barrier(N_THREADS)

    def reader(_i: int):
        barrier.wait()
        return _image_fingerprint(doc.image)

    fingerprints = _run_concurrently(reader, n=N_THREADS)
    assert len(set(fingerprints)) == 1, (
        f"lazy .image render diverged across threads: {len(set(fingerprints))}"
    )
    assert doc._image_materialized is True


# ---------------------------------------------------------------------------
# 4. Public lock accessor
# ---------------------------------------------------------------------------


def test_pdfium_lock_is_reentrant_and_module_wide():
    lock = pdfium_lock()
    # Same object on every call.
    assert pdfium_lock() is lock
    # RLock: acquiring twice on the same thread must not deadlock.
    with lock:
        with lock:
            pass


# ---------------------------------------------------------------------------
# Ad-hoc entry point — run as a script for quick local repro.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-v"]))
