from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

import httpx

from ghscope.auth.app import GITHUB_REST_URL, GitHubAuth
from ghscope.client.graphql import GitHubApiError

logger = logging.getLogger("ghscope.client.rest")


@dataclass
class GitHubRestClient:
    auth: GitHubAuth
    timeout: float = 30.0
    _client: httpx.Client = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._client = httpx.Client(
            base_url=GITHUB_REST_URL,
            headers=dict[str, str](self.auth.headers()),
            timeout=self.timeout,
        )

    def close(self) -> None:
        self._client.close()

    def get(self, path: str, params: Optional[Mapping[str, Any]] = None) -> Any:
        response = self._client.get(path, params=params)
        self._log_rate_limit(response.headers)

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise GitHubApiError(f"GitHub REST request failed: {exc}") from exc

        return response.json()

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
                "GitHub REST rate limit low: %s/%s remaining (reset at %s)",
                remaining,
                limit,
                reset,
            )
