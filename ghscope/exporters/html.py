from __future__ import annotations

from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ghscope.report.context import ReportContext


def _env(templates_dir: Path) -> Environment:
    return Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(enabled_extensions=("html", "xml")),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_html(context: ReportContext, templates_dir: Path, template_name: str) -> str:
    env = _env(templates_dir)
    template = env.get_template(template_name)
    return template.render(report=context)


def export_html(
    context: ReportContext,
    templates_dir: Path,
    output_path: Optional[Path],
    template_name: str = "report.html.j2",
) -> str:
    html = render_html(context, templates_dir, template_name)
    if output_path is not None:
        output_path.write_text(html, encoding="utf-8")
    return html

