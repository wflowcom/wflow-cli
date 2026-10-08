import httpx
import pytest

from tests.helpers import ACCOUNT_BODY, mock_response
from wflow_api.errors import WflowError
from wflow_api.guards import (
    current_account,
    ensure_list,
    filename_from_disposition,
    path_segment,
    problem_detail,
    query_params,
    write_body,
    write_definitions_json,
    write_json,
    write_json_list,
)
from wflow_api.models import PartnerFull, StorageFolderUpdate
from wflow_api.models.documents import Property


def test_query_params_drops_unset_arguments():
    assert query_params(search="acme", sort=None, page=0) == {"search": "acme", "page": 0}


def test_a_path_segment_is_encoded_without_disturbing_a_real_id():
    assert path_segment("3f2a9c7e-1b44-4e0a-9d21-6c5b8a0f7e13") == "3f2a9c7e-1b44-4e0a-9d21-6c5b8a0f7e13"
    assert path_segment("../d-1") == "..%2Fd-1"
    assert path_segment("a?b#c") == "a%3Fb%23c"


def test_a_segment_of_nothing_but_dots_is_refused_rather_than_encoded():
    for hostile in (".", "..", "..."):
        with pytest.raises(WflowError, match="run of dots"):
            path_segment(hostile)

    assert path_segment("..d-1") == "..d-1"


def test_an_empty_register_write_is_refused():
    with pytest.raises(WflowError, match="empty list") as refused:
        write_body([])

    assert "patch_register_" in str(refused.value)


def test_an_unknown_field_is_refused_by_its_indexed_path():
    partner = PartnerFull.model_validate({"name": "Acme", "mainAddress": {"streetAndNumber": "A 1", "stret": "typo"}})

    with pytest.raises(WflowError, match=r"\[0\]\.mainAddress\.stret"):
        write_body([partner])


def test_a_register_body_leaves_out_what_the_caller_did_not_set():
    assert write_body([PartnerFull.model_validate({"name": "Acme"})]) == [{"name": "Acme"}]


def test_a_single_record_body_is_checked_the_same_way():
    with pytest.raises(WflowError, match="Unknown field"):
        write_json(StorageFolderUpdate.model_validate({"name": "Invoices", "nmae": "typo"}))


def test_a_list_body_refuses_empty_unless_empty_is_the_point():
    with pytest.raises(WflowError, match="empty list"):
        write_json_list([])

    assert write_json_list([], allow_empty=True) == []


def test_a_definition_write_refuses_an_entry_without_name_and_type():
    with pytest.raises(WflowError, match=r"\[0\]") as refused:
        write_definitions_json([Property.model_validate({"value": 1})], values_operation="update_document_properties")

    assert "update_document_properties" in str(refused.value)


def test_no_refusal_talks_about_tools_or_mcp():
    refusals = []
    for call in (
        lambda: write_body([]),
        lambda: write_json_list([]),
        lambda: write_json(StorageFolderUpdate.model_validate({"nmae": "typo"})),
        lambda: path_segment(".."),
    ):
        with pytest.raises(WflowError) as refused:
            call()
        refusals.append(str(refused.value).lower())

    for text in refusals:
        assert "tool" not in text and "mcp" not in text and "schema" not in text, text


def test_a_bare_array_endpoint_answering_an_object_is_refused():
    with pytest.raises(WflowError, match="not an array"):
        ensure_list("/api/acme/documents/tags", {"items": ["a"]})

    assert ensure_list("/api/acme/documents/tags", ["a"]) == ["a"]


def test_a_problem_detail_is_summarised_and_html_degrades_to_nothing():
    assert problem_detail(httpx.Response(400, json={"title": "Bad", "detail": "id must be unique"})) == (
        " Bad — id must be unique"
    )
    assert problem_detail(httpx.Response(502, content=b"<html>bad gateway</html>")) == ""
    assert problem_detail(httpx.Response(500, json=["not", "a", "dict"])) == ""


def test_the_filename_is_read_the_way_the_rfcs_say():
    assert filename_from_disposition('attachment; filename="a;b.pdf"') == "a;b.pdf"
    assert filename_from_disposition("attachment; filename*=UTF-8''faktura-%C4%8D.pdf") == "faktura-č.pdf"
    assert filename_from_disposition("") is None


async def test_the_current_account_is_typed():
    client, sent = mock_response(200, json=ACCOUNT_BODY)

    account = await current_account(client, "acme")

    assert sent[0].url.path == "/api/acme/account"
    assert account.identity.login == "lukas@wflow.com"


async def test_a_workspace_without_the_caller_is_a_named_failure():
    client, _ = mock_response(200, content=b"null")

    with pytest.raises(WflowError, match="list_organizations"):
        await current_account(client, "acme")
