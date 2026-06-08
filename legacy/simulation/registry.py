"""PersonRegistry: canonical person records for the simulation."""

from dataclasses import dataclass
from models.schemas import Platform


@dataclass(frozen=True)
class PersonRecord:
    name: str
    email: str
    role: str
    preferred_platform: Platform


# All actors in the simulation — keys used throughout agents
PEOPLE: dict[str, PersonRecord] = {
    "linda": PersonRecord(
        "Linda Torres", "ltorres@company.com",
        "Manager", Platform.GMAIL,
    ),
    "robert": PersonRecord(
        "Robert Kim", "rkim@company.com",
        "Project Director", Platform.GMAIL,
    ),
    "sarah": PersonRecord(
        "Sarah Chen", "schen@company.com",
        "Senior Engineer", Platform.SLACK,
    ),
    "marcus": PersonRecord(
        "Marcus Webb", "mwebb@company.com",
        "Junior Developer", Platform.SLACK,
    ),
    "priya": PersonRecord(
        "Priya Patel", "ppatel@company.com",
        "Mid-level Developer", Platform.SLACK,
    ),
    "you": PersonRecord(
        "You", "you@company.com",
        "Tech Lead", Platform.GMAIL,
    ),
}
