from __future__ import annotations

from datetime import datetime, timezone

from ghscope.models import Commit, Issue, PullRequest, Repository, User


def test_user_model() -> None:
    user = User(
        id="uid",
        login="jdoe",
        name="John Doe",
        url="https://github.com/jdoe",
        created_at=datetime.now(timezone.utc),
        is_site_admin=False,
        is_bot=False,
    )
    assert user.login == "jdoe"


def test_repository_model() -> None:
    now = datetime.now(timezone.utc)
    repo = Repository(
        id="rid",
        name="repo",
        full_name="org/repo",
        url="https://github.com/org/repo",
        is_private=False,
        is_fork=False,
        is_archived=False,
        default_branch="main",
        created_at=now,
        updated_at=now,
    )
    assert repo.full_name == "org/repo"


def test_commit_model() -> None:
    now = datetime.now(timezone.utc)
    commit = Commit(
        id="cid",
        oid="123",
        message_headline="feat: test",
        message_body=None,
        authored_at=now,
        committed_at=now,
        author_login="jdoe",
        author_name="John Doe",
        repository_full_name="org/repo",
        additions=10,
        deletions=2,
    )
    assert commit.additions == 10


def test_pull_request_model() -> None:
    now = datetime.now(timezone.utc)
    pr = PullRequest(
        id="pid",
        number=1,
        title="Add feature",
        state="MERGED",
        is_merged=True,
        created_at=now,
        merged_at=now,
        closed_at=now,
        author_login="jdoe",
        repository_full_name="org/repo",
        additions=5,
        deletions=1,
        changed_files=2,
        review_count=1,
        comment_count=0,
        reviewer_logins=["reviewer"],
    )
    assert pr.is_merged is True


def test_issue_model() -> None:
    now = datetime.now(timezone.utc)
    issue = Issue(
        id="iid",
        number=1,
        title="Bug",
        state="OPEN",
        created_at=now,
        closed_at=None,
        author_login="jdoe",
        assignee_logins=["jdoe"],
        repository_full_name="org/repo",
        comment_count=0,
    )
    assert issue.state == "OPEN"

