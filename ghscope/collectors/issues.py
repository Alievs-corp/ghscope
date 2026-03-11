from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Iterable, List, Optional, Tuple

from ghscope.client.graphql import GitHubGraphQLClient
from ghscope.models.issue import Issue

logger = logging.getLogger("ghscope.collectors.issues")


ISSUES_QUERY = """
query RepoIssues(
  $owner: String!,
  $name: String!,
  $after: String
) {
  repository(owner: $owner, name: $name) {
    issues(
      first: 100,
      after: $after,
      orderBy: { field: CREATED_AT, direction: DESC },
      states: [OPEN, CLOSED]
    ) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        id
        number
        title
        state
        createdAt
        closedAt
        author {
          login
        }
        assignees(first: 10) {
          nodes {
            login
          }
        }
        comments(first: 1) {
          totalCount
        }
      }
    }
  }
}
"""


def collect_repository_issues(
    client: GitHubGraphQLClient,
    repo_full_name: str,
    since: datetime,
    until: datetime,
) -> List[Issue]:
    """Collect issues for a repository over a time range."""
    if "/" not in repo_full_name:
        raise ValueError(f"Repository full name must be 'owner/name', got: {repo_full_name!r}")
    owner, name = _split_full_name(repo_full_name)
    logger.info(
        "Collecting issues for %s between %s and %s",
        repo_full_name,
        since.isoformat(),
        until.isoformat(),
    )

    issues: List[Issue] = []
    after: Optional[str] = None

    while True:
        data = client.execute(
            ISSUES_QUERY,
            {
                "owner": owner,
                "name": name,
                "after": after,
            },
        )
        repo_data = data.get("repository")
        if not repo_data:
            break

        connection = repo_data["issues"]
        issues.extend(
            _parse_issues(
                repo_full_name=repo_full_name,
                nodes=connection["nodes"],
                since=since,
                until=until,
            ),
        )

        page_info = connection["pageInfo"]
        if not page_info["hasNextPage"]:
            break
        after = page_info["endCursor"]

    return issues


def _split_full_name(full_name: str) -> Tuple[str, str]:
    owner, name = full_name.split("/", 1)
    return owner, name


def _parse_issues(
    repo_full_name: str,
    nodes: Iterable[dict[str, Any]],
    since: datetime,
    until: datetime,
) -> List[Issue]:
    parsed: List[Issue] = []
    for node in nodes:
        created_at = datetime.fromisoformat(node["createdAt"].replace("Z", "+00:00"))
        if created_at < since or created_at > until:
            continue

        author = node.get("author") or {}
        assignees_conn = node.get("assignees") or {}
        assignees_nodes = assignees_conn.get("nodes") or []
        comments = node.get("comments") or {}
        parsed.append(
            Issue(
                id=node["id"],
                number=int(node["number"]),
                title=node["title"],
                state=node["state"],
                created_at=created_at,
                closed_at=(
                    datetime.fromisoformat(node["closedAt"].replace("Z", "+00:00"))
                    if node.get("closedAt")
                    else None
                ),
                author_login=author.get("login"),
                assignee_logins=[
                    login
                    for assignee in assignees_nodes
                    if (login := assignee.get("login")) is not None
                ],
                repository_full_name=repo_full_name,
                comment_count=int(comments.get("totalCount", 0)),
            ),
        )
    return parsed
