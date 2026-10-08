"""Checks every operation relies on: arguments, write bodies, and what wflow sends back."""

from collections.abc import Sequence
from email.message import Message
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

import httpx

from wflow_api.errors import WflowError
from wflow_api.models.account import Account
from wflow_api.models.common import WflowModel
from wflow_api.models.documents import Property

if TYPE_CHECKING:
    from wflow_api.client import WflowClient


def query_params(**kwargs: object) -> dict[str, object]:
    return {name: value for name, value in kwargs.items() if value is not None}


def path_segment(value: str) -> str:
    if value and not value.strip("."):
        raise WflowError(
            f"{value!r} is not a usable path segment: a run of dots is resolved away before the request "
            "leaves, so the call would land on the parent record and report success against it. Pass the "
            "identifier the paired read hands back."
        )
    return quote(value, safe="")


def _unknown_fields(item: WflowModel, path: str) -> list[str]:
    unknown = [f"{path}{name}" for name in item.model_extra or {}]
    for name in type(item).model_fields:
        value = getattr(item, name)
        for index, nested in enumerate(value if isinstance(value, list) else [value]):
            if isinstance(nested, WflowModel):
                position = f"[{index}]" if isinstance(value, list) else ""
                unknown += _unknown_fields(nested, f"{path}{name}{position}.")
    return unknown


def _refuse_unknown(unknown: list[str]) -> None:
    if unknown:
        raise WflowError(
            f"Unknown field(s) in the payload: {', '.join(unknown)}. wflow ignores JSON members it does "
            "not recognise, so the write would report success while those values never arrive — and on a "
            "whole-record write any field one of them was meant to set is cleared instead. Correct the "
            "spelling, or drop the field: only the fields the model declares can be written."
        )


def _indexed_unknown(items: Sequence[WflowModel]) -> list[str]:
    return [name for index, item in enumerate(items) for name in _unknown_fields(item, f"[{index}].")]


def write_body(items: Sequence[WflowModel]) -> list[dict[str, Any]]:
    if not items:
        raise WflowError(
            "Refusing to send an empty list of records: it can neither add nor update anything, and on "
            "an update_register_* call it would mark every record in the register invalid. To retire "
            "records deliberately, send them to the matching patch_register_* operation with isValid: false "
            "— and keep that field in every later payload naming them, because it defaults to true and a "
            "write that omits it revives the record."
        )
    _refuse_unknown(_indexed_unknown(items))
    return [item.model_dump(exclude_none=True) for item in items]


def write_json(item: WflowModel) -> dict[str, Any]:
    _refuse_unknown(_unknown_fields(item, ""))
    return item.model_dump(mode="json", exclude_none=True)


def write_json_list(items: Sequence[WflowModel], *, allow_empty: bool = False) -> list[dict[str, Any]]:
    if not items and not allow_empty:
        raise WflowError(
            "Refusing to send an empty list: this endpoint replaces the whole set, so it would clear "
            "everything currently held rather than change nothing, and wflow keeps no version history to "
            "restore it from. An empty list is also what payload construction yields when it yields nothing "
            "— a read that came back empty, a filter that matched no rows. Send the records you mean to "
            "keep; to remove one deliberately, use the matching delete_* operation where the endpoint has one."
        )
    _refuse_unknown(_indexed_unknown(items))
    return [item.model_dump(mode="json", exclude_none=True) for item in items]


def write_definitions_json(properties: Sequence[Property], *, values_operation: str) -> list[dict[str, Any]]:
    undefined = [f"[{index}]" for index, item in enumerate(properties) if not item.carries_definition()]
    if undefined:
        raise WflowError(
            f"Entries {', '.join(undefined)} carry no `name` and `type`. wflow refuses the whole list over "
            f"such an entry, so nothing was sent. Give every entry its `name` and `type`, or set values on "
            f"already-defined properties with {values_operation}."
        )
    return write_json_list(properties)


def ensure_list(path: str, payload: Any) -> list[Any]:
    if not isinstance(payload, list):
        raise WflowError(f"wflow GET {path} returned {payload!r}, not an array.")
    return payload


def problem_detail(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return ""
    if not isinstance(body, dict):
        return ""
    parts = [str(body[key]) for key in ("title", "detail") if body.get(key)]
    return f" {' — '.join(parts)}" if parts else ""


def filename_from_disposition(header: str) -> str | None:
    message = Message()
    message["content-disposition"] = header
    return message.get_filename() or None


async def current_account(client: "WflowClient", organization: str) -> Account:
    payload = await client.request("GET", f"/api/{organization}/account")
    if payload is None:
        raise WflowError(
            f"wflow returned an empty account for organization '{organization}' "
            "(HTTP 200, body `null`). This endpoint reports the *current user*, so the "
            "signed-in identity has no account in that workspace. Use list_organizations "
            "to see which slugs are visible."
        )
    return Account.model_validate(payload)
