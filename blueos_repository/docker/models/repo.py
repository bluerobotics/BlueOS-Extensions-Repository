import dataclasses
from typing import Optional


@dataclasses.dataclass
class RepoInfo:
    downloads: int
    last_updated: Optional[str] = None  # utc timestamp
    date_registered: Optional[str] = None  # utc timestamp
