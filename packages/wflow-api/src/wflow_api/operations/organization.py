"""Organization: the current workspace's own identity and settings."""

from wflow_api.client import WflowClient
from wflow_api.models import Organization, OrganizationSettings, OrgSlug
from wflow_api.operation import operation


@operation
async def get_organization(client: WflowClient, organization: OrgSlug) -> Organization:
    """The workspace's own identity — who this organization is, not who the caller is.

    Use `get_me` for the signed-in user's rights within the workspace, and this for the
    workspace itself.

    Fields:

    - `name`, `id`, `created` — display name and identity
    - `organizationUrlPart`, `customerUrlPart` — the slugs in the workspace's URLs
    - `vatCountry`, `vatNonPayer` — which VAT regime documents are processed under
    - `seriesOnDocument`, `acceptDateAsCreatedDate` — document numbering and dating behaviour
    - `allowSupportAccess` — whether wflow support may enter this workspace
    - `trialExpiration` — trial end date, or null when not on a trial
    - `authenticationPolicy`, `biDashboardStatus`, `biDashboardTrialExpires`
    """
    return Organization.model_validate(await client.request("GET", f"/api/{organization}/organization") or {})


@operation
async def get_organization_settings(client: WflowClient, organization: OrgSlug) -> OrganizationSettings:
    """How this workspace processes documents — the toggles behind its automatic behaviour.

    Read this before explaining why a document was linked, posted or numbered the way it
    was: most of that behaviour is a setting here rather than a rule in the document.

    Fields:

    - `vatCountry`, `vatNonPayer`, `fiscalYearStart` — the accounting regime
    - `defaultLanguage`, `name` — workspace defaults
    - `processIsdoc`, `processIsdocLines`, `processIsdocDescription`,
      `autoGenerateMissingPDFForISDOC` — how ISDOC e-invoices are ingested
    - `processEKasa`, `processEKasaLines` — how eKasa receipts are ingested
    - `autoLinkIISD`, `autoLinkIISDToleranceRate`, `autoLinkTakeLinesIISD`,
      `autoLinkTakeAccountingIISD`, `numberOnlyIISD`, `shareApproveIISD`,
      `shareApproveIISDTolerance` — automatic linking of invoices to delivery notes
    - `autoLinkPartner`, `sortDocumentsByIc` — partner matching
    - `enableLinesApproval`, `autoCloneLastDocumentAccounting`, `vatInclusiveBudgets`
    - `allowSupportAccess`, `trialExpiration`
    """
    return OrganizationSettings.model_validate(
        await client.request("GET", f"/api/{organization}/organization/settings") or {}
    )
