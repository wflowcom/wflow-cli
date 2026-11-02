import json

import pytest

from tests.helpers import mock_download, mock_response, mock_wflow
from wflow_api.errors import WflowApiError, WflowError
from wflow_api.models.requests import StructuredFilter
from wflow_api.operations import documents


def test_a_structured_filter_is_accepted():
    view = StructuredFilter.model_validate(
        {"search": "invoice", "filters": [{"column": "number", "filters": [{"operator": "CO", "value": "2026"}]}]}
    )

    assert view.search == "invoice"
    assert view.filters[0].filters[0].operator == "CO"
    assert view.model_dump(exclude_none=True) == {
        "search": "invoice",
        "filters": [{"column": "number", "filters": [{"operator": "CO", "value": "2026"}]}],
    }


async def test_creating_a_document_with_files_uses_the_part_name_the_spec_declares():
    client, requests = mock_wflow({"/api/acme/documents/withfiles": None})

    result = await documents.create_document_with_files(
        client, organization="acme", filename="invoice.pdf", content=b"%PDF-1.7", typeId="t-1", invoiceType="TaxInvoice"
    )

    sent = requests[0]
    assert sent.method == "POST"
    assert b'name="uploadedFiles"; filename="invoice.pdf"' in sent.content
    assert b"%PDF-1.7" in sent.content
    assert sent.url.params["typeId"] == "t-1"
    assert sent.url.params["invoiceType"] == "TaxInvoice"
    assert (result.action, result.resource, result.id) == ("created", "documents/withfiles", None)


async def test_a_document_from_a_zero_byte_file_is_sent_as_wflow_would_receive_any_other():
    client, requests = mock_wflow({"/api/acme/documents/withfiles": None})

    result = await documents.create_document_with_files(client, organization="acme", filename="blank.pdf", content=b"")

    assert len(requests) == 1
    assert b'name="uploadedFiles"; filename="blank.pdf"' in requests[0].content
    assert (result.action, result.resource, result.id) == ("created", "documents/withfiles", None)


async def test_an_export_streams_back_as_the_files_own_bytes():
    body = b"<?xml version='1.0'?><invoices/>"
    client, requests = mock_download(body, content_type="application/xml", filename=None)

    result = await documents.export_documents(client, organization="acme", format="isdoc", filter={"search": "2026"})

    assert requests[0].method == "POST"
    assert requests[0].url.path == "/api/acme/documents/export/isdoc"
    assert json.loads(requests[0].content) == {"search": "2026", "filters": [], "propertyFilters": []}
    assert (result.content, result.content_type, result.filename) == (body, "application/xml", None)


async def test_an_empty_export_filter_is_still_sent():
    client, requests = mock_download(b"x")

    await documents.export_documents(client, organization="acme", format="excel", filter={})

    assert json.loads(requests[0].content) == {"search": "", "filters": [], "propertyFilters": []}


async def test_an_export_filter_holding_only_sort_sends_the_restrictions_empty():
    client, requests = mock_download(b"x")

    await documents.export_documents(client, organization="acme", format="excel", filter={"sort": "number asc"})

    assert json.loads(requests[0].content) == {"sort": "number asc", "search": "", "filters": [], "propertyFilters": []}


async def test_an_export_filter_keeps_the_restrictions_it_names():
    client, requests = mock_download(b"x")
    view = {"sort": "number asc", "filters": [{"column": "number", "filters": [{"operator": "CO", "value": "2026"}]}]}

    await documents.export_documents(client, organization="acme", format="excel", filter=view)

    assert json.loads(requests[0].content) == {**view, "search": "", "propertyFilters": []}


async def test_a_misspelt_export_filter_field_is_refused():
    client, requests = mock_download(b"x")

    with pytest.raises(WflowError, match="serach"):
        await documents.export_documents(client, organization="acme", format="isdoc", filter={"serach": "2026"})

    assert requests == []


async def test_an_export_wflow_fails_is_an_api_error_naming_the_status_and_path():
    client, _ = mock_response(500, json={"title": "Value cannot be null"})

    with pytest.raises(WflowApiError, match="/api/acme/documents/export/excel returned 500") as failed:
        await documents.export_documents(client, organization="acme", format="excel", filter={})

    assert failed.value.status == 500


async def test_an_export_over_the_limit_is_refused():
    client, _ = mock_download(b"x" * 33)

    with pytest.raises(WflowError, match="is 33 bytes, over the 32-byte limit"):
        await documents.export_documents(
            client, organization="acme", format="excel", filter={"sort": "number asc"}, max_bytes=32
        )


async def test_a_document_from_text_instead_of_bytes_sends_nothing():
    client, requests = mock_wflow({"/api/acme/documents/withfiles": None})

    with pytest.raises(WflowError, match=r"^create_document_with_files: invalid arguments\. content: "):
        await documents.create_document_with_files(client, organization="acme", filename="a.pdf", content="a.pdf")

    assert requests == []
