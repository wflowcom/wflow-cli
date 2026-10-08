import io
import json
import os
import sys

import pytest
import typer

from wflow_api import FileContent
from wflow_api.models import WriteResult
from wflow_cli.io import check_output, print_json, read_json, save_download


def test_json_can_be_inline_a_file_or_stdin(tmp_path, monkeypatch):
    source = tmp_path / "partners.json"
    source.write_text('[{"name": "Účetní s.r.o."}]', encoding="utf-8")
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(b'{"a": 1}')))

    assert read_json('[{"name": "Acme"}]', "--partners") == [{"name": "Acme"}]
    assert read_json(f"@{source}", "--partners") == [{"name": "Účetní s.r.o."}]
    assert read_json("-", "--partners") == {"a": 1}


def test_a_missing_file_is_a_usage_error_naming_the_option(tmp_path):
    with pytest.raises(typer.BadParameter, match="cannot read") as refused:
        read_json(f"@{tmp_path / 'nope.json'}", "--partners")

    assert refused.value.param_hint == "--partners"


def test_invalid_json_says_where():
    with pytest.raises(typer.BadParameter, match="line 1 column") as refused:
        read_json("[{name: 1}]", "--partners")

    assert refused.value.param_hint == "--partners"


def test_text_that_is_not_utf8_is_a_usage_error(tmp_path, monkeypatch):
    latin1 = tmp_path / "partners.json"
    latin1.write_bytes('[{"name": "Ústí s.r.o."}]'.encode("latin-1"))
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(b'"\xda"')))

    for text in (f"@{latin1}", "-", '"\udcda"'):
        with pytest.raises(typer.BadParameter, match="not UTF-8") as refused:
            read_json(text, "--partners")
        assert refused.value.param_hint == "--partners"


def test_a_file_saved_as_utf16_with_a_bom_is_read(tmp_path):
    source = tmp_path / "partners.json"
    source.write_bytes('[{"name": "Účetní s.r.o."}]'.encode("utf-16"))

    assert read_json(f"@{source}", "--partners") == [{"name": "Účetní s.r.o."}]


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


def test_a_dangling_symlink_counts_as_an_existing_output(tmp_path):
    link = tmp_path / "a.pdf"
    link.symlink_to(tmp_path / "gone.pdf")

    with pytest.raises(typer.BadParameter, match="already exists"):
        check_output(str(link), force=False)


@pytest.mark.skipif(getattr(os, "geteuid", lambda: -1)() == 0, reason="root can write anywhere")
def test_an_output_that_cannot_be_written_is_refused_up_front(tmp_path):
    locked_dir = tmp_path / "locked"
    locked_dir.mkdir()
    read_only = tmp_path / "a.pdf"
    read_only.write_bytes(b"old")
    read_only.chmod(0o444)
    locked_dir.chmod(0o555)
    try:
        with pytest.raises(typer.BadParameter, match="cannot write"):
            check_output(str(locked_dir / "new.pdf"), force=False)
        with pytest.raises(typer.BadParameter, match="cannot write"):
            check_output(str(read_only), force=True)
    finally:
        locked_dir.chmod(0o755)


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


def test_a_download_that_cannot_be_written_is_a_usage_error(tmp_path):
    blocker = tmp_path / "a.pdf"
    blocker.write_bytes(b"old")

    with pytest.raises(typer.BadParameter, match="cannot write") as refused:
        save_download(FileContent(filename=None, content_type=None, content=b"%PDF"), str(blocker / "b.pdf"))

    assert refused.value.param_hint == "--output"


def test_a_download_to_stdout_is_the_raw_bytes(capsysbinary):
    save_download(FileContent(filename=None, content_type=None, content=b"\x00\xffPDF"), "-")

    assert capsysbinary.readouterr().out == b"\x00\xffPDF"
