from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


# --- PROV-O: Provenance Tracking ---

class Platform(str, Enum):
    GMAIL = "gmail"
    SLACK = "slack"
    TEAMS = "teams"


class SourceMetadata(BaseModel):
    """PROV-O: Tracking the origin of the information."""
    source_id: str = Field(..., description="Email UID or Slack message TS")
    platform: Platform = Field(..., description="Origin platform")
    sender_name: str = Field(..., description="Display name of the sender")
    sender_email: str = Field(..., description="Email address of the sender")
    received_at: datetime = Field(..., description="When the message was received")


# --- Core Ontology Nodes ---

class PersonEntity(BaseModel):
    """A person mentioned in or sending communications."""
    name: str = Field(..., description="Full name of the person")
    email: Optional[str] = Field(None, description="Email if available")
    role: Optional[str] = Field(None, description="Role or title if mentioned")
    aliases: List[str] = Field(default_factory=list, description="Alternate names (e.g. first name only)")


class ProjectEntity(BaseModel):
    """A project or initiative referenced in communications."""
    name: str = Field(..., description="Project name or codename")
    status: str = Field("active", description="Current status: active, blocked, completed")
    priority: str = Field("medium", description="Priority: low, medium, high, critical")


# --- PPO: Project Planning Ontology ---

class TaskEntity(BaseModel):
    """A task, action item, or deliverable extracted from communications."""
    description: str = Field(..., description="What needs to be done")
    status: str = Field("pending", description="pending, in_progress, done")
    due_date: Optional[str] = Field(None, description="Deadline as ISO date string if mentioned")
    assignee: Optional[str] = Field(None, description="Person responsible for this task")
    waiting_on: Optional[str] = Field(None, description="Person this task is blocked by")
    priority: str = Field("medium", description="low, medium, high, critical")
    project: Optional[str] = Field(None, description="Project this task belongs to")


# --- Extraction Result (LLM Output) ---

class ExtractionResult(BaseModel):
    """The full structured payload from LLM entity extraction.
    Used to update both Neo4j (graph) and ChromaDB (vector store)."""
    people: List[PersonEntity] = Field(default_factory=list, description="People mentioned")
    projects: List[ProjectEntity] = Field(default_factory=list, description="Projects referenced")
    tasks: List[TaskEntity] = Field(default_factory=list, description="Action items and deliverables")
    urls: List[str] = Field(default_factory=list, description="URLs or links found")
    summary: str = Field(..., description="Short summary for ChromaDB embedding")
