from __future__ import annotations

import logging
from typing import Optional

import click

from . import __version__

logger = logging.getLogger("ghscope")


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


@click.group()
@click.version_option(version=__version__, prog_name="ghscope")
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="Enable verbose logging output.",
)
def cli(verbose: bool) -> None:
    """Command-line interface for ghscope."""
    _configure_logging(verbose)


@cli.command()
@click.option(
    "--org",
    "org",
    type=str,
    required=False,
    help="GitHub organization to report on.",
)
@click.option(
    "--user",
    "user",
    type=str,
    required=False,
    help="GitHub user account to report on.",
)
@click.option(
    "--since",
    "since",
    type=str,
    required=True,
    help="Start date (YYYY-MM-DD) for the reporting window.",
)
@click.option(
    "--until",
    "until",
    type=str,
    required=True,
    help="End date (YYYY-MM-DD) for the reporting window.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["md", "html", "pdf", "json", "csv"], case_sensitive=False),
    default="md",
    show_default=True,
    help="Output format for the report.",
)
@click.option(
    "--output",
    "output_path",
    type=str,
    required=False,
    help="Path to the output file or directory.",
)
@click.option(
    "--token",
    "token",
    type=str,
    required=False,
    envvar=["GH_FINE_GRAINED_TOKEN", "GITHUB_TOKEN", "GH_TOKEN"],
    help="GitHub fine-grained personal access token.",
)
def report(
    org: Optional[str],
    user: Optional[str],
    since: str,
    until: str,
    output_format: str,
    output_path: Optional[str],
    token: Optional[str],
) -> None:
    """Generate a GitHub activity report."""
    if not org and not user:
        raise click.UsageError("You must provide either --org or --user.")

    logger.info(
        "ghscope report requested",
        extra={
            "org": org,
            "user": user,
            "since": since,
            "until": until,
            "format": output_format,
            "output": output_path,
        },
    )

    from .report.builder import ReportBuilder

    builder = ReportBuilder(
        org=org,
        user=user,
        since=since,
        until=until,
        token=token,
    )
    builder.build_and_export(format_name=output_format, output_path=output_path)


def main() -> None:
    cli(standalone_mode=True)


if __name__ == "__main__":
    main()

