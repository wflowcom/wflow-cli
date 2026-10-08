"""Integrations tag: minting an API client, and what one is allowed to do in a workspace."""

from typing import Annotated

from pydantic import Field

from wflow_api.client import WflowClient
from wflow_api.guards import query_params
from wflow_api.models import ApiClientResult, OrgSlug, WriteResult
from wflow_api.operation import operation


@operation
async def allow_integration(client: WflowClient, organization: OrgSlug) -> WriteResult:
    """Allow the calling client to integrate with this workspace.

    wflow applies it to the client the request is authenticated as: there is nothing to
    name, and it cannot grant access to a different one. `organization` is the only
    choice being made here, so check it is the workspace you mean.

    Fields: on the result —

    - `action` — "allowed"
    - `resource` — "integrations/allow"
    """
    await client.request("PUT", f"/api/{organization}/integrations/allow")
    return WriteResult(action="allowed", resource="integrations/allow")


@operation
async def create_api_client(
    client: WflowClient,
    organization: OrgSlug,
    name: str,
    sufix: Annotated[
        str | None, Field(default=None, description="Suffix appended to the generated client name")
    ] = None,
    alwaysAllow: Annotated[
        bool | None,
        Field(default=None, description="Create it already allowed, so it needs no allow_integration call"),
    ] = None,
) -> ApiClientResult:
    """Mint a machine-to-machine API client for this workspace.

    **The result contains a client secret, shown once and never again.** Hand it to the
    person who asked for it and do not repeat it in a summary, a commit message or a
    file. If it is lost, the client has to be created again.

    This is a `client_credentials` pair for a customer's own integration. It is not an
    `authorization_code` client for an interactive application — those have to be
    requested from the wflow identity administrators.

    Fields: on the result —

    - `id` — the generated client id
    - `secret` — the client secret, shown only here
    """
    payload = await client.request(
        "POST",
        f"/api/{organization}/integrations/apiclient",
        params=query_params(name=name, sufix=sufix, alwaysAllow=alwaysAllow),
    )
    return ApiClientResult.model_validate(payload or {})
