from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .token import TokenConfig, resolve_token


GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"
GITHUB_REST_URL = "https://api.github.com"


@dataclass(frozen=True)
class GitHubAuth:
    """Authentication configuration for GitHub API access."""

    token_config: TokenConfig

    def headers(self) -> Mapping[str, str]:
        token = resolve_token(self.token_config)
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

