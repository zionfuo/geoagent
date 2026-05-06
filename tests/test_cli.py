import pytest
from click.testing import CliRunner

def test_cli_help():
    from geoagent.cli import cli

    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert "transform" in result.output

def test_cli_transform_command_exists():
    from geoagent.cli import cli

    runner = CliRunner()
    result = runner.invoke(cli, ['transform', '--help'])
    assert result.exit_code == 0