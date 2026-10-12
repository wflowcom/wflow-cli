"""The wflow OpenAPI document, and the tables that turn an operation into a tool name.

Run with --fetch to vendor the published document; committing the result means an upstream
change shows up as a git diff instead of a surprise at runtime.

The tables are design §3 (naming) and §11 (tag → leaf) made executable. tests/api/test_wflow_spec.py
checks they have no gaps and no duplicates; tests/api/test_parity.py checks the registered
tools against them.
"""

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

SPEC_URL = "https://developers.wflow.com/api/v1/projects/wflow/wflowapidoc/nodes/reference/WflowOpenAPI.json"
HERE = Path(__file__).resolve().parent
VENDORED = HERE / "wflow-openapi.json"

METHODS = ("get", "post", "put", "patch", "delete")
REGISTER_VERBS = {"get": "list_register_{}", "put": "update_register_{}", "patch": "patch_register_{}"}

# Design §11. Kept here so the split is executable rather than prose, the same reason
# the naming table is.
LEAF_BY_TAG = {
    "Account": "account",
    "User": "account",
    "Registers": "registers",
    "Documents": "documents",
    "DocumentTypes": "documents",
    "DocumentLinks": "documents",
    "DocumentRights": "documents",
    "DocumentComments": "documents",
    "DocumentPayments": "documents",
    "DocumentFiles": "document_files",
    "DocumentProperties": "document_files",
    "DocumentTags": "document_files",
    "StorageFiles": "storage",
    "StorageFileProperties": "storage",
    "StorageFolders": "storage",
    "StorageRights": "storage",
    "ApprovalsTemplates": "approvals",
    "DocumentApprovals": "approvals",
    "StorageFileApprovals": "approvals",
    "Roles": "admin",
    "Teams": "admin",
    "Users": "admin",
    "Organization": "admin",
    "WebHookRegistrations": "integrations",
    "Integrations": "integrations",
}

TOOL_NAMES = {
    ("get", "/api/user/myorganizations"): "list_organizations",
    ("get", "/api/{organization}/account"): "get_me",
    ("get", "/api/{organization}/approvalstemplates"): "list_approval_templates",
    ("get", "/api/{organization}/approvalstemplates/{templateId}"): "get_approval_template",
    ("delete", "/api/{organization}/approvalstemplates/{templateId}"): "delete_approval_template",
    ("put", "/api/{organization}/approvalstemplates"): "update_approval_template",
    ("get", "/api/{organization}/documents"): "list_documents",
    ("put", "/api/{organization}/documents"): "update_document",
    ("get", "/api/{organization}/documents/{documentId}"): "get_document",
    ("delete", "/api/{organization}/documents/{documentId}"): "delete_document",
    ("get", "/api/{organization}/documents/{documentId}/metadata"): "get_document_metadata",
    ("put", "/api/{organization}/documents/{documentId}/metadata"): "update_document_metadata",
    ("get", "/api/{organization}/documents/{documentId}/events"): "list_document_events",
    ("get", "/api/{organization}/documents/toexport"): "list_documents_to_export",
    ("get", "/api/{organization}/documents/toextract"): "list_documents_to_extract",
    ("post", "/api/{organization}/documents/{documentId}/task/{type}"): "create_document_task",
    ("post", "/api/{organization}/documents/withfiles"): "create_document_with_files",
    ("post", "/api/{organization}/documents/export/{format}"): "export_documents",
    ("put", "/api/{organization}/documents/{documentId}/lock/{value}"): "lock_document",
    ("put", "/api/{organization}/documents/{documentId}/task/{taskType}/processed"): "set_document_task_processed",
    ("get", "/api/{organization}/storage/files/{fileId}/download"): "download_storage_file",
    ("get", "/api/{organization}/storage/files/{fileId}"): "get_storage_file",
    ("get", "/api/{organization}/storage/files"): "list_storage_files",
    ("delete", "/api/{organization}/storage/files/{fileId}"): "delete_storage_file",
    ("put", "/api/{organization}/storage/files/{fileId}/lock/{value}"): "lock_storage_file",
    ("put", "/api/{organization}/storage/files/{fileId}/move"): "move_storage_file",
    ("put", "/api/{organization}/storage/files/{fileId}/rename"): "rename_storage_file",
    ("put", "/api/{organization}/storage/files/{fileId}/restore"): "restore_storage_file",
    ("put", "/api/{organization}/storage/files/upload"): "upload_storage_file",
    ("get", "/api/{organization}/documents/{documentId}/properties"): "get_document_properties",
    ("get", "/api/{organization}/documents/properties/definition/{id}"): "get_document_property_definition",
    ("get", "/api/{organization}/documents/properties/definitions"): "list_document_property_definitions",
    ("delete", "/api/{organization}/documents/{documentId}/properties/{propertyId}"): "delete_document_property",
    (
        "delete",
        "/api/{organization}/documents/properties/definition/{id}",
    ): "delete_document_property_definition",
    ("put", "/api/{organization}/documents/{documentId}/properties"): "update_document_properties",
    (
        "put",
        "/api/{organization}/documents/{documentId}/properties/withdefinition",
    ): "update_document_properties_with_definition",
    ("put", "/api/{organization}/documents/properties/definition"): "update_document_property_definition",
    ("get", "/api/{organization}/storage/files/{fileId}/properties"): "get_storage_file_properties",
    (
        "get",
        "/api/{organization}/storage/files/properties/definition/{id}",
    ): "get_storage_file_property_definition",
    (
        "get",
        "/api/{organization}/storage/files/properties/definitions",
    ): "list_storage_file_property_definitions",
    (
        "delete",
        "/api/{organization}/storage/files/{fileId}/properties/{propertyId}",
    ): "delete_storage_file_property",
    (
        "delete",
        "/api/{organization}/storage/files/properties/definition/{id}",
    ): "delete_storage_file_property_definition",
    ("put", "/api/{organization}/storage/files/{fileId}/properties"): "update_storage_file_properties",
    (
        "put",
        "/api/{organization}/storage/files/{fileId}/properties/withdefinition",
    ): "update_storage_file_properties_with_definition",
    ("put", "/api/{organization}/storage/files/properties/definition"): "update_storage_file_property_definition",
    ("get", "/api/{organization}/documents/files/{fileId}/download"): "download_document_file",
    ("get", "/api/{organization}/documents/{documentId}/files/main/download"): "download_document_main_file",
    ("get", "/api/{organization}/documents/{documentId}/files"): "list_document_files",
    ("delete", "/api/{organization}/documents/files/{fileId}"): "delete_document_file",
    ("put", "/api/{organization}/documents/{documentId}/files/{fileId}/stamp"): "stamp_document_file",
    ("put", "/api/{organization}/documents/{documentId}/files/upload"): "upload_document_file",
    ("get", "/api/{organization}/roles/{id}"): "get_role",
    ("get", "/api/{organization}/roles"): "list_roles",
    ("post", "/api/{organization}/roles"): "create_role",
    ("delete", "/api/{organization}/roles/{id}"): "delete_role",
    ("put", "/api/{organization}/roles/{id}"): "update_role",
    ("get", "/api/{organization}/teams/{id}"): "get_team",
    ("get", "/api/{organization}/teams"): "list_teams",
    ("post", "/api/{organization}/teams"): "create_team",
    ("delete", "/api/{organization}/teams/{id}"): "delete_team",
    ("put", "/api/{organization}/teams/{id}"): "update_team",
    ("get", "/api/{organization}/documents/{documentId}/tags"): "get_document_tags",
    ("get", "/api/{organization}/documents/tags"): "list_document_tags",
    ("put", "/api/{organization}/documents/{documentId}/tags/{tag}"): "add_document_tag",
    ("delete", "/api/{organization}/documents/{documentId}/tags/{tag}"): "delete_document_tag",
    ("get", "/api/{organization}/documents/types/typeid:guid"): "get_document_type",
    ("get", "/api/{organization}/documents/types"): "list_document_types",
    ("delete", "/api/{organization}/documents/types/typeid:guid"): "delete_document_type",
    ("put", "/api/{organization}/documents/types"): "update_document_type",
    ("get", "/api/{organization}/storage/folders/{folderId}"): "get_storage_folder",
    ("get", "/api/{organization}/storage/folders/children"): "list_storage_folder_children",
    ("delete", "/api/{organization}/storage/folders/{folderId}"): "delete_storage_folder",
    ("put", "/api/{organization}/storage/folders"): "update_storage_folder",
    ("get", "/api/{organization}/storage/files/{fileId}/rights"): "get_storage_file_rights",
    ("get", "/api/{organization}/storage/folders/{folderId}/rights"): "get_storage_folder_rights",
    ("put", "/api/{organization}/storage/files/{fileId}/rights"): "set_storage_file_rights",
    ("put", "/api/{organization}/storage/folders/{folderId}/rights"): "set_storage_folder_rights",
    ("get", "/api/{organization}/users/{userId}"): "get_user",
    ("get", "/api/{organization}/users"): "list_users",
    ("delete", "/api/{organization}/users/{userId}"): "delete_user",
    ("put", "/api/{organization}/users"): "update_user",
    ("get", "/api/{organization}/documents/{documentId}/approvals"): "get_document_approvals",
    ("delete", "/api/{organization}/documents/{documentId}/approvals"): "delete_document_approval_path",
    (
        "put",
        "/api/{organization}/documents/{documentId}/approvals/set/{templateId}",
    ): "set_document_approval_path",
    ("get", "/api/{organization}/documents/{documentId}/links"): "list_document_links",
    ("put", "/api/{organization}/documents/{documentId}/links/{linkedDocumentId}"): "link_document",
    ("delete", "/api/{organization}/documents/{documentId}/links/{linkedDocumentId}"): "unlink_document",
    ("get", "/api/{organization}/storage/files/{fileId}/approvals"): "get_storage_file_approvals",
    ("delete", "/api/{organization}/storage/files/{fileId}/approvals"): "delete_storage_file_approval_path",
    (
        "put",
        "/api/{organization}/storage/files/{fileId}/approvals/set/{templateId}",
    ): "set_storage_file_approval_path",
    ("get", "/api/{organization}/webhookregistrations"): "list_webhook_registrations",
    ("delete", "/api/{organization}/webhookregistrations/{registrationId}"): "delete_webhook_registration",
    ("put", "/api/{organization}/webhookregistrations"): "update_webhook_registration",
    ("get", "/api/{organization}/documents/{documentId}/rights"): "get_document_rights",
    ("put", "/api/{organization}/documents/{documentId}/rights"): "set_document_rights",
    ("put", "/api/{organization}/integrations/allow"): "allow_integration",
    ("post", "/api/{organization}/integrations/apiclient"): "create_api_client",
    ("get", "/api/{organization}/organization"): "get_organization",
    ("get", "/api/{organization}/organization/settings"): "get_organization_settings",
    ("get", "/api/{organization}/documents/{documentId}/comments"): "list_document_comments",
    ("put", "/api/{organization}/documents/{documentId}/payments"): "update_document_payments",
}


def snake(text: str) -> str:
    return re.sub(r"\s+", "_", re.sub(r"[^A-Za-z0-9]+", " ", text).strip()).lower()


def tool_name(method: str, path: str, summary: str) -> str:
    """Apply design §3. Registers come out of the rule; everything else out of the table."""
    if "/registers/" in path:
        register = snake(re.sub(r"^(Get|Update|Patch)\s+", "", summary))
        return REGISTER_VERBS[method].format(register)
    return TOOL_NAMES[(method, path)]


def operations(spec: dict):
    """Yield (path, method, operation) for every documented operation."""
    for path, item in spec["paths"].items():
        for method, operation in item.items():
            if method in METHODS:
                yield path, method, operation


SCALARS = {"string": "str", "integer": "int", "number": "float", "boolean": "bool", "object": "dict"}


def python_type(spec: dict, schema: dict) -> str:
    """Map an OpenAPI property schema to a Python annotation.

    Enums become plain str: this is a trust boundary against a live API, and a value
    wflow adds tomorrow must reach the caller rather than fail validation here. A
    property with neither a type nor a $ref (e.g. Property.value) becomes Any, since
    Pydantic's default validation mode would otherwise reject anything but a str.
    """
    if "$ref" in schema:
        name = schema["$ref"].rsplit("/", 1)[-1]
        target = spec["components"]["schemas"].get(name, {})
        return "str" if "enum" in target else name
    if schema.get("type") == "array":
        return f"list[{python_type(spec, schema.get('items', {}))}]"
    if schema.get("format") in ("date-time", "date"):
        return "datetime"
    if "type" not in schema:
        return "Any"
    return SCALARS.get(schema["type"], "str")


def field_description(spec: dict, schema: dict) -> str:
    """Carry the spec's own description, plus the permitted values for an enum."""
    parts = [schema.get("description", "").strip()]
    ref = schema.get("$ref") or schema.get("items", {}).get("$ref")
    if ref:
        target = spec["components"]["schemas"].get(ref.rsplit("/", 1)[-1], {})
        if "enum" in target:
            parts.append("One of: " + ", ".join(target["enum"]))
    return " ".join(part for part in parts if part).replace('"', "'")


def model_source(spec: dict, name: str) -> str:
    schema = spec["components"]["schemas"][name]
    lines = [f"class {name}(WflowModel):"]
    doc = schema.get("description", "").strip()
    if doc:
        lines.append(f'    """{doc}"""')
        lines.append("")
    properties = schema.get("properties", {})
    if not properties:
        lines.append("    pass")
    for field, prop in properties.items():
        annotation = python_type(spec, prop)
        description = field_description(spec, prop)
        if description:
            lines.append(f'    {field}: {annotation} | None = Field(default=None, description="{description}")')
        else:
            lines.append(f"    {field}: {annotation} | None = None")
    return "\n".join(lines)


def dependency_order(spec: dict, names: list[str]) -> list[str]:
    """Emit a class after everything it references, so forward refs are unnecessary."""
    ordered: list[str] = []
    seen: set[str] = set()

    def visit(name: str) -> None:
        if name in seen or name not in spec["components"]["schemas"]:
            return
        seen.add(name)
        schema = spec["components"]["schemas"][name]
        if "enum" in schema:
            return
        for prop in schema.get("properties", {}).values():
            ref = prop.get("$ref") or prop.get("items", {}).get("$ref")
            if ref:
                visit(ref.rsplit("/", 1)[-1])
        ordered.append(name)

    for name in names:
        visit(name)
    return ordered


def models_source(spec: dict, names: list[str]) -> str:
    """Emit importable, lint-clean Pydantic classes for the given schemas.

    The import list is derived from the generated bodies rather than fixed, since an
    unused import (F401) and a missing one (F821) both fail lint, and compile() cannot
    catch the latter.
    """
    bodies = [model_source(spec, name) for name in dependency_order(spec, names)]
    text = "\n\n\n".join(bodies)

    imports = []
    if re.search(r"\bdatetime\b", text):
        imports.append("from datetime import datetime")
    if re.search(r"\bAny\b", text):
        imports.append("from typing import Any")
    if imports:
        imports.append("")
    if "Field(" in text:
        imports.append("from pydantic import Field")
        imports.append("")
    imports.append("from wflow_api.models.common import WflowModel")

    header = (
        '"""Generated from the wflow OpenAPI spec, then refined by hand.\n\n'
        "Regenerate with `uv run scripts/wflow_spec.py --models <Name> ...` and review\n"
        'the diff; hand-written descriptions live here and must not be lost."""\n\n' + "\n".join(imports) + "\n"
    )
    return header + "\n\n" + text + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true", help="download and vendor the OpenAPI document")
    parser.add_argument("--models", nargs="+", metavar="SCHEMA", help="emit Pydantic classes for these schemas")
    args = parser.parse_args(argv)

    if args.models:
        spec = json.loads(VENDORED.read_text())
        print(models_source(spec, args.models))
        return 0

    if not args.fetch:
        parser.error("nothing to do without --fetch; the tables are consumed by the tests")

    with urllib.request.urlopen(SPEC_URL) as response:
        VENDORED.write_bytes(response.read())
    print(f"vendored {VENDORED}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
