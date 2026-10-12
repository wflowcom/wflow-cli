"""DocumentProperties tag: custom property definitions, and the values set per document."""

from typing import Annotated

from pydantic import Field

from wflow_api.client import WflowClient
from wflow_api.guards import path_segment, query_params, write_definitions_json, write_json, write_json_list
from wflow_api.models import OrgSlug, PropertyUpdate, WriteResult
from wflow_api.models.documents import Property, PropertyDefinition
from wflow_api.operation import operation


@operation
async def get_document_properties(client: WflowClient, organization: OrgSlug, documentId: str) -> list[Property]:
    """The custom property values set on one document.

    A workspace defines its custom properties once with `list_document_property_definitions`;
    this is what a specific document holds for each of them.

    Fields:

    - `name`, `type` — the definition this value belongs to
    - `value` — what this document holds for the property
    - `order`, `show`, `editable`, `kinds` — the definition's own presentation and
      applicability settings, echoed alongside the value
    """
    payload = await client.request("GET", f"/api/{organization}/documents/{path_segment(documentId)}/properties") or []
    return [Property.model_validate(item) for item in payload]


@operation
async def get_document_property_definition(client: WflowClient, organization: OrgSlug, id: str) -> PropertyDefinition:
    """One custom property definition, by its id.

    Use `list_document_property_definitions` to find the id, or resolve one already seen
    on a document's `get_document_properties` result.

    Fields:

    - `name`, `type` — how the property is labelled and what kind of value it holds
    - `order`, `show` — where it appears, and whether it is shown at all
    - `editable` — whether a document's value for it can be changed
    - `kinds` — which document kinds it applies to
    """
    payload = (
        await client.request("GET", f"/api/{organization}/documents/properties/definition/{path_segment(id)}") or {}
    )
    return PropertyDefinition.model_validate(payload)


@operation
async def list_document_property_definitions(client: WflowClient, organization: OrgSlug) -> list[PropertyDefinition]:
    """Every custom property defined in the workspace.

    Call this to learn what custom fields exist before reading or interpreting the
    values `get_document_properties` returns for a specific document.

    Fields:

    - `name`, `type` — how the property is labelled and what kind of value it holds
    - `order`, `show` — where it appears, and whether it is shown at all
    - `editable` — whether a document's value for it can be changed
    - `kinds` — which document kinds it applies to
    """
    payload = await client.request("GET", f"/api/{organization}/documents/properties/definitions") or []
    return [PropertyDefinition.model_validate(item) for item in payload]


@operation
async def delete_document_property(
    client: WflowClient, organization: OrgSlug, documentId: str, propertyId: str
) -> WriteResult:
    """Clear one custom property value from one document.

    Only this document's value goes; the definition stays and every other document keeps
    its own value. Get `propertyId` from the `id` of the entry in
    `get_document_properties`.

    Fields: on the result —

    - `action` — "deleted"
    - `resource` — "documents/properties"
    """
    await client.request(
        "DELETE", f"/api/{organization}/documents/{path_segment(documentId)}/properties/{path_segment(propertyId)}"
    )
    return WriteResult(action="deleted", resource="documents/properties")


@operation
async def delete_document_property_definition(client: WflowClient, organization: OrgSlug, id: str) -> WriteResult:
    """Delete one custom property definition from the workspace.

    This is the definition itself, not one document's value for it: the property stops
    existing for every document at once. To clear a single document's value, use
    `delete_document_property`. Get the id from `list_document_property_definitions`.

    Fields: on the result —

    - `action` — "deleted"
    - `resource` — "documents/properties/definition"
    """
    await client.request("DELETE", f"/api/{organization}/documents/properties/definition/{path_segment(id)}")
    return WriteResult(action="deleted", resource="documents/properties/definition")


@operation
async def update_document_properties(
    client: WflowClient, organization: OrgSlug, documentId: str, properties: list[PropertyUpdate]
) -> WriteResult:
    """Replace the custom property values held on one document.

    The list you send becomes the document's values, so a property you leave out is
    cleared on this document. `get_document_properties` returns everything it currently
    holds, in one array — read it first and send back the `id` and `value` of every entry
    you mean to keep, and nothing else: the read also carries each definition's name, type
    and presentation, which this operation does not write. To set a value for a property the
    workspace has not defined yet, use `update_document_properties_with_definition`.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "documents/properties"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/documents/{path_segment(documentId)}/properties",
        json=write_json_list(properties),
    )
    return WriteResult(action="updated", resource="documents/properties")


@operation
async def update_document_properties_with_definition(
    client: WflowClient,
    organization: OrgSlug,
    documentId: str,
    properties: list[Property],
    addOnly: Annotated[
        bool | None, Field(default=None, description="Leave an existing definition alone; defaults to true")
    ] = None,
) -> WriteResult:
    """Define new custom properties and set their values on one document.

    Every entry must carry `id`, `name`, `type` and `value`, whether the property is new to
    the workspace or already defined: wflow refuses the whole list over an entry holding
    only `id` and `value`, so such a list is refused here before anything is sent. An
    already-defined property sent in full gets its value updated on this document; one
    you leave out keeps its value. To set values without repeating definitions, use
    `update_document_properties`. `id` is a free-form string you choose; wflow keeps at
    most 30 characters of it and drops dashes, so a GUID comes back changed — pick a
    short plain id. A definition sent with only those four fields is created hidden and
    read-only (`order` 0, `show` false, `editable` false) — change that with
    `update_document_property_definition`. A definition is workspace configuration, so that
    part reaches every document. `addOnly` defaults to true, which leaves an existing
    definition as it is; false rewrites it from what you send, for every document at once.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "documents/properties/withdefinition"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/documents/{path_segment(documentId)}/properties/withdefinition",
        params=query_params(addOnly=addOnly),
        json=write_definitions_json(properties, values_operation="update_document_properties"),
    )
    return WriteResult(action="updated", resource="documents/properties/withdefinition")


@operation
async def update_document_property_definition(
    client: WflowClient, organization: OrgSlug, definition: PropertyDefinition
) -> WriteResult:
    """Define a custom property for documents, or replace an existing definition.

    This is workspace configuration, not one document's value: every document sees the
    change at once. **`id` is required and you choose it** — a free-form string, not a
    GUID wflow mints; a definition sent without one creates nothing. wflow keeps at most
    30 characters of the id and drops dashes, so a GUID comes back changed — pick a short
    plain id. The submitted object replaces the stored definition, so a field you
    leave out can be cleared, and `kinds` and `data` are whole lists — omit a document
    kind and the property stops applying there, omit a choice from `data` and it can no
    longer be picked. `get_document_property_definition` returns the definition in full;
    read it first when changing one that exists.

    **`type` is not reliably stored.** A definition sent with `type: "Text"` can be
    accepted as a success and read back as `type: "UNDEFINED"`; the set of values wflow
    accepts is not documented. Read the definition back and check what landed rather
    than trusting the write.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "documents/properties/definition"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/documents/properties/definition",
        json=write_json(definition),
    )
    return WriteResult(action="updated", resource="documents/properties/definition")
