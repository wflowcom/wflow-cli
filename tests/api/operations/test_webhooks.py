import json

from tests.helpers import mock_wflow
from wflow_api.models.admin import WebHookRegistration
from wflow_api.operations import webhooks


def test_a_webhook_registration_carries_its_target():
    hook = WebHookRegistration.model_validate(
        {"id": "wh-1", "webHookUri": "https://example.test/hook", "actions": ["DocumentCreated"]}
    )

    assert hook.webHookUri.startswith("https://")
    assert hook.actions == ["DocumentCreated"]


async def test_webhook_registrations_are_a_bare_list():
    client, requests = mock_wflow(
        {"/api/acme/webhookregistrations": [{"id": "wh-1", "webHookUri": "https://example.test/h"}]}
    )

    result = await webhooks.list_webhook_registrations(client, "acme")

    assert requests[0].url.path == "/api/acme/webhookregistrations"
    assert result[0].webHookUri == "https://example.test/h"


async def test_deleting_a_registration_hits_its_own_path():
    client, requests = mock_wflow({"/api/acme/webhookregistrations/wh-1": None})

    result = await webhooks.delete_webhook_registration(client, "acme", "wh-1")

    assert requests[0].method == "DELETE"
    assert requests[0].url.path == "/api/acme/webhookregistrations/wh-1"
    assert (result.action, result.resource) == ("deleted", "webhookregistrations")


async def test_a_registration_write_sends_its_own_payload():
    client, requests = mock_wflow({"/api/acme/webhookregistrations": "new-id"})

    result = await webhooks.update_webhook_registration(client, "acme", {"webHookUri": "https://erp.example/hook"})

    assert requests[0].method == "PUT"
    assert json.loads(requests[0].content) == {"webHookUri": "https://erp.example/hook"}
    assert (result.action, result.resource, result.id) == ("updated", "webhookregistrations", "new-id")


async def test_a_webhook_uri_with_its_own_query_string_reaches_wflow_verbatim():
    uri = "https://erp.example/hook?token=a%2Fb&mode=full"
    client, requests = mock_wflow({"/api/acme/webhookregistrations": "wh-9"})

    result = await webhooks.update_webhook_registration(
        client, "acme", {"webHookUri": uri, "actions": ["DocumentCreated"]}
    )

    assert json.loads(requests[0].content) == {"webHookUri": uri, "actions": ["DocumentCreated"]}
    assert not requests[0].url.query
    assert result.id == "wh-9"
