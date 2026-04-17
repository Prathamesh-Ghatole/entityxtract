"""Tests for the durable extraction pipeline.

Currently only covers type serialization; activity + workflow tests
land in follow-up commits.
"""

from __future__ import annotations

import json

import pytest

from entityxtract.durable.types import (
    DocumentRef,
    EntitySpec,
    ExtractionJobRequest,
    JobProgress,
    ValidationReport,
)
from entityxtract.extractor_types import ExtractionConfig, FileInputMode


# ----- Fixtures -----

@pytest.fixture
def sample_request() -> ExtractionJobRequest:
    return ExtractionJobRequest(
        doc_ref=DocumentRef(
            uri="file:///tmp/test-document.pdf",
            doc_type="pdf",
            page_range=(0, 3),
        ),
        entities=[
            EntitySpec(
                name="Authors",
                kind="table",
                example_schema=json.dumps([
                    {"Name": "Example", "Organization": "Example Org", "Email": "ex@ex.com"},
                ]),
                instructions="Extract authors table.",
                required=True,
            ),
        ],
        config=ExtractionConfig(
            model_name="google/gemini-2.5-flash",
            temperature=0.0,
            file_input_modes=[FileInputMode.FILE],
        ),
        auto_detect=False,
        require_human_approval=False,
    )


# ----- Tests -----

class TestDurableTypes:
    """Test serialization of durable types."""

    def test_document_ref_roundtrip(self):
        ref = DocumentRef(uri="file:///tmp/test.pdf", doc_type="pdf", page_range=(0, 5))
        json_str = ref.model_dump_json()
        restored = DocumentRef.model_validate_json(json_str)
        assert restored.uri == ref.uri
        assert restored.doc_type == ref.doc_type
        assert restored.page_range == (0, 5)

    def test_entity_spec_roundtrip(self):
        spec = EntitySpec(
            name="Test",
            kind="table",
            example_schema='[{"col": "val"}]',
            instructions="Extract test data",
        )
        json_str = spec.model_dump_json()
        restored = EntitySpec.model_validate_json(json_str)
        assert restored.name == "Test"
        assert restored.kind == "table"

    def test_extraction_job_request_roundtrip(self, sample_request: ExtractionJobRequest):
        json_str = sample_request.model_dump_json()
        restored = ExtractionJobRequest.model_validate_json(json_str)
        assert restored.doc_ref.uri == sample_request.doc_ref.uri
        assert len(restored.entities) == 1
        assert restored.entities[0].name == "Authors"

    def test_job_progress_default(self):
        progress = JobProgress()
        assert progress.entity_progress == {}
        assert progress.started_at is None

    def test_validation_report(self):
        report = ValidationReport(
            entity_name="Test",
            is_valid=False,
            issues=["Missing column: Email"],
            suggestions=["Add explicit instruction for Email column"],
        )
        assert not report.is_valid
        assert len(report.issues) == 1
