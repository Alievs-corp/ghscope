from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, MutableMapping

from ghscope.models import Commit, Issue, PullRequest, Repository, User


@dataclass
class UserActivitySummary:
    login: str
    commits: int
    lines_added: int
    lines_deleted: int
    pull_requests_opened: int
    pull_requests_merged: int
    issues_opened: int
    issues_closed: int
    issues_assigned: int
    reviews_given: int
    reviews_received: int


@dataclass
class RepositoryActivitySummary:
    full_name: str
    commits: int
    lines_added: int
    lines_deleted: int
    pull_requests_opened: int
    pull_requests_merged: int
    issues_opened: int
    issues_closed: int
    contributors: int


@dataclass
class ActivityReport:
    users: Mapping[str, UserActivitySummary]
    repositories: Mapping[str, RepositoryActivitySummary]
    active_contributors: List[str]
    inactive_contributors: List[str]


def aggregate_activity(
    users: Iterable[User],
    repositories: Iterable[Repository],
    commits: Iterable[Commit],
    pull_requests: Iterable[PullRequest],
    issues: Iterable[Issue],
    active_threshold: int = 1,
) -> ActivityReport:
    """Aggregate per-user and per-repository activity."""
    user_logins = {user.login for user in users}
    repo_names = {repo.full_name for repo in repositories}

    user_commits: MutableMapping[str, int] = Counter()
    user_lines_added: MutableMapping[str, int] = Counter()
    user_lines_deleted: MutableMapping[str, int] = Counter()
    repo_commits: MutableMapping[str, int] = Counter()
    repo_lines_added: MutableMapping[str, int] = Counter()
    repo_lines_deleted: MutableMapping[str, int] = Counter()

    for commit in commits:
        login = commit.author_login
        if login:
            user_commits[login] += 1
            user_lines_added[login] += commit.additions
            user_lines_deleted[login] += commit.deletions
        repo = commit.repository_full_name
        repo_commits[repo] += 1
        repo_lines_added[repo] += commit.additions
        repo_lines_deleted[repo] += commit.deletions

    user_pr_opened: MutableMapping[str, int] = Counter()
    user_pr_merged: MutableMapping[str, int] = Counter()
    user_reviews_given: MutableMapping[str, int] = Counter()
    user_reviews_received: MutableMapping[str, int] = Counter()
    repo_pr_opened: MutableMapping[str, int] = Counter()
    repo_pr_merged: MutableMapping[str, int] = Counter()

    for pr in pull_requests:
        repo = pr.repository_full_name
        repo_pr_opened[repo] += 1
        if pr.is_merged:
            repo_pr_merged[repo] += 1

        if pr.author_login:
            user_pr_opened[pr.author_login] += 1
            if pr.is_merged:
                user_pr_merged[pr.author_login] += 1
            user_reviews_received[pr.author_login] += pr.review_count

        for reviewer in pr.reviewer_logins:
            user_reviews_given[reviewer] += 1

    user_issues_opened: MutableMapping[str, int] = Counter()
    user_issues_closed: MutableMapping[str, int] = Counter()
    user_issues_assigned: MutableMapping[str, int] = Counter()
    repo_issues_opened: MutableMapping[str, int] = Counter()
    repo_issues_closed: MutableMapping[str, int] = Counter()

    for issue in issues:
        repo = issue.repository_full_name
        repo_issues_opened[repo] += 1
        if issue.closed_at is not None:
            repo_issues_closed[repo] += 1

        if issue.author_login:
            user_issues_opened[issue.author_login] += 1
            if issue.closed_at is not None:
                user_issues_closed[issue.author_login] += 1

        for assignee in issue.assignee_logins:
            user_issues_assigned[assignee] += 1

    user_summaries: Dict[str, UserActivitySummary] = {}
    for login in sorted(user_logins):
        user_summaries[login] = UserActivitySummary(
            login=login,
            commits=user_commits.get(login, 0),
            lines_added=user_lines_added.get(login, 0),
            lines_deleted=user_lines_deleted.get(login, 0),
            pull_requests_opened=user_pr_opened.get(login, 0),
            pull_requests_merged=user_pr_merged.get(login, 0),
            issues_opened=user_issues_opened.get(login, 0),
            issues_closed=user_issues_closed.get(login, 0),
            issues_assigned=user_issues_assigned.get(login, 0),
            reviews_given=user_reviews_given.get(login, 0),
            reviews_received=user_reviews_received.get(login, 0),
        )

    repo_contributors: MutableMapping[str, set[str]] = defaultdict(set)
    for commit in commits:
        if commit.author_login:
            repo_contributors[commit.repository_full_name].add(commit.author_login)
    for pr in pull_requests:
        if pr.author_login:
            repo_contributors[pr.repository_full_name].add(pr.author_login)
        for reviewer in pr.reviewer_logins:
            repo_contributors[pr.repository_full_name].add(reviewer)
    for issue in issues:
        if issue.author_login:
            repo_contributors[issue.repository_full_name].add(issue.author_login)
        for assignee in issue.assignee_logins:
            repo_contributors[issue.repository_full_name].add(assignee)

    repo_summaries: Dict[str, RepositoryActivitySummary] = {}
    for full_name in sorted(repo_names):
        contributors = repo_contributors.get(full_name, set())
        repo_summaries[full_name] = RepositoryActivitySummary(
            full_name=full_name,
            commits=repo_commits.get(full_name, 0),
            lines_added=repo_lines_added.get(full_name, 0),
            lines_deleted=repo_lines_deleted.get(full_name, 0),
            pull_requests_opened=repo_pr_opened.get(full_name, 0),
            pull_requests_merged=repo_pr_merged.get(full_name, 0),
            issues_opened=repo_issues_opened.get(full_name, 0),
            issues_closed=repo_issues_closed.get(full_name, 0),
            contributors=len(contributors),
        )

    contributor_activity: MutableMapping[str, int] = Counter()
    for summary in user_summaries.values():
        contributor_activity[summary.login] = (
            summary.commits
            + summary.pull_requests_opened
            + summary.issues_opened
            + summary.reviews_given
        )

    active_contributors = sorted(
        login for login, count in contributor_activity.items() if count >= active_threshold
    )
    inactive_contributors = sorted(
        login for login, count in contributor_activity.items() if count < active_threshold
    )

    return ActivityReport(
        users=user_summaries,
        repositories=repo_summaries,
        active_contributors=active_contributors,
        inactive_contributors=inactive_contributors,
    )
