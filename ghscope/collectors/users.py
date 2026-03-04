from __future__ import annotations

import logging

from ghscope.client.graphql import GitHubGraphQLClient
from ghscope.models.user import User

logger = logging.getLogger("ghscope.collectors.users")


ORG_MEMBERS_QUERY = """
query OrgMembers($login: String!, $after: String) {
  organization(login: $login) {
    membersWithRole(first: 100, after: $after) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        id
        login
        name
        url
        createdAt
        isSiteAdmin
      }
    }
  }
}
"""


def collect_org_members(client: GitHubGraphQLClient, org: str) -> list[User]:
    """Collect members of an organization."""
    logger.info("Collecting members for organization %s", org)
    users: list[User] = []
    after: str | None = None

    while True:
        data = client.execute(
            ORG_MEMBERS_QUERY,
            {"login": org, "after": after},
        )
        org_data = data.get("organization")
        if not org_data:
            break

        connection = org_data["membersWithRole"]
        for node in connection["nodes"]:
            users.append(
                User(
                    id=node["id"],
                    login=node["login"],
                    name=node.get("name"),
                    url=node["url"],
                    created_at=node["createdAt"],
                    is_site_admin=bool(node.get("isSiteAdmin", False)),
                    is_bot=False,
                ),
            )

        page_info = connection["pageInfo"]
        if not page_info["hasNextPage"]:
            break
        after = page_info["endCursor"]

    logger.info(
        "Collected %d members for organization %s: %s",
        len(users),
        org,
        [user.login for user in users],
    )
    return users


USER_QUERY = """
query User($login: String!) {
  user(login: $login) {
    id
    login
    name
    url
    createdAt
    isSiteAdmin
    isBot
  }
}
"""


def collect_user(client: GitHubGraphQLClient, login: str) -> User:
    """Collect a single user by login."""
    logger.info("Collecting user %s", login)
    data = client.execute(USER_QUERY, {"login": login})
    user_data = data.get("user")
    if not user_data:
        raise ValueError(f"User {login!r} not found")

    return User(
        id=user_data["id"],
        login=user_data["login"],
        name=user_data.get("name"),
        url=user_data["url"],
        created_at=user_data["createdAt"],
        is_site_admin=bool(user_data.get("isSiteAdmin", False)),
        is_bot=bool(user_data.get("isBot", False)),
    )
