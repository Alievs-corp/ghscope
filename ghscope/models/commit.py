from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class Commit(BaseModel):
    id: str
    oid: str
    message_headline: str
    message_body: str | None
    authored_at: datetime
    committed_at: datetime
    author_login: str | None
    author_name: str | None
    repository_full_name: str
    additions: int
    deletions: int
