import inspect

import pytest
import typer
from typer.testing import CliRunner

from tests.helpers import mock_wflow
from wflow_api import WflowApiError, WflowError
from wflow_api.operations import operations
from wflow_cli.commands import _command, build_app, command_name, explain, option_name

runner = CliRunner()

DOWNLOADS = ("download-document-main-file", "download-document-file", "download-storage-file", "export-documents")


def test_names_follow_the_operation_mechanically():
    assert command_name("list_register_partners") == "list-register-partners"
    assert option_name("documentId") == "--document-id"
    assert option_name("pageSize") == "--page-size"
    assert option_name("organization") == "--organization"
    assert option_name("max_bytes") == "--max-bytes"


def test_every_operation_is_a_command():
    client, _ = mock_wflow({})
    app = build_app(lambda: client)

    registered = {command.name for command in app.registered_commands}

    assert registered == {command_name(fn.__name__) for _, fn in operations()}
    assert len(registered) == 173


@pytest.mark.parametrize(("module", "fn"), operations(), ids=lambda value: getattr(value, "__name__", value))
def test_every_command_has_working_help(module, fn):
    client, _ = mock_wflow({})

    shown = runner.invoke(build_app(lambda: client), [command_name(fn.__name__), "--help"])

    assert shown.exit_code == 0, shown.output
    if "organization" in inspect.signature(fn).parameters:
        assert "--organization" in shown.output


@pytest.mark.parametrize("command", DOWNLOADS)
def test_a_download_takes_a_size_limit_and_says_where_the_bytes_go(command):
    client, _ = mock_wflow({})

    shown = runner.invoke(build_app(lambda: client), [command, "--help"])

    assert shown.exit_code == 0, shown.output
    assert "--max-bytes" in shown.output and "sizeBytes" in shown.output


def test_a_negative_size_limit_is_a_usage_error():
    client, requests = mock_wflow({})

    refused = runner.invoke(
        build_app(lambda: client),
        ["download-storage-file", "-o", "acme", "--file-id", "f-1", "--output", "-", "--max-bytes", "-1"],
    )

    assert refused.exit_code == 2
    assert requests == []


def test_only_one_option_may_read_stdin():
    called = []

    async def two_bodies(client, first, second):
        called.append(1)

    run = _command(two_bodies, {"first": "json", "second": "json"}, lambda: None)

    with pytest.raises(typer.BadParameter) as refused:
        run(first="-", second="-")

    assert "--first" in str(refused.value) and "--second" in str(refused.value)
    assert called == []


def test_an_error_is_one_line_on_stderr(capsys):
    async def fails(client):
        raise WflowError("first line\nsecond line")

    run = _command(fails, {}, lambda: None)

    with pytest.raises(typer.Exit) as exited:
        run()

    assert exited.value.exit_code == 1
    printed = capsys.readouterr()
    assert printed.out == ""
    assert printed.err.splitlines() == ["first line; second line"]


def test_a_401_and_a_failed_token_request_point_at_the_credentials():
    for error in (
        WflowApiError("x", status=401, method="GET", path="/api/acme/x", detail=""),
        WflowApiError("x", status=400, method="POST", path="/connect/token", detail="invalid_client"),
    ):
        assert "WFLOW_CLIENT_ID" in explain(error)


def test_a_403_points_at_the_workspace_setting():
    assert "API accesses" in explain(WflowApiError("x", status=403, method="GET", path="/api/acme/x", detail=""))


def test_other_errors_are_left_alone():
    assert explain(WflowError("plain")) == "plain"
