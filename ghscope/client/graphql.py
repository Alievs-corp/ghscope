from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Tuple

import httpx

from ghscope.auth.app import GITHUB_GRAPHQL_URL, GitHubAuth

logger = logging.getLogger("ghscope.client.graphql")


class GitHubApiError(RuntimeError):
    """Raised when GitHub's API returns an error response."""


CacheKey = Tuple[str, Tuple[Tuple[str, Any], ...]]


def _make_cache_key(query: str, variables: Mapping[str, Any]) -> CacheKey:
    return (query, tuple(sorted(variables.items())))


@dataclass
class GitHubGraphQLClient:
    auth: GitHubAuth
    timeout: float = 30.0
    _client: httpx.Client = field(init=False, repr=False)
    _cache: Dict[CacheKey, Any] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        self._client = httpx.Client(
            base_url="https://api.github.com",
            headers=dict(self.auth.headers()),
            timeout=self.timeout,
        )

    def close(self) -> None:
        self._client.close()

    def execute(self, query: str, variables: Optional[Mapping[str, Any]] = None) -> Any:
        if variables is None:
            variables = {}

        cache_key = _make_cache_key(query, variables)
        if cache_key in self._cache:
            return self._cache[cache_key]

        response = self._client.post(
            GITHUB_GRAPHQL_URL.replace("https://api.github.com", ""),
            json={"query": query, "variables": variables},
        )
        self._log_rate_limit(response.headers)

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise GitHubApiError(f"GitHub GraphQL request failed: {exc}") from exc

        payload = response.json()
        logger.debug("GraphQL response payload: %s", payload)
        if "errors" in payload:
            raise GitHubApiError(f"GitHub GraphQL error: {payload['errors']}")

        data = payload.get("data", {})
        self._cache[cache_key] = data
        return data

    @staticmethod
    def _log_rate_limit(headers: Mapping[str, str]) -> None:
        remaining = headers.get("X-RateLimit-Remaining")
        limit = headers.get("X-RateLimit-Limit")
        reset = headers.get("X-RateLimit-Reset")
        if remaining is None or limit is None:
            return

        try:
            remaining_int = int(remaining)
            limit_int = int(limit)
        except ValueError:
            logger.debug("Non-integer rate limit headers: %s/%s", remaining, limit)
            return

        if remaining_int <= max(1, limit_int // 10):
            logger.warning(
                "GitHub rate limit low: %s/%s remaining (reset at %s)",
                remaining,
                limit,
                reset,
            )

