"""Generated from the wflow OpenAPI spec, then refined by hand.

Regenerate with:

    uv run scripts/wflow_spec.py --models ApprovalsTemplate ApprovalsTemplatesTeam ApprovalsTemplateFull Role Team User WebHookRegistration

then review the diff; hand-written descriptions live here and must not be lost.

That command's dependency closure emits 9 classes, not the 7 below. Delete `Identity` and
`UserBase` from the regenerated output and import them instead — `Identity` from
wflow_api.models.account and `UserBase` from wflow_api.models.documents — because one name
must mean one shape. Re-emitting them here is what commit 106184d existed to undo.

The spec's four collection wrappers for these schemas — ApprovalsTemplateCollection,
RoleBaseCollection, TeamBaseCollection and UserCollection — are deliberately not generated:
the generic `Paged[T]` in wflow_api.models.common covers all four."""

from pydantic import Field

from wflow_api.models.account import Identity
from wflow_api.models.common import WflowModel, WflowTimestamp
from wflow_api.models.documents import UserBase


class ApprovalsTemplate(WflowModel):
    """Approvals template"""

    id: str | None = Field(default=None, description="Id")
    name: str | None = Field(default=None, description="Name")
    isEmpty: bool | None = Field(default=None, description="Is empty")


class ApprovalsTemplatesTeam(WflowModel):
    """Approvals templates team"""

    teamId: str | None = Field(default=None, description="Team Id")
    level: int | None = Field(default=None, description="Level in approval process")


class ApprovalsTemplateFull(WflowModel):
    """Approvals template full"""

    id: str | None = Field(default=None, description="Id")
    name: str | None = Field(default=None, description="Name")
    isEmpty: bool | None = Field(default=None, description="Is empty")
    accessTeams: list[str] | None = Field(default=None, description="Teams collection for automatic set access")
    teams: list[ApprovalsTemplatesTeam] | None = Field(default=None, description="Approvals teams collection")
    conditionFolders: list[str] | None = Field(
        default=None, description="Storage folder IDs collection for conditional assignment"
    )
    validationLockLevel: int | None = Field(default=None, description="Validation lock level")


class Role(WflowModel):
    """Role"""

    id: str | None = Field(default=None, description="Gets or sets the identifier.")
    name: str | None = Field(default=None, description="Gets or sets the name.")
    description: str | None = Field(default=None, description="Gets or sets the description.")
    users: list[UserBase] | None = Field(default=None, description="Gets or sets the users collection.")
    rights: list[str] | None = Field(
        default=None,
        description="Gets or sets the rights collection. One of: CanApprove, CanReview, CanManageApprovalPath, CanCreateDocument, CanDeleteDocument, CanManageAccess, CanChangeDocumentType, CanLock, CanManageAttachments, CanSendToExtraction, CanSendToReview, CanSendToErp, CanManageDocumentLinks, CanManageDocument, CanManageDocumentAccounting, CanManageCustomProperty, CanManageTags, CanManagePayments, CanMarkForPayment, CanExport, CanManageExternalSignature, CanStamp, CanManagePartners, CanManageBusinessItems, CanManageDocumentLinesTemplates, CanManageRegisters, CanManageSettings, CanManageFileStorage, CanManageExpenses, CanViewExpenses, CanViewReporting, CanManageBudgeting, CanManageDocumentBudgets, CanMoveDocumentToOtherOrganization, CanAccessInbox, CanRejectPeppolMessage",
    )


class Team(WflowModel):
    """Team"""

    id: str | None = Field(default=None, description="Gets or sets the identifier.")
    name: str | None = Field(default=None, description="Gets or sets the name.")
    description: str | None = Field(default=None, description="Gets or sets the description.")
    system: bool | None = Field(
        default=None,
        description="Gets or sets a value indicating whether this wflow.Core.Contracts.Teams.TeamBase is system.",
    )
    users: list[UserBase] | None = Field(default=None, description="Gets or sets the users collection.")


class User(WflowModel):
    """User"""

    id: str | None = Field(default=None, description="Id")
    identity: Identity | None = None
    created: WflowTimestamp | None = Field(default=None, description="Date of creation")
    hasFullAccess: bool | None = Field(default=None, description="Full access role indicator")


class WebHookRegistration(WflowModel):
    """web hook registration"""

    id: str | None = Field(default=None, description="Id")
    webHookUri: str | None = Field(default=None, description="Web hook URi")
    description: str | None = Field(default=None, description="Description")
    actions: list[str] | None = Field(
        default=None,
        description="Registered actions collection One of: All, DocumentReadyToExtract, DocumentReadyToExport, DocumentUpdated, DocumentApprovalProcessFinished, RegisterUpdated, DocumentDeleted, DocumentReadyToReview, DocumentCreated, DocumentReviewed",
    )
