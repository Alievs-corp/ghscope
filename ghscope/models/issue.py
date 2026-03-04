from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class Issue(BaseModel):
    id: str
    number: int
    title: str
    state: str
    created_at: datetime
    closed_at: Optional[datetime]
    author_login: Optional[str]
    assignee_logins: List[str]
    repository_full_name: str
    comment_count: int
