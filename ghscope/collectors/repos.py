from __future__ import annotations

import logging
from typing import Any, Iterable, List

from ghscope.client.graphql import GitHubGraphQLClient
from ghscope.models.repo import Repository

logger = logging.getLogger("ghscope.collectors.repos")


ORG_REPOS_QUERY = """
query OrgRepositories($login: String!, $after: String) {
  organization(login: $login) {
    repositories(
      first: 100,
      after: $after,
      orderBy: { field: PUSHED_AT, direction: DESC }
    ) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        id
        name
        nameWithOwner
        url
        isPrivate
        isFork
        isArchived
        defaultBranchRef {
          name
        }
        createdAt
        updatedAt
      }
    }
  }
}
"""


USER_REPOS_QUERY = """
query UserRepositories($login: String!, $after: String) {
  user(login: $login) {
    repositories(
      first: 100,
      after: $after,
      orderBy: { field: PUSHED_AT, direction: DESC }
    ) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        id
        name
        nameWithOwner
        url
        isPrivate
        isFork
        isArchived
        defaultBranchRef {
          name
        }
        createdAt
        updatedAt
      }
    }
  }
}
"""


def collect_org_repositories(client: GitHubGraphQLClient, org: str) -> List[Repository]:
    """Collect repositories for an organization."""
    logger.info("Collecting repositories for organization %s", org)
    repos: List[Repository] = []
    after: str | None = None

    while True:
        data = client.execute(
            ORG_REPOS_QUERY,
            {"login": org, "after": after},
        )
        org_data = data.get("organization")
        if not org_data:
            break

        connection = org_data["repositories"]
        repos.extend(_parse_repositories(connection["nodes"]))

        page_info = connection["pageInfo"]
        if not page_info["hasNextPage"]:
            break
        after = page_info["endCursor"]

    logger.info(
        "Collected %d repositories for organization %s: %s",
        len(repos),
        org,
        [repo.full_name for repo in repos],
    )
    return repos


def collect_user_repositories(client: GitHubGraphQLClient, login: str) -> List[Repository]:
    """Collect repositories for a user."""
    logger.info("Collecting repositories for user %s", login)
    repos: List[Repository] = []
    after: str | None = None

    while True:
        data = client.execute(
            USER_REPOS_QUERY,
            {"login": login, "after": after},
        )
        user_data = data.get("user")
        if not user_data:
            break

        connection = user_data["repositories"]
        repos.extend(_parse_repositories(connection["nodes"]))

        page_info = connection["pageInfo"]
        if not page_info["hasNextPage"]:
            break
        after = page_info["endCursor"]

    return repos


def _parse_repositories(nodes: Iterable[dict[str, Any]]) -> List[Repository]:
    parsed: List[Repository] = []
    for node in nodes:
        parsed.append(
            Repository(
                id=node["id"],
                name=node["name"],
                full_name=node["nameWithOwner"],
                url=node["url"],
                is_private=bool(node["isPrivate"]),
                is_fork=bool(node["isFork"]),
                is_archived=bool(node["isArchived"]),
                default_branch=node["defaultBranchRef"]["name"]
                if node.get("defaultBranchRef")
                else None,
                created_at=node["createdAt"],
                updated_at=node["updatedAt"],
            ),
        )
    return parsed
