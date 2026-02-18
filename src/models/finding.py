"""Finding model for individual code review issues."""

from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Severity levels for findings."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Location(BaseModel):
    """Code location for a finding."""

    line_start: int
    line_end: int
    column_start: Optional[int] = None
    column_end: Optional[int] = None


class Finding(BaseModel):
    """Individual code review finding."""

    id: UUID = Field(default_factory=uuid4)
    severity: Severity
    category: str
    title: str
    description: str
    location: Optional[Location] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    code_snippet: Optional[str] = None
    suggestion: Optional[str] = None
    references: list[str] = Field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        data = self.model_dump()
        data["id"] = str(self.id)
        return data
