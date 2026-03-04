from __future__ import annotations

from datetime import datetime, timezone

from ghscope.analytics.aggregates import aggregate_activity
from ghscope.analytics.timelines import build_timelines
from ghscope.models import Commit, Issue, PullRequest, Repository, User


def _now() -> datetime:
    return datetime(2025, 1, 1, tzinfo=timezone.utc)


def test_aggregate_activity_basic() -> None:
    users = [
        User(
            id="u1",
            login="alice",
            name=None,
            url="https://github.com/alice",
            created_at=_now(),
            is_site_admin=False,
            is_bot=False,
        ),
        User(
            id="u2",
            login="bob",
            name=None,
            url="https://github.com/bob",
            created_at=_now(),
            is_site_admin=False,
            is_bot=False,
        ),
    ]
    repos = [
        Repository(
            id="r1",
            name="repo",
            full_name="org/repo",
            url="https://github.com/org/repo",
            is_private=False,
            is_fork=False,
            is_archived=False,
            default_branch="main",
            created_at=_now(),
            updated_at=_now(),
        ),
    ]
    commit = Commit(
        id="c1",
        oid="abc",
        message_headline="test",
        message_body=None,
        authored_at=_now(),
        committed_at=_now(),
        author_login="alice",
        author_name=None,
        repository_full_name="org/repo",
        additions=5,
        deletions=1,
    )
    pr = PullRequest(
        id="p1",
        number=1,
        title="PR",
        state="MERGED",
        is_merged=True,
        created_at=_now(),
        merged_at=_now(),
        closed_at=_now(),
        author_login="alice",
        repository_full_name="org/repo",
        additions=5,
        deletions=1,
        changed_files=1,
        review_count=1,
        comment_count=0,
        reviewer_logins=["bob"],
    )
    issue = Issue(
        id="i1",
        number=1,
        title="Issue",
        state="OPEN",
        created_at=_now(),
        closed_at=None,
        author_login="alice",
        assignee_logins=["bob"],
        repository_full_name="org/repo",
        comment_count=0,
    )

    report = aggregate_activity(
        users=users,
        repositories=repos,
        commits=[commit],
        pull_requests=[pr],
        issues=[issue],
        active_threshold=1,
    )

    assert report.users["alice"].commits == 1
    assert report.users["alice"].pull_requests_opened == 1
    assert report.users["alice"].issues_opened == 1
    assert report.users["bob"].reviews_given == 1
    assert "alice" in report.active_contributors
    assert "bob" in report.active_contributors


def test_build_timelines_basic() -> None:
    now = _now()
    commits = [
        Commit(
            id="c1",
            oid="abc",
            message_headline="test",
            message_body=None,
            authored_at=now,
            committed_at=now,
            author_login="alice",
            author_name=None,
            repository_full_name="org/repo",
            additions=5,
            deletions=1,
        ),
    ]
    prs = [
        PullRequest(
            id="p1",
            number=1,
            title="PR",
            state="MERGED",
            is_merged=True,
            created_at=now,
            merged_at=now,
            closed_at=now,
            author_login="alice",
            repository_full_name="org/repo",
            additions=5,
            deletions=1,
            changed_files=1,
            review_count=1,
            comment_count=0,
            reviewer_logins=["bob"],
        ),
    ]
    issues = [
        Issue(
            id="i1",
            number=1,
            title="Issue",
            state="OPEN",
            created_at=now,
            closed_at=None,
            author_login="alice",
            assignee_logins=["bob"],
            repository_full_name="org/repo",
            comment_count=0,
        ),
    ]

    timelines = build_timelines(commits=commits, pull_requests=prs, issues=issues)
    assert len(timelines.by_day) == 1
    bucket = timelines.by_day[0]
    assert bucket.commits == 1
    assert bucket.pull_requests == 1
    assert bucket.issues == 1
