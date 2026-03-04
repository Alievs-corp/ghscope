from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from ghscope.analytics.aggregates import ActivityReport, aggregate_activity
from ghscope.analytics.timelines import Timelines, build_timelines
from ghscope.models import Commit, Issue, PullRequest, Repository, User


@dataclass
class AnalyticsResult:
    activity: ActivityReport
    timelines: Timelines


def compute_analytics(
    users: Iterable[User],
    repositories: Iterable[Repository],
    commits: Iterable[Commit],
    pull_requests: Iterable[PullRequest],
    issues: Iterable[Issue],
    since: datetime,
    until: datetime,
) -> AnalyticsResult:
    activity = aggregate_activity(
        users=users,
        repositories=repositories,
        commits=commits,
        pull_requests=pull_requests,
        issues=issues,
    )
    timelines = build_timelines(
        commits=commits,
        pull_requests=pull_requests,
        issues=issues,
    )
    return AnalyticsResult(activity=activity, timelines=timelines)
