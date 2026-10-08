"""Account and organization models, mirroring the schemas in the wflow OpenAPI spec."""

from pydantic import Field

from wflow_api.models.common import WflowModel, WflowTimestamp


class OrganizationDomain(WflowModel):
    """A workspace the signed-in user has access to, as listed by list_organizations.

    Distinct from Organization, which is one workspace's own detail.
    """

    name: str | None = None
    baseURL: str | None = Field(default=None, description='Host, e.g. "nonameorg.wflow.com"')
    subdomain: str | None = Field(default=None, description="Workspace slug; pass as `organization`")
    trialExpiration: WflowTimestamp | None = Field(default=None, description="Null when not on a trial")


class Identity(WflowModel):
    id: str | None = None
    login: str | None = None
    firstName: str | None = None
    lastName: str | None = None
    fullName: str | None = None
    language: str | None = Field(default=None, description="ISO 639-1 code")


class RoleBase(WflowModel):
    id: str | None = None
    name: str | None = None
    description: str | None = None


class TeamBase(WflowModel):
    id: str | None = None
    name: str | None = None
    description: str | None = None
    system: bool | None = Field(default=None, description="Built-in, not organization-created")
    # get_document_rights sends this; declared so its read-then-PUT-back round-trip is not refused.
    fromApprovalTemplate: bool | None = Field(
        default=None, description="Access came from an approval template rather than being set directly"
    )


class DocumentTypeBase(WflowModel):
    id: str | None = None
    name: str | None = None
    kind: str | None = Field(default=None, description="e.g. IncomingInvoice, Contract")
    default: bool | None = None


class TypePermission(WflowModel):
    documentType: DocumentTypeBase | None = None
    permission: str | None = Field(default=None, description="All, OnlyAssigned or FullAccess")


class UserFull(WflowModel):
    """The profile of the authenticated user within one organization."""

    id: str | None = None
    identity: Identity | None = None
    created: WflowTimestamp | None = None
    hasFullAccess: bool | None = None
    roles: list[RoleBase] | None = None
    teams: list[TeamBase] | None = None
    documentTypes: list[TypePermission] | None = Field(default=None, description="Per document type access")
    rights: list[str] | None = Field(default=None, description="e.g. CanApprove, CanCreateDocument")


Account = UserFull


class Organization(WflowModel):
    """The workspace's own identity, as returned by get_organization."""

    id: str | None = Field(default=None, description="Id")
    name: str | None = Field(default=None, description="Name")
    created: WflowTimestamp | None = Field(default=None, description="Creation date (yyyy-mm-ddThh:mm:ss.ffffff)")
    organizationUrlPart: str | None = Field(default=None, description="Organization part in URL")
    customerUrlPart: str | None = Field(default=None, description="Customer part in URL")
    vatCountry: str | None = Field(default=None, description="VAT registration country ISO code (fixed length 3 chars)")
    vatNonPayer: bool | None = None
    seriesOnDocument: bool | None = None
    acceptDateAsCreatedDate: bool | None = None
    allowSupportAccess: bool | None = None
    trialExpiration: WflowTimestamp | None = None
    authenticationPolicy: str | None = Field(
        default=None, description="One of: MultiFactor, MicrosoftSingleSign, GoogleSingleSign"
    )
    biDashboardStatus: str | None = Field(default=None, description="One of: None, InPreparation, Active")
    biDashboardTrialExpires: WflowTimestamp | None = Field(
        default=None, description="Gets or sets the bi dashboard trial expires."
    )


class OrganizationSettings(WflowModel):
    """How the workspace processes documents, as returned by get_organization_settings."""

    name: str | None = None
    vatCountry: str | None = None
    vatNonPayer: bool | None = None
    seriesOnDocument: bool | None = None
    acceptDateAsCreatedDate: bool | None = None
    defaultLanguage: str | None = None
    allowSupportAccess: bool | None = None
    autoCloneLastDocumentAccounting: bool | None = None
    settings: str | None = None
    autoLinkIISD: bool | None = None
    autoLinkTakeLinesIISD: bool | None = None
    autoLinkTakeAccountingIISD: bool | None = None
    shareApproveIISD: bool | None = None
    shareApproveIISDTolerance: float | None = None
    numberOnlyIISD: bool | None = None
    autoLinkIISDToleranceRate: int | None = None
    processIsdoc: bool | None = None
    processIsdocLines: bool | None = None
    processIsdocDescription: bool | None = None
    processEKasa: bool | None = None
    processEKasaLines: bool | None = None
    sortDocumentsByIc: bool | None = None
    enableLinesApproval: bool | None = None
    autoLinkPartner: bool | None = None
    autoGenerateMissingPDFForISDOC: bool | None = None
    vatInclusiveBudgets: bool | None = None
    trialExpiration: WflowTimestamp | None = Field(default=None, description="Gets or sets the trial expiration date.")
    fiscalYearStart: int | None = None
