from __future__ import annotations

import logging
from datetime import datetime
from typing import Iterable, List, Optional, Tuple

from ghscope.client.graphql import GitHubGraphQLClient
from ghscope.models.pull_request import PullRequest

logger = logging.getLogger("ghscope.collectors.pull_requests")


PULL_REQUESTS_QUERY = """
query RepoPullRequests(
  $owner: String!,
  $name: String!,
  $after: String
) {
  repository(owner: $owner, name: $name) {
    pullRequests(
      first: 50,
      after: $after,
      orderBy: { field: CREATED_AT, direction: DESC },
      states: [OPEN, MERGED, CLOSED]
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
        mergedAt
        additions
        deletions
        changedFiles
        author {
          login
        }
        comments(first: 1) {
          totalCount
        }
        reviews(first: 100) {
          totalCount
          nodes {
            author {
              login
            }
            state
            submittedAt
          }
        }
      }
    }
  }
}
"""


def collect_repository_pull_requests(
    client: GitHubGraphQLClient,
    repo_full_name: str,
    since: datetime,
    until: datetime,
) -> List[PullRequest]:
    """Collect pull requests for a repository over a time range."""
    owner, name = _split_full_name(repo_full_name)
    logger.info(
        "Collecting pull requests for %s between %s and %s",
        repo_full_name,
        since.isoformat(),
        until.isoformat(),
    )

    since_str = since.isoformat()
    until_str = until.isoformat()

    pull_requests: List[PullRequest] = []
    after: Optional[str] = None

    while True:
        data = client.execute(
            PULL_REQUESTS_QUERY,
            {
                "owner": owner,
                "name": name,
                "after": after,
            },
        )
        repo_data = data.get("repository")
        if not repo_data:
            break

        connection = repo_data["pullRequests"]
        pull_requests.extend(
            _parse_pull_requests(
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

    return pull_requests


def _split_full_name(full_name: str) -> Tuple[str, str]:
    owner, name = full_name.split("/", 1)
    return owner, name


def _parse_pull_requests(
    repo_full_name: str,
    nodes: Iterable[dict],
    since: datetime,
    until: datetime,
) -> List[PullRequest]:
    parsed: List[PullRequest] = []
    for node in nodes:
        created_at = datetime.fromisoformat(node["createdAt"].replace("Z", "+00:00"))
        if created_at < since or created_at > until:
            continue

        author = node.get("author") or {}
        reviews = node.get("reviews") or {}
        comments = node.get("comments") or {}
        review_nodes = reviews.get("nodes") or []
        reviewer_logins = []
        for review in review_nodes:
            review_author = review.get("author") or {}
            login = review_author.get("login")
            if login:
                reviewer_logins.append(login)

        parsed.append(
            PullRequest(
                id=node["id"],
                number=int(node["number"]),
                title=node["title"],
                state=node["state"],
                is_merged=node.get("mergedAt") is not None,
                created_at=created_at,
                merged_at=(
                    datetime.fromisoformat(node["mergedAt"].replace("Z", "+00:00"))
                    if node.get("mergedAt")
                    else None
                ),
                closed_at=(
                    datetime.fromisoformat(node["closedAt"].replace("Z", "+00:00"))
                    if node.get("closedAt")
                    else None
                ),
                author_login=author.get("login"),
                repository_full_name=repo_full_name,
                additions=node.get("additions", 0),
                deletions=node.get("deletions", 0),
                changed_files=node.get("changedFiles", 0),
                review_count=int(reviews.get("totalCount", 0)),
                comment_count=int(comments.get("totalCount", 0)),
                reviewer_logins=reviewer_logins,
            ),
        )
    return parsed


