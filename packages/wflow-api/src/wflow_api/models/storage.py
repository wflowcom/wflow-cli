"""Generated from the wflow OpenAPI spec, then refined by hand.

Regenerate with `uv run scripts/wflow_spec.py --models <Name> ...` and review
the diff; hand-written descriptions live here and must not be lost."""

from pydantic import Field

from wflow_api.models.common import WflowModel, WflowTimestamp


class StorageFile(WflowModel):
    """Storage file"""

    id: str | None = Field(default=None, description="Gets or sets the identifier.")
    name: str | None = Field(default=None, description="Gets or sets the name.")
    description: str | None = Field(default=None, description="Gets or sets the description.")
    created: WflowTimestamp | None = Field(default=None, description="Gets or sets the created date.")
    updated: WflowTimestamp | None = Field(default=None, description="Gets or sets the updated date.")
    removed: WflowTimestamp | None = Field(default=None, description="Gets or sets the removed date.")
    locked: bool | None = Field(
        default=None,
        description="Gets or sets a value indicating whether this wflow.Core.Contracts.Storage.Files.StorageFile is locked.",
    )
    approvalStatus: str | None = Field(
        default=None, description="One of: NotApproved, Approved, Rejected, Returned, None"
    )
    folderId: str | None = Field(default=None, description="Gets or sets the folder identifier.")
    location: str | None = Field(default=None, description="Gets or sets the location.")


class StorageFolder(WflowModel):
    """Storage folder"""

    id: str | None = Field(default=None, description="Gets or sets the identifier.")
    parentId: str | None = Field(default=None, description="Gets or sets the parent identifier.")
    name: str | None = Field(default=None, description="Gets or sets the name.")
    fullPath: str | None = Field(default=None, description="Gets or sets the full path.")
    hasChildren: bool | None = Field(default=None, description="Gets or sets the has children.")
