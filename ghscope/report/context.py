from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from ghscope.analytics.aggregates import ActivityReport
from ghscope.analytics.timelines import Timelines
from ghscope.models import Commit, Issue, PullRequest, Repository, User


@dataclass
class ReportInput:
    org: Optional[str]
    user: Optional[str]
    since: datetime
    until: datetime
    users: Iterable[User]
    repositories: Iterable[Repository]
    commits: Iterable[Commit]
    pull_requests: Iterable[PullRequest]
    issues: Iterable[Issue]


@dataclass
class ReportContext:
    org: Optional[str]
    user: Optional[str]
    since: datetime
    until: datetime
    activity: ActivityReport
    timelines: Timelines
    users: list[User]
    repositories: list[Repository]
    commits: list[Commit]
    pull_requests: list[PullRequest]
    issues: list[Issue]
    generated_at: datetime
    templates_dir: Path
