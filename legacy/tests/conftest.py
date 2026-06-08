"""Shared pytest fixtures for brain-dump tests."""

import pytest
from datetime import datetime

from models.schemas import (
    ExtractionResult,
    PersonEntity,
    Platform,
    ProjectEntity,
    SourceMetadata,
    TaskEntity,
)


@pytest.fixture
def sample_email_text():
    """A raw email string for testing the extraction pipeline."""
    return (
        "Hey team, for Operation Dormant Seed, I need Sarah to finalize the "
        "database migration by next Friday. I'm currently blocked waiting on "
        "the AWS credentials from John. Marcus should start writing the Python "
        "extraction scripts once the schema is done."
    )


@pytest.fixture
def sample_source_metadata():
    """A SourceMetadata object representing an incoming email."""
    return SourceMetadata(
        source_id="email_001",
        platform=Platform.GMAIL,
        sender_name="Alex Vance",
        sender_email="avance@rti.org",
        received_at=datetime(2026, 2, 26, 10, 0, 0),
    )


@pytest.fixture
def sample_extraction_result():
    """A pre-built ExtractionResult matching the sample email text."""
    return ExtractionResult(
        people=[
            PersonEntity(name="Sarah", email=None, role=None),
            PersonEntity(name="John", email=None, role=None),
            PersonEntity(name="Marcus", email=None, role=None),
        ],
        projects=[
            ProjectEntity(name="Operation Dormant Seed", status="active", priority="high"),
        ],
        tasks=[
            TaskEntity(
                description="Finalize the database migration",
                status="pending",
                due_date="2026-03-06",
                assignee="Sarah",
                waiting_on=None,
                priority="high",
                project="Operation Dormant Seed",
            ),
            TaskEntity(
                description="Provide AWS credentials",
                status="pending",
                due_date=None,
                assignee="John",
                waiting_on=None,
                priority="high",
                project="Operation Dormant Seed",
            ),
            TaskEntity(
                description="Write Python extraction scripts",
                status="pending",
                due_date=None,
                assignee="Marcus",
                waiting_on="Sarah",
                priority="medium",
                project="Operation Dormant Seed",
            ),
        ],
        urls=[],
        summary="Team is blocked on AWS credentials from John; Sarah must finish "
        "the database migration before Marcus can start extraction scripts.",
    )
