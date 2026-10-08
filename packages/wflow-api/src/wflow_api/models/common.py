"""Shared building blocks: the model base, the repeated operation arguments, and the outcome types writes and downloads return.

Field names are camelCase, exactly as wflow sends them, so a caller can read the
published wflow reference and this output side by side.

Every field read off the API is optional and unknown fields are kept: this is a trust
boundary against a live API, where a missing field must not turn a working call into an
opaque failure, and a newly added one should reach the caller rather than be dropped here.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, WithJsonSchema, field_validator


class WflowModel(BaseModel):
    model_config = ConfigDict(extra="allow")


DOTNET_UNSET_DATE = datetime.min
"""What .NET serialises for a DateTime nobody set: "0001-01-01T00:00:00"."""


def _unset_date_is_none(value: datetime) -> datetime | None:
    return None if value.replace(tzinfo=None) == DOTNET_UNSET_DATE else value


WflowTimestamp = Annotated[datetime, AfterValidator(_unset_date_is_none), WithJsonSchema({"type": "string"})]
"""A timestamp read off wflow, parsed but published without a `format`.

wflow sends these with no UTC offset — "2026-05-13T07:42:45.010" — which pydantic parses
into a naive datetime and re-serializes just as offsetless. That is not RFC 3339, so a
field declaring `format: "date-time"` makes the MCP client reject the whole response.
Attaching an offset here would make the schema true only if these are UTC, which wflow
does not state; publishing a plain string claims no more than wflow actually sends.

A date wflow never filled in arrives as .NET's default, "0001-01-01T00:00:00" — the
summaries `list_document_links` returns carry it as `created` and `updated`. It is
published as null, because a client reading a real year-one date would be misled, and
every field of this type is already nullable.
"""


class Paged[T](WflowModel):
    """One page of a collection. `totalItems` is the count across all pages, so it says
    whether the page in hand is the whole register or only the start of it.
    """

    items: list[T] = []
    totalItems: int | None = None
    pageSize: int | None = None
    page: int | None = None

    @field_validator("items", mode="before")
    @classmethod
    def _null_items_is_an_empty_page(cls, value: object) -> object:
        """wflow documents `items` as nullable; an empty page must not fail validation."""
        return [] if value is None else value


OrgSlug = Annotated[
    str,
    Field(
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$",
        description='Workspace slug, e.g. "produkt-testovaci" (`subdomain` from list_organizations)',
    ),
]
Search = Annotated[str | None, Field(default=None, description="Free-text search value")]
Sort = Annotated[
    str | None,
    Field(
        default=None,
        description=(
            "Comma-separated sort keys, ascending unless a key carries the 'desc' modifier, "
            'e.g. "created,totalAmount desc". Sort on the fields this operation documents.'
        ),
    ),
]
Query = Annotated[
    str | None,
    Field(
        default=None,
        description=(
            "Filter expression `field operator value`, with one space around the operator: "
            '`number = "A100"` is accepted, `number="A100"` is rejected as invalid syntax. '
            "Operators are = != < <= > >=, and against null only = and !=. Quote text and dates "
            '("2021-01-01"), leave numbers and null bare. Chain conditions with `and`, e.g. '
            '`totalAmount > 1000 and created > "2021-01-01"`. Filter on the fields this operation documents.'
        ),
    ),
]
PageSize = Annotated[int | None, Field(default=None, description="Records per page")]
Page = Annotated[int | None, Field(default=None, description="Page number, zero-based")]


class WriteResult(WflowModel):
    """What a tool returns when wflow accepted a change.

    Most write endpoints answer 200 with no body, so there is nothing to hand back but
    a confirmation. Returning one shape for all of them means a caller never has to ask
    whether silence meant success.
    """

    action: str = Field(description="created, updated, patched or deleted")
    resource: str = Field(description='What was changed, e.g. "registers/partners"')
    id: str | None = Field(default=None, description="Set only where wflow returns an identifier")


@dataclass(frozen=True)
class FileContent:
    """A file as wflow sent it."""

    filename: str | None
    content_type: str | None
    content: bytes
