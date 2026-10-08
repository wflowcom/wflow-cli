import subprocess

from typer.testing import CliRunner

from wflow_cli import __version__

runner = CliRunner()


def test_the_console_script_prints_the_version():
    shown = subprocess.run(["wflow", "--version"], capture_output=True, text=True, check=False)

    assert shown.returncode == 0, shown.stderr
    assert shown.stdout.strip() == __version__


def test_missing_credentials_exit_2_with_the_reason():
    from wflow_cli.main import app

    ran = runner.invoke(
        app, ["get-organization", "-o", "acme"], env={"WFLOW_CLIENT_ID": None, "WFLOW_CLIENT_SECRET": None}
    )

    assert ran.exit_code == 2
    assert "WFLOW_CLIENT_ID" in ran.output
