from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path
from typing import Optional

from ghscope.report.context import ReportContext


def export_csv(context: ReportContext, output_path: Optional[Path]) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "login",
            "commits",
            "lines_added",
            "lines_deleted",
            "pull_requests_opened",
            "pull_requests_merged",
            "issues_opened",
            "issues_closed",
            "issues_assigned",
            "reviews_given",
            "reviews_received",
        ],
    )
    for summary in context.activity.users.values():
        writer.writerow(
            [
                summary.login,
                summary.commits,
                summary.lines_added,
                summary.lines_deleted,
                summary.pull_requests_opened,
                summary.pull_requests_merged,
                summary.issues_opened,
                summary.issues_closed,
                summary.issues_assigned,
                summary.reviews_given,
                summary.reviews_received,
            ],
        )

    text = buffer.getvalue()
    if output_path is not None:
        output_path.write_text(text, encoding="utf-8")
    return text

