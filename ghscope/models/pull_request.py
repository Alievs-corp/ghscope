from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class PullRequest(BaseModel):
    id: str
    number: int
    title: str
    state: str
    is_merged: bool
    created_at: datetime
    merged_at: Optional[datetime]
    closed_at: Optional[datetime]
    author_login: Optional[str]
    repository_full_name: str
    additions: int
    deletions: int
    changed_files: int
    review_count: int
    comment_count: int
    reviewer_logins: List[str]


