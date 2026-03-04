from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from ghscope.report.context import ReportContext


def _model_to_dict(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    if hasattr(model, "__dict__"):
        return dict(model.__dict__)
    return dict(model)


def export_json(context: ReportContext, output_path: Optional[Path]) -> str:
    payload: dict[str, Any] = {
        "activity": {
            "users": {
                login: _model_to_dict(summary)
                for login, summary in context.activity.users.items()
            },
            "repositories": {
                name: _model_to_dict(summary)
                for name, summary in context.activity.repositories.items()
            },
            "active_contributors": context.activity.active_contributors,
            "inactive_contributors": context.activity.inactive_contributors,
        },
        "timelines": [
            {
                "day": bucket.day.isoformat(),
                "commits": bucket.commits,
                "pull_requests": bucket.pull_requests,
                "issues": bucket.issues,
            }
            for bucket in context.timelines.by_day
        ],
        "scope": {
            "org": context.org,
            "user": context.user,
            "since": context.since.isoformat(),
            "until": context.until.isoformat(),
        },
        "entities": {
            "users": [_model_to_dict(user) for user in context.users],
            "repositories": [
                _model_to_dict(repo) for repo in context.repositories
            ],
            "commits": [_model_to_dict(commit) for commit in context.commits],
            "pull_requests": [
                _model_to_dict(pr) for pr in context.pull_requests
            ],
            "issues": [_model_to_dict(issue) for issue in context.issues],
        },
    }
    text = json.dumps(payload, indent=2, sort_keys=True)
    if output_path is not None:
        output_path.write_text(text, encoding="utf-8")
    return text

