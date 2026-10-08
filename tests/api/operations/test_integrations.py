import inspect

from tests.helpers import mock_wflow
from wflow_api.models.requests import ApiClientResult
from wflow_api.operations import integrations


def test_the_api_client_result_carries_a_secret():
    result = ApiClientResult.model_validate({"id": "c-1", "secret": "s3cr3t"})

    assert result.secret == "s3cr3t"
    assert ApiClientResult.model_validate({"id": "c-1"}).model_dump() == {"id": "c-1", "secret": None}


async def test_allowing_the_integration_is_a_bodiless_put():
    client, requests = mock_wflow({"/api/acme/integrations/allow": None})

    result = await integrations.allow_integration(client, "acme")

    assert requests[0].method == "PUT"
    assert requests[0].url.path == "/api/acme/integrations/allow"
    assert not requests[0].content
    assert (result.action, result.resource) == ("allowed", "integrations/allow")


async def test_creating_an_api_client_returns_the_pair():
    client, requests = mock_wflow({"/api/acme/integrations/apiclient": {"id": "c-1", "secret": "s3cr3t"}})

    result = await integrations.create_api_client(client, "acme", "ERP sync", sufix="erp")

    assert requests[0].method == "POST"
    assert requests[0].url.params["name"] == "ERP sync"
    assert requests[0].url.params["sufix"] == "erp"
    assert "alwaysAllow" not in requests[0].url.params
    assert (result.id, result.secret) == ("c-1", "s3cr3t")


def test_the_docstring_warns_that_it_returns_a_secret():
    doc = inspect.getdoc(integrations.create_api_client) or ""

    assert "shown once" in doc, "the docstring no longer says the secret cannot be read again"
    assert "do not repeat" in doc, "the docstring no longer tells the reader to keep it out of a summary"
    assert "MCP" not in doc
