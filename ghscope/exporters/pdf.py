from __future__ import annotations

from pathlib import Path

from weasyprint import HTML  # type: ignore[import-untyped]

from ghscope.exporters.html import render_html
from ghscope.report.context import ReportContext


def export_pdf(
    context: ReportContext,
    templates_dir: Path,
    output_path: Path,
    template_name: str = "report.html.j2",
) -> None:
    html = render_html(context, templates_dir, template_name)
    HTML(string=html).write_pdf(str(output_path))
