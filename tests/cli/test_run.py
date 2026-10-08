import json
import subprocess
import sys
from pathlib import Path

import httpx
from typer.testing import CliRunner

from tests.helpers import API_BASE, HEADERS, client_for, mock_download, mock_wflow
from wflow_api import WflowApiError, WflowClient
from wflow_cli import __version__
from wflow_cli.commands import build_app

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


PARTNERS = {
    "items": [{"id": "p-1", "name": "Účetní s.r.o.", "ic": "12345678", "isValid": True}],
    "totalItems": 1,
    "pageSize": 50,
    "page": 0,
}


def app_on(client):
    return build_app(lambda: client)


def test_a_read_prints_the_page_as_json():
    client, sent = mock_wflow({"/api/acme/registers/partners": PARTNERS})

    ran = runner.invoke(app_on(client), ["list-register-partners", "-o", "acme", "--page-size", "50"])

    assert ran.exit_code == 0, ran.output
    assert json.loads(ran.stdout)["items"][0]["id"] == "p-1"
    assert sent[0].url.params["pageSize"] == "50"


def test_non_ascii_text_is_printed_as_is():
    client, _ = mock_wflow({"/api/acme/registers/partners": PARTNERS})

    ran = runner.invoke(app_on(client), ["list-register-partners", "-o", "acme"])

    assert "Účetní s.r.o." in ran.stdout


BIG_PAGE = """
from tests.helpers import mock_wflow
from wflow_cli.commands import build_app
items = [{"id": str(i), "name": "Účetní s.r.o."} for i in range(20000)]
client, _ = mock_wflow({"/api/acme/registers/partners": {"items": items}})
build_app(lambda: client)(["list-register-partners", "-o", "acme"])
"""


def test_a_reader_that_stops_early_gets_no_traceback():
    piped = subprocess.Popen(
        [sys.executable, "-c", BIG_PAGE], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=Path(__file__).parents[2]
    )
    assert piped.stdout is not None and piped.stderr is not None

    assert piped.stdout.read(10) == b'{\n  "items'
    piped.stdout.close()
    piped.wait(timeout=60)

    assert piped.stderr.read() == b""


def test_the_organization_can_come_from_the_environment():
    client, sent = mock_wflow({"/api/acme/organization": {"name": "Acme"}})

    ran = runner.invoke(app_on(client), ["get-organization"], env={"WFLOW_ORGANIZATION": "acme"})

    assert ran.exit_code == 0, ran.output
    assert sent[0].url.path == "/api/acme/organization"


def test_a_hostile_organization_never_reaches_wflow():
    client, sent = mock_wflow({})

    ran = runner.invoke(app_on(client), ["get-organization", "-o", "../acme"])

    assert ran.exit_code == 1
    assert len(ran.stderr.strip().splitlines()) == 1
    assert "pattern" in ran.stderr
    assert sent == []


def test_a_write_takes_json_inline_from_a_file_and_from_stdin(tmp_path):
    body = [{"name": "Acme"}]
    source = tmp_path / "partners.json"
    source.write_text(json.dumps(body), encoding="utf-8")

    for arguments, stdin in (([json.dumps(body)], None), ([f"@{source}"], None), (["-"], json.dumps(body))):
        client, sent = mock_wflow({"/api/acme/registers/partners": None})
        ran = runner.invoke(
            app_on(client), ["update-register-partners", "-o", "acme", "--partners", *arguments], input=stdin
        )

        assert ran.exit_code == 0, ran.output
        assert sent[0].method == "PUT"
        assert json.loads(sent[0].content) == body
        assert json.loads(ran.stdout)["action"] == "updated"


def test_bad_json_is_a_usage_error_and_nothing_is_sent():
    client, sent = mock_wflow({})

    ran = runner.invoke(app_on(client), ["update-register-partners", "-o", "acme", "--partners", "[{name: 1}]"])

    assert ran.exit_code == 2
    assert "not valid JSON" in ran.output
    assert sent == []


def test_an_unknown_field_is_refused_by_the_library():
    client, sent = mock_wflow({})

    ran = runner.invoke(app_on(client), ["update-register-partners", "-o", "acme", "--partners", '[{"nmae": "Acme"}]'])

    assert ran.exit_code == 1
    assert "Unknown field" in ran.output
    assert sent == []


def test_an_upload_sends_the_file_under_its_own_name_unless_renamed(tmp_path):
    document = tmp_path / "faktura-č.pdf"
    document.write_bytes(b"%PDF-1.7")

    client, sent = mock_wflow({"/api/acme/documents/d-1/files/upload": "f-9"})
    ran = runner.invoke(
        app_on(client), ["upload-document-file", "-o", "acme", "--document-id", "d-1", "--file", str(document)]
    )

    assert ran.exit_code == 0, ran.output
    assert b"%PDF-1.7" in sent[0].content
    assert "faktura-" in sent[0].content.decode("utf-8", "replace")
    assert json.loads(ran.stdout)["id"] == "f-9"

    client, sent = mock_wflow({"/api/acme/documents/d-1/files/upload": "f-9"})
    runner.invoke(
        app_on(client),
        [
            "upload-document-file",
            "-o",
            "acme",
            "--document-id",
            "d-1",
            "--file",
            str(document),
            "--filename",
            "renamed.pdf",
        ],
    )
    assert b'filename="renamed.pdf"' in sent[0].content


def test_an_upload_sends_the_exact_bytes_under_the_base_name(tmp_path):
    payload = bytes(range(256)) + b"\r\n--boundary\r\n"
    document = tmp_path / "faktura-č.pdf"
    document.write_bytes(payload)

    client, sent = mock_wflow({"/api/acme/documents/d-1/files/upload": "f-9"})
    ran = runner.invoke(
        app_on(client), ["upload-document-file", "-o", "acme", "--document-id", "d-1", "--file", str(document)]
    )

    assert ran.exit_code == 0, ran.output
    body = sent[0].content
    boundary = sent[0].headers["content-type"].split("boundary=")[1].encode()
    head, _, rest = body.partition(b"\r\n\r\n")
    assert rest.removesuffix(b"\r\n--" + boundary + b"--\r\n") == payload
    assert 'filename="faktura-č.pdf"'.encode() in head
    assert str(tmp_path).encode() not in body


def test_an_upload_of_a_missing_file_is_a_usage_error(tmp_path):
    client, sent = mock_wflow({})

    ran = runner.invoke(
        app_on(client),
        ["upload-document-file", "-o", "acme", "--document-id", "d-1", "--file", str(tmp_path / "nope.pdf")],
    )

    assert ran.exit_code == 2
    assert sent == []


def test_a_download_is_written_to_the_named_file(tmp_path):
    client, sent = mock_download(b"%PDF-1.7", filename="invoice.pdf")
    target = tmp_path / "out.pdf"

    ran = runner.invoke(
        app_on(client), ["download-document-file", "-o", "acme", "--file-id", "f-1", "--output", str(target)]
    )

    assert ran.exit_code == 0, ran.output
    assert target.read_bytes() == b"%PDF-1.7"
    assert json.loads(ran.stdout)["sizeBytes"] == 8
    assert sent[0].url.path == "/api/acme/documents/files/f-1/download"


def test_a_download_to_stdout_is_the_raw_bytes():
    client, _ = mock_download(b"\x00\xffPDF")

    ran = runner.invoke(app_on(client), ["download-document-file", "-o", "acme", "--file-id", "f-1", "--output", "-"])

    assert ran.exit_code == 0
    assert ran.stdout_bytes == b"\x00\xffPDF"


def test_a_download_never_overwrites_without_force(tmp_path):
    target = tmp_path / "out.pdf"
    target.write_bytes(b"keep me")
    client, sent = mock_download(b"new")

    ran = runner.invoke(
        app_on(client), ["download-document-file", "-o", "acme", "--file-id", "f-1", "--output", str(target)]
    )

    assert ran.exit_code == 2
    assert "--force" in ran.output
    assert sent == []
    assert target.read_bytes() == b"keep me"


def test_a_403_says_where_to_allow_the_client():
    client, _ = mock_wflow({}, status=403)

    ran = runner.invoke(app_on(client), ["get-organization", "-o", "acme"])

    assert ran.exit_code == 1
    assert "403" in ran.output and "API accesses" in ran.output


def test_a_refused_token_points_at_the_credentials():
    async def refused() -> str:
        raise WflowApiError(
            "wflow account.wflow.com POST /connect/token returned 400 (invalid_client).",
            status=400,
            method="POST",
            path="/connect/token",
            detail="invalid_client",
        )

    client = WflowClient(
        refused, api_base=API_BASE, headers=HEADERS, transport=httpx.MockTransport(lambda request: httpx.Response(200))
    )

    ran = runner.invoke(app_on(client), ["get-organization", "-o", "acme"])

    assert ran.exit_code == 1
    assert "invalid_client" in ran.output and "WFLOW_CLIENT_SECRET" in ran.output


def test_an_unreachable_wflow_is_one_line_and_exit_1():
    def unreachable(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    ran = runner.invoke(app_on(client_for(unreachable)), ["get-organization", "-o", "acme"])

    assert ran.exit_code == 1
    assert len(ran.stderr.strip().splitlines()) == 1
    assert ran.stdout == ""
