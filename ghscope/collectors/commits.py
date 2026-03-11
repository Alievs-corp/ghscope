from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Iterable, List, Optional, Tuple

from ghscope.client.graphql import GitHubGraphQLClient
from ghscope.models.commit import Commit

logger = logging.getLogger("ghscope.collectors.commits")


COMMITS_QUERY = """
query RepoCommits(
  $owner: String!,
  $name: String!,
  $since: GitTimestamp,
  $until: GitTimestamp,
  $after: String
) {
  repository(owner: $owner, name: $name) {
    defaultBranchRef {
      name
      target {
        ... on Commit {
          history(first: 100, after: $after, since: $since, until: $until) {
            pageInfo {
              hasNextPage
              endCursor
            }
            nodes {
              id
              oid
              messageHeadline
              messageBody
              committedDate
              authoredDate
              author {
                name
                user {
                  login
                }
              }
              additions
              deletions
            }
          }
        }
      }
    }
  }
}
"""


def collect_repository_commits(
    client: GitHubGraphQLClient,
    repo_full_name: str,
    since: datetime,
    until: datetime,
) -> List[Commit]:
    """Collect commits for a repository over a time range."""
    owner, name = _split_full_name(repo_full_name)
    logger.info(
        "Collecting commits for %s between %s and %s",
        repo_full_name,
        since.isoformat(),
        until.isoformat(),
    )
    commits: List[Commit] = []
    after: Optional[str] = None

    since_str = since.isoformat()
    until_str = until.isoformat()

    while True:
        data = client.execute(
            COMMITS_QUERY,
            {
                "owner": owner,
                "name": name,
                "since": since_str,
                "until": until_str,
                "after": after,
            },
        )
        repo_data = data.get("repository")
        if not repo_data:
            break

        default_branch = repo_data.get("defaultBranchRef")
        if not default_branch:
            break

        target = default_branch.get("target")
        if not target:
            break

        history = target["history"]
        commits.extend(
            _parse_commits(
                repo_full_name=repo_full_name,
                nodes=history["nodes"],
            ),
        )

        page_info = history["pageInfo"]
        if not page_info["hasNextPage"]:
            break
        after = page_info["endCursor"]

    return commits


def _split_full_name(full_name: str) -> Tuple[str, str]:
    # Must be exactly "owner/name" with non-empty parts.
    if full_name.count("/") != 1:
        raise ValueError(
            f"Repository full name must be 'owner/name', got: {full_name!r}",
        )
    owner, name = full_name.split("/", 1)
    owner = owner.strip()
    name = name.strip()
    if not owner or not name:
        raise ValueError(
            f"Repository full name must be 'owner/name' with non-empty owner and name, got: {full_name!r}",
        )
    return owner, name


def _parse_commits(repo_full_name: str, nodes: Iterable[dict[str, Any]]) -> List[Commit]:
    parsed: List[Commit] = []
    for node in nodes:
        author = node.get("author") or {}
        author_user = author.get("user") or {}
        authored_at = _parse_iso_date(node["authoredDate"])
        committed_at = _parse_iso_date(node["committedDate"])
        parsed.append(
            Commit(
                id=node["id"],
                oid=node["oid"],
                message_headline=node.get("messageHeadline", ""),
                message_body=node.get("messageBody"),
                authored_at=authored_at,
                committed_at=committed_at,
                author_login=author_user.get("login"),
                author_name=author.get("name"),
                repository_full_name=repo_full_name,
                additions=node.get("additions", 0),
                deletions=node.get("deletions", 0),
            ),
        )
    return parsed


def _parse_iso_date(value: str) -> datetime:
    """Parse ISO 8601 date string from GraphQL (e.g. with Z suffix) to timezone-aware datetime."""
    normalized = value.replace("Z", "+00:00")
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt
