import inspect
import json
import re

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


async def test_several_files_go_as_uploaded_files_parts_in_order():
    client, requests = mock_wflow({"/api/acme/documents/withfiles": {"documentId": "d-9", "newOrganization": None}})

    result = await documents.create_document_with_files(
        client,
        organization="acme",
        files=[("invoice.pdf", b"%PDF-main"), ("annex.pdf", b"%PDF-annex")],
        typeId="t-1",
        invoiceType="TaxInvoice",
    )

    sent = requests[0]
    body = sent.content
    assert sent.method == "POST"
    assert body.count(b'name="uploadedFiles"') == 2
    assert body.index(b'filename="invoice.pdf"') < body.index(b'filename="annex.pdf"')
    assert body.index(b"%PDF-main") < body.index(b"%PDF-annex")
    assert sent.url.params["typeId"] == "t-1"
    assert sent.url.params["invoiceType"] == "TaxInvoice"
    assert (result.documentId, result.newOrganization) == ("d-9", None)


async def test_a_document_moved_to_another_workspace_names_it():
    client, _ = mock_wflow({"/api/acme/documents/withfiles": {"documentId": "d-9", "newOrganization": "acme-sk"}})

    result = await documents.create_document_with_files(
        client, organization="acme", files=[("invoice.pdf", b"%PDF")], typeId="t-1"
    )

    assert (result.documentId, result.newOrganization) == ("d-9", "acme-sk")


async def test_a_document_from_a_zero_byte_file_is_sent_as_wflow_would_receive_any_other():
    client, requests = mock_wflow({"/api/acme/documents/withfiles": {"documentId": "d-9"}})

    result = await documents.create_document_with_files(
        client, organization="acme", files=[("blank.pdf", b"")], typeId="t-1"
    )

    assert len(requests) == 1
    assert b'name="uploadedFiles"; filename="blank.pdf"' in requests[0].content
    assert result.documentId == "d-9"


async def test_an_empty_answer_is_a_result_with_nothing_set():
    client, _ = mock_wflow({"/api/acme/documents/withfiles": None})

    result = await documents.create_document_with_files(
        client, organization="acme", files=[("a.pdf", b"%PDF")], typeId="t-1"
    )

    assert (result.documentId, result.newOrganization) == (None, None)


def test_the_multi_file_description_states_what_wflow_reads_and_when_it_generates_a_pdf():
    doc = " ".join(inspect.getdoc(documents.create_document_with_files).split())
    invoice_type = inspect.signature(documents.create_document_with_files).parameters["invoiceType"]
    hint = " ".join(invoice_type.annotation.__metadata__[0].description.split())

    assert "reads only the first file of each kind (PDF, XML, ISDOC, ISDOCX)" in doc
    assert "the QR receipt on a Slovak cash slip only from the first file" in doc
    assert "only for an invoice document type, only when the workspace has that turned on" in doc
    assert "not when the e-invoice already embeds a PDF" in doc
    assert "among any of the files" not in doc
    assert hint.endswith("omitted means TaxInvoice")


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


async def test_an_export_without_the_new_arguments_sends_no_query_parameters():
    client, requests = mock_download(b"x")

    await documents.export_documents(client, organization="acme", format="excel", filter={"sort": "number asc"})

    assert not requests[0].url.params


async def test_an_export_forwards_mark_as_exported_and_parameters_verbatim():
    client, requests = mock_download(b"x")

    await documents.export_documents(
        client,
        organization="acme",
        format="kros",
        filter={"sort": "number asc"},
        markAsExported=True,
        parameters='{"cashSlipType": "pd", "incomingInvoiceTarget": "inv"}',
    )

    assert requests[0].url.params["markAsExported"] == "true"
    assert requests[0].url.params["parameters"] == '{"cashSlipType": "pd", "incomingInvoiceTarget": "inv"}'


def test_the_export_description_states_what_marking_and_parameters_do():
    doc = " ".join(inspect.getdoc(documents.export_documents).split())

    assert "the document is locked" in doc
    assert "skipped silently" in doc
    assert "required for kros" in doc
    assert "definition ids are not available through this API" in doc
    assert "Other formats ignore it" in doc
    assert "`sequence` applies only to documents with no series of their own" in doc
    assert '`{"cashSlipKind": "ProdejkaPrijata"|"PokladniDoklad"|"ZavazkovyDoklad"}`' in doc
    assert "`sequence` is accepted but has no effect" in doc


@pytest.mark.parametrize(
    "type_id,problem",
    [
        ({}, "missing a required argument: 'typeId'"),
        ({"typeId": ""}, "typeId: String should have at least 1 character"),
    ],
)
async def test_a_missing_or_empty_type_is_refused_before_any_request(type_id, problem):
    client, requests = mock_wflow({"/api/acme/documents/withfiles": None})

    with pytest.raises(WflowError, match=rf"^create_document_with_files: invalid arguments\. {re.escape(problem)}"):
        await documents.create_document_with_files(client, organization="acme", files=[("a.pdf", b"%PDF")], **type_id)

    assert requests == []


@pytest.mark.parametrize("files,problem", [([], "files"), ([("a.pdf", "text")], "files.0.1")])
async def test_no_files_or_text_instead_of_bytes_sends_nothing(files, problem):
    client, requests = mock_wflow({"/api/acme/documents/withfiles": None})

    with pytest.raises(WflowError, match=rf"^create_document_with_files: invalid arguments\. {re.escape(problem)}: "):
        await documents.create_document_with_files(client, organization="acme", files=files, typeId="t-1")

    assert requests == []
