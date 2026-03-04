from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl


class User(BaseModel):
    id: str
    login: str
    name: Optional[str] = None
    url: HttpUrl
    created_at: datetime
    is_site_admin: bool = False
    is_bot: bool = False
