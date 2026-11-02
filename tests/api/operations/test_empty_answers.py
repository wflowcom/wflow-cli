import inspect
import typing

import pytest

from tests.helpers import mock_response
from wflow_api.models.common import Paged
from wflow_api.operations import operations


def returns_a_collection(fn) -> bool:
    annotation = inspect.signature(fn).return_annotation
    metadata = getattr(annotation, "__pydantic_generic_metadata__", None) or {}
    return typing.get_origin(annotation) is list or metadata.get("origin") is Paged


COLLECTIONS = sorted((fn for _, fn in operations() if returns_a_collection(fn)), key=lambda fn: fn.__name__)


def minimal_arguments(fn) -> dict[str, str]:
    required = {
        parameter.name: parameter.annotation
        for parameter in inspect.signature(fn).parameters.values()
        if parameter.default is inspect.Parameter.empty and parameter.name != "client"
    }
    assert all(annotation is str or name == "organization" for name, annotation in required.items()), (
        f"{fn.__name__} needs more than ids"
    )
    return {name: "acme" if name == "organization" else "x" for name in required}


def test_the_collections_are_found():
    assert len(COLLECTIONS) > 40


@pytest.mark.parametrize("body", [b"", b"null"], ids=["no body", "json null"])
@pytest.mark.parametrize("fn", COLLECTIONS, ids=lambda fn: fn.__name__)
async def test_an_empty_answer_is_an_empty_collection(fn, body):
    client, requests = mock_response(200, content=body)

    result = await fn(client, **minimal_arguments(fn))

    assert len(requests) == 1
    assert (result if isinstance(result, list) else result.items) == []
