import inspect
import re
import typing

import pytest

from tests.helpers import body_source
from wflow_api.client import WflowClient
from wflow_api.models.common import FileContent, Paged, WflowModel, WriteResult
from wflow_api.operations import operations

SCALAR_RETURNS = {
    "list_document_tags": "wflow returns a bare array of tag strings",
    "get_document_tags": "wflow returns a bare array of tag strings",
    "list_documents_to_export": "wflow returns a bare array of document ids",
    "list_documents_to_extract": "wflow returns a bare array of document ids",
    "get_document_metadata": "the spec documents neither a response schema nor a request body",
}
ENTITY_RETURNS = {
    "export_documents": "the export is a file, and FileContent is the one shape every file here has",
    "create_api_client": "the client secret is shown once, and WriteResult has nowhere to carry it",
}
NAME_PREFIXES = (
    "list_",
    "get_",
    "update_",
    "patch_",
    "create_",
    "delete_",
    "set_",
    "add_",
    "upload_",
    "download_",
    "export_",
    "lock_",
    "move_",
    "rename_",
    "restore_",
    "stamp_",
    "link_",
    "unlink_",
    "allow_",
)
READ_PREFIXES = ("list_", "get_", "download_")
WRITE_PREFIXES = tuple(prefix for prefix in NAME_PREFIXES if prefix not in READ_PREFIXES)
MCP_ONLY = (
    "uploadId",
    "downloadUrl",
    "zipPassword",
    "create_file_upload_url",
    "get_download_archive_format",
    "MCP",
    "Reconnect",
    "this tool",
)
MCP_TERMS = re.compile(r"\btools?\b|MCP|reconnect|input schema", re.IGNORECASE)


@pytest.fixture
def ops() -> dict:
    return {fn.__name__: fn for _, fn in operations()}


def is_typed_return(annotation) -> bool:
    if annotation in (WriteResult, FileContent):
        return True
    if typing.get_origin(annotation) is list:
        (inner,) = typing.get_args(annotation)
        return is_typed_return(inner)
    return isinstance(annotation, type) and issubclass(annotation, WflowModel)


def descriptions(annotation) -> str:
    return " ".join(getattr(meta, "description", None) or "" for meta in getattr(annotation, "__metadata__", ()))


def test_there_is_at_least_one_operation(ops):
    assert ops


def test_every_operation_is_a_validated_coroutine(ops):
    for name, fn in ops.items():
        assert inspect.iscoroutinefunction(fn), f"{name} is not async"
        assert inspect.unwrap(fn) is not fn, f"{name} is not wrapped by @operation"


def test_every_operation_takes_the_client_first(ops):
    for name, fn in ops.items():
        first = next(iter(inspect.signature(fn).parameters.values()))
        assert first.name == "client", f"{name} takes {first.name} first"
        assert first.annotation is WflowClient, f"{name} annotates client as {first.annotation!r}"


def test_every_operation_returns_a_typed_outcome(ops):
    for name, fn in ops.items():
        annotation = inspect.signature(fn).return_annotation
        assert annotation is not inspect.Signature.empty, f"{name} has no return annotation"
        if name in SCALAR_RETURNS:
            continue
        assert is_typed_return(annotation), f"{name} returns {annotation!r}, which is not a wflow model"


def test_every_operation_has_a_description(ops):
    for name, fn in ops.items():
        assert len(inspect.getdoc(fn) or "") > 40, f"{name} has no usable description"


def test_every_operation_documents_its_fields(ops):
    for name, fn in ops.items():
        assert "Fields:" in (inspect.getdoc(fn) or ""), f"{name} does not document its return fields"


def test_no_operation_docstring_mentions_mcp_only_things(ops):
    for name, fn in ops.items():
        doc = inspect.getdoc(fn) or ""
        for word in MCP_ONLY:
            assert word not in doc, f"{name}'s docstring mentions {word!r}"
        assert not MCP_TERMS.search(doc), f"{name}'s docstring mentions {MCP_TERMS.search(doc)[0]!r}"


def test_no_operation_parameter_description_mentions_mcp_only_things(ops):
    for name, fn in ops.items():
        for parameter in inspect.signature(fn).parameters.values():
            found = MCP_TERMS.search(descriptions(parameter.annotation))
            assert not found, f"{name}'s `{parameter.name}` description mentions {found and found[0]!r}"


def test_every_paged_operation_validates_the_model_its_annotation_declares(ops):
    for name, fn in sorted(ops.items()):
        metadata = getattr(inspect.signature(fn).return_annotation, "__pydantic_generic_metadata__", None)
        if not metadata or metadata.get("origin") is not Paged:
            continue
        (returned,) = metadata["args"]
        (model,) = re.findall(r"Paged\[(\w+)\]", body_source(fn))
        assert inspect.unwrap(fn).__globals__[model] is returned, (
            f"{name} returns Paged[{returned.__name__}] but validates {model}"
        )


def test_every_operation_name_follows_the_rule(ops):
    for name in ops:
        assert name.startswith(NAME_PREFIXES), f"{name} does not start with a known verb"
        assert name == name.lower(), f"{name} is not snake_case"


def test_every_operation_taking_an_organization_requires_it(ops):
    for name, fn in ops.items():
        parameter = inspect.signature(fn).parameters.get("organization")
        if parameter is not None:
            assert parameter.default is inspect.Parameter.empty, f"{name} lets organization default"


def test_every_write_returns_a_write_result(ops):
    for name, fn in ops.items():
        if not name.startswith(WRITE_PREFIXES) or name in SCALAR_RETURNS or name in ENTITY_RETURNS:
            continue
        assert inspect.signature(fn).return_annotation is WriteResult, f"{name} does not return WriteResult"


def described(fn, parameter: str) -> str:
    return descriptions(typing.get_type_hints(inspect.unwrap(fn), include_extras=True)[parameter])


def test_every_filterable_operation_carries_the_query_syntax(ops):
    filterable = {name: fn for name, fn in ops.items() if "query" in inspect.signature(fn).parameters}

    assert len(filterable) > 20, "the filterable operations should be most of the list operations"
    for name, fn in filterable.items():
        for rule in ("!=", ">=", "space", "and"):
            assert rule in described(fn, "query"), f"{name} does not document {rule!r} on `query`"
