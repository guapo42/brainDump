"""Tests for Pydantic schema validation."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from models.schemas import (
    ExtractionResult,
    PersonEntity,
    Platform,
    ProjectEntity,
    SourceMetadata,
    TaskEntity,
)


class TestSourceMetadata:
    def test_valid_source(self):
        src = SourceMetadata(
            source_id="msg_001",
            platform=Platform.GMAIL,
            sender_name="Alice",
            sender_email="alice@example.com",
            received_at=datetime(2026, 1, 1),
        )
        assert src.source_id == "msg_001"
        assert src.platform == Platform.GMAIL

    def test_invalid_platform_rejected(self):
        with pytest.raises(ValidationError):
            SourceMetadata(
                source_id="msg_001",
                platform="fax",
                sender_name="Alice",
                sender_email="alice@example.com",
                received_at=datetime(2026, 1, 1),
            )

    def test_missing_required_field(self):
        with pytest.raises(ValidationError):
            SourceMetadata(
                source_id="msg_001",
                platform=Platform.SLACK,
                # missing sender_name, sender_email, received_at
            )


class TestTaskEntity:
    def test_defaults(self):
        task = TaskEntity(description="Do something")
        assert task.status == "pending"
        assert task.priority == "medium"
        assert task.due_date is None
        assert task.assignee is None
        assert task.waiting_on is None
        assert task.project is None

    def test_full_task(self):
        task = TaskEntity(
            description="Deploy dbt models",
            status="pending",
            due_date="2026-03-05",
            assignee="You",
            waiting_on="Sarah",
            priority="critical",
            project="EPA Data Modernization",
        )
        assert task.waiting_on == "Sarah"
        assert task.project == "EPA Data Modernization"


class TestExtractionResult:
    def test_from_fixture(self, sample_extraction_result):
        er = sample_extraction_result
        assert len(er.people) == 3
        assert len(er.projects) == 1
        assert len(er.tasks) == 3
        assert er.projects[0].name == "Operation Dormant Seed"

    def test_empty_lists_allowed(self):
        er = ExtractionResult(
            people=[],
            projects=[],
            tasks=[],
            urls=[],
            summary="Nothing found.",
        )
        assert er.summary == "Nothing found."

    def test_summary_required(self):
        with pytest.raises(ValidationError):
            ExtractionResult(
                people=[],
                projects=[],
                tasks=[],
                urls=[],
                # missing summary
            )
