from __future__ import annotations

from click.testing import CliRunner

from ghscope.cli import cli


def test_cli_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "ghscope" in result.output

