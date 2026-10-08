import importlib
import inspect
from typing import Annotated

import pytest
from pydantic import Field

from tests.helpers import mock_wflow
from wflow_api.client import WflowClient
from wflow_api.errors import WflowError
from wflow_api.models import OrgSlug, PartnerFull
from wflow_api.operation import operation


@operation
async def sample(
    client: WflowClient,
    organization: OrgSlug,
    partners: list[PartnerFull],
    page: Annotated[int | None, Field(default=None, description="Page number, zero-based")] = None,
) -> int:
    """A sample operation."""
    await client.request("GET", f"/api/{organization}/x")
    return len(partners)


def test_the_wrapper_is_still_a_coroutine_function_with_the_real_signature():
    assert inspect.iscoroutinefunction(sample)
    assert list(inspect.signature(sample).parameters) == ["client", "organization", "partners", "page"]
    assert sample.__name__ == "sample" and sample.__doc__ == "A sample operation."
    assert inspect.unwrap(sample) is not sample


async def test_a_valid_call_runs_and_dicts_become_models():
    client, sent = mock_wflow({"/api/acme/x": {}})

    assert await sample(client, "acme", [{"name": "Acme"}]) == 1
    assert sent[0].url.path == "/api/acme/x"


@pytest.mark.parametrize("hostile", ["../acme", "acme/x", "acme?x", ""])
async def test_an_organization_with_a_delimiter_never_reaches_the_wire(hostile):
    client, sent = mock_wflow({})

    with pytest.raises(WflowError, match="sample") as refused:
        await sample(client, hostile, [])

    assert "organization" in str(refused.value)
    assert sent == []


async def test_a_wrong_type_is_a_wflow_error_not_a_pydantic_one():
    client, _ = mock_wflow({})

    with pytest.raises(WflowError, match="page"):
        await sample(client, "acme", [], page="first")


async def test_the_client_must_be_a_client():
    with pytest.raises(WflowError, match="client"):
        await sample("not a client", "acme", [])


async def test_a_call_that_does_not_bind_is_a_wflow_error():
    client, sent = mock_wflow({})

    with pytest.raises(WflowError, match="sample"):
        await sample(client, "acme", [], nonsense=1)

    assert sent == []


async def test_the_validator_is_built_on_first_call_not_at_import(monkeypatch):
    module = importlib.import_module("wflow_api.operation")

    built = []
    real = module.validate_call
    monkeypatch.setattr(module, "validate_call", lambda *args, **kwargs: built.append(args) or real(*args, **kwargs))

    @module.operation
    async def lazy(client: WflowClient) -> None:
        """Lazy."""

    assert built == []
    client, _ = mock_wflow({})
    await lazy(client)
    await lazy(client)
    assert len(built) == 1
