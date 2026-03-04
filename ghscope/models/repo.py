from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, HttpUrl


class Repository(BaseModel):
    id: str
    name: str
    full_name: str
    url: HttpUrl
    is_private: bool
    is_fork: bool
    is_archived: bool
    default_branch: str | None
    created_at: datetime
    updated_at: datetime
