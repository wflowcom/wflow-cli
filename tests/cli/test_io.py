import io
import json
import sys

import pytest
import typer

from wflow_api import FileContent
from wflow_api.models import WriteResult
from wflow_cli.io import check_output, print_json, read_json, save_download


def test_json_can_be_inline_a_file_or_stdin(tmp_path, monkeypatch):
    source = tmp_path / "partners.json"
    source.write_text('[{"name": "Účetní s.r.o."}]', encoding="utf-8")
    monkeypatch.setattr(sys, "stdin", io.StringIO('{"a": 1}'))

    assert read_json('[{"name": "Acme"}]', "--partners") == [{"name": "Acme"}]
    assert read_json(f"@{source}", "--partners") == [{"name": "Účetní s.r.o."}]
    assert read_json("-", "--partners") == {"a": 1}


def test_a_missing_file_is_a_usage_error_naming_the_option(tmp_path):
    with pytest.raises(typer.BadParameter, match="cannot read") as refused:
        read_json(f"@{tmp_path / 'nope.json'}", "--partners")

    assert refused.value.param_hint == "--partners"


def test_invalid_json_says_where(tmp_path):
    with pytest.raises(typer.BadParameter, match="line 1 column"):
        read_json("[{name: 1}]", "--partners")


def test_results_print_as_indented_json_with_text_as_is(capsys):
    print_json(WriteResult(action="updated", resource="registers/partners"))
    print_json({"name": "Účetní s.r.o."})

    out = capsys.readouterr().out
    assert '"action": "updated"' in out
    assert "Účetní s.r.o." in out


def test_an_output_path_is_checked_before_anything_is_fetched(tmp_path):
    existing = tmp_path / "a.pdf"
    existing.write_bytes(b"old")

    check_output("-", force=False)
    check_output(str(tmp_path / "new.pdf"), force=False)
    check_output(str(existing), force=True)
    for bad in (str(existing), str(tmp_path), str(tmp_path / "missing-dir" / "a.pdf")):
        with pytest.raises(typer.BadParameter):
            check_output(bad, force=False)


def test_a_download_is_written_and_described(tmp_path, capsys):
    target = tmp_path / "faktura.pdf"

    save_download(FileContent(filename="faktura.pdf", content_type="application/pdf", content=b"%PDF"), str(target))

    assert target.read_bytes() == b"%PDF"
    assert json.loads(capsys.readouterr().out) == {
        "filename": "faktura.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 4,
        "path": str(target),
    }


def test_a_download_to_stdout_is_the_raw_bytes(capsysbinary):
    save_download(FileContent(filename=None, content_type=None, content=b"\x00\xffPDF"), "-")

    assert capsysbinary.readouterr().out == b"\x00\xffPDF"
