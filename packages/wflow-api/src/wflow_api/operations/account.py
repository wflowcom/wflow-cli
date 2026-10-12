"""Account: who the caller is, and which workspaces they can reach."""

from wflow_api.client import WflowClient
from wflow_api.guards import current_account, ensure_list
from wflow_api.models import Account, OrganizationDomain, OrgSlug
from wflow_api.operation import operation


@operation
async def get_me(client: WflowClient, organization: OrgSlug) -> Account:
    """Return the profile of the currently authenticated user in one organization.

    Fields:

    - `id` — the user's identifier in this organization
    - `identity` — login, first/last/full name, and ISO 639-1 language
    - `created` — when the account was created
    - `hasFullAccess` — full-access role indicator, which overrides the detail below
    - `roles` — role memberships (id, name, description)
    - `teams` — team memberships; `system` marks a built-in team
    - `documentTypes` — per document type access: the type (with its `kind`) and
      whether the user sees All, OnlyAssigned or FullAccess
    - `rights` — named rights held here, e.g. CanApprove, CanCreateDocument
    """
    return await current_account(client, organization)


@operation
async def list_organizations(client: WflowClient) -> list[OrganizationDomain]:
    """List the wflow organizations the signed-in user can access.

    One entry per organization workspace:

    Fields:

    - `subdomain` — the workspace slug, e.g. "nonameorg". This is the value to pass
      as the `organization` argument of other operations.
    - `name` — display name, e.g. "Noname Ltd."
    - `baseURL` — workspace host, e.g. "nonameorg.wflow.com"
    - `trialExpiration` — trial end date, or null when not on a trial

    Takes no arguments — start here when you do not know which workspace the user means.
    """
    path = "/api/user/myorganizations"
    payload = await client.request("GET", path) or []
    return [OrganizationDomain.model_validate(item) for item in ensure_list(path, payload)]
