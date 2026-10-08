"""WebHookRegistrations tag: the endpoints an integrator connects to."""

from wflow_api.client import WflowClient
from wflow_api.guards import path_segment, write_json
from wflow_api.models import OrgSlug, WebHookRegistration, WriteResult
from wflow_api.operation import operation


@operation
async def list_webhook_registrations(client: WflowClient, organization: OrgSlug) -> list[WebHookRegistration]:
    """Webhook registrations configured for this workspace.

    Fields:

    - `id`
    - `webHookUri` — the URL wflow calls
    - `description`
    - `actions` — one or more of: All, DocumentReadyToExtract, DocumentReadyToExport,
      DocumentUpdated, DocumentApprovalProcessFinished, RegisterUpdated, DocumentDeleted,
      DocumentReadyToReview, DocumentCreated, DocumentReviewed
    """
    payload = await client.request("GET", f"/api/{organization}/webhookregistrations") or []
    return [WebHookRegistration.model_validate(item) for item in payload]


@operation
async def delete_webhook_registration(client: WflowClient, organization: OrgSlug, registrationId: str) -> WriteResult:
    """Delete one webhook registration, so wflow stops calling that endpoint.

    Whatever is on the far end of `webHookUri` goes silent for the `actions` this
    registration covered, with no notice to it. Get the id from
    `list_webhook_registrations`.

    Fields: on the result —

    - `action` — "deleted"
    - `resource` — "webhookregistrations"
    """
    await client.request("DELETE", f"/api/{organization}/webhookregistrations/{path_segment(registrationId)}")
    return WriteResult(action="deleted", resource="webhookregistrations")


@operation
async def update_webhook_registration(
    client: WflowClient, organization: OrgSlug, registration: WebHookRegistration
) -> WriteResult:
    """Register a URL for wflow to call, or replace an existing registration.

    Matched by the `id` inside `registration`; omit it to create. `actions` is a whole
    set — an action you omit stops being delivered, with no notice to whatever is on the
    far end of `webHookUri` — and send `webHookUri` and `description` with it: whether a
    field you omit is kept or cleared is not guaranteed, so send the whole registration.
    `list_webhook_registrations` returns every registration with its actions; read it
    first when changing one that exists.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "webhookregistrations"
    - `id` — the registration's id
    """
    created = await client.request(
        "PUT",
        f"/api/{organization}/webhookregistrations",
        json=write_json(registration),
    )
    return WriteResult(action="updated", resource="webhookregistrations", id=created)
