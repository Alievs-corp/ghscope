from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date
from typing import Iterable, List, Mapping

from ghscope.models import Commit, Issue, PullRequest


@dataclass
class ActivityBucket:
    day: date
    commits: int
    pull_requests: int
    issues: int


@dataclass
class Timelines:
    by_day: List[ActivityBucket]


def build_timelines(
    commits: Iterable[Commit],
    pull_requests: Iterable[PullRequest],
    issues: Iterable[Issue],
) -> Timelines:
    commit_counts: Mapping[date, int] = Counter()
    pr_counts: Mapping[date, int] = Counter()
    issue_counts: Mapping[date, int] = Counter()

    for commit in commits:
        commit_date = commit.committed_at.date()
        commit_counts[commit_date] = commit_counts.get(commit_date, 0) + 1

    for pr in pull_requests:
        pr_date = pr.created_at.date()
        pr_counts[pr_date] = pr_counts.get(pr_date, 0) + 1

    for issue in issues:
        issue_date = issue.created_at.date()
        issue_counts[issue_date] = issue_counts.get(issue_date, 0) + 1

    all_days = sorted(
        {*(commit_counts.keys()), *(pr_counts.keys()), *(issue_counts.keys())},
    )

    buckets: List[ActivityBucket] = []
    for day in all_days:
        buckets.append(
            ActivityBucket(
                day=day,
                commits=commit_counts.get(day, 0),
                pull_requests=pr_counts.get(day, 0),
                issues=issue_counts.get(day, 0),
            ),
        )

    return Timelines(by_day=buckets)

