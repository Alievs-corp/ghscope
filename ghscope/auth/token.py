from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable, Optional


DEFAULT_ENV_VARS: tuple[str, ...] = (
    "GH_FINE_GRAINED_TOKEN",
    "GITHUB_TOKEN",
    "GH_TOKEN",
)


class TokenError(RuntimeError):
    """Raised when a GitHub token cannot be resolved or is invalid."""


@dataclass(frozen=True)
class TokenConfig:
    explicit_token: Optional[str] = None
    env_vars: Iterable[str] = DEFAULT_ENV_VARS


def resolve_token(config: TokenConfig) -> str:
    """Resolve a GitHub personal access token from config or environment."""
    if config.explicit_token:
        return config.explicit_token

    for env_name in config.env_vars:
        value = os.getenv(env_name)
        if value:
            return value

    raise TokenError(
        "GitHub token not provided. Set one of "
        f"{', '.join(config.env_vars)} or pass an explicit token.",
    )

