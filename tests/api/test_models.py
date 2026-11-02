import json
from datetime import datetime

import pytest

from wflow_api.models import Account, WflowModel, WriteResult
from wflow_api.models.common import FileContent
from wflow_api.models.documents import DocumentBase


def test_unknown_fields_survive():
    """wflow adding a field must not mean the caller stops seeing it."""
    account = Account.model_validate({"id": "u-1", "somethingNew": "keep me"})

    assert account.model_dump()["somethingNew"] == "keep me"


def test_every_field_is_optional():
    """A missing field must not turn a working call into an opaque failure."""
    assert Account.model_validate({}).id is None


def test_write_result_names_what_happened():
    result = WriteResult(action="updated", resource="registers/partners")

    assert result.id is None
    assert result.model_dump()["action"] == "updated"


def test_write_result_carries_the_id_when_wflow_returns_one():
    result = WriteResult(action="created", resource="documents", id="4f9c")

    assert result.id == "4f9c"


def test_wflow_model_is_the_shared_base():
    assert issubclass(Account, WflowModel)


def test_an_offsetless_timestamp_parses_and_is_published_without_a_format():
    """wflow sends no UTC offset, and a schema demanding one costs the whole response."""
    document = DocumentBase.model_validate({"id": "d-1", "created": "2026-05-13T07:42:45.010"})

    assert document.created == datetime(2026, 5, 13, 7, 42, 45, 10_000)
    assert document.model_dump(mode="json")["created"] == "2026-05-13T07:42:45.010000"
    assert "date-time" not in json.dumps(DocumentBase.model_json_schema()["properties"]["created"])


@pytest.mark.parametrize("unset", ["0001-01-01T00:00:00", "0001-01-01T00:00:00Z"])
def test_dotnets_unset_date_is_published_as_null(unset):
    """`list_document_links` summaries carry .NET's DateTime default where wflow filled nothing in;
    a client must not read that as a real date in year one."""
    document = DocumentBase.model_validate({"id": "d-1", "created": unset, "updated": "2026-05-13T07:42:45.010"})

    assert document.created is None
    assert document.model_dump(mode="json")["created"] is None
    assert document.updated == datetime(2026, 5, 13, 7, 42, 45, 10_000)


def test_file_content_is_the_raw_bytes_and_what_wflow_said_about_them():
    file = FileContent(filename="faktura.pdf", content_type="application/pdf", content=b"%PDF")

    assert (file.filename, file.content_type, file.content) == ("faktura.pdf", "application/pdf", b"%PDF")


def test_the_mcp_only_types_are_not_part_of_the_library():
    from wflow_api import models

    for name in ("ArchiveFormat", "FileDownload", "Playbook", "PlaybookBase", "UploadId", "UploadTicket"):
        assert not hasattr(models, name), name
