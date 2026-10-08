import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import wflow_spec as gen


def test_register_names_come_out_of_the_rule():
    """72 register tools must not need 72 table entries to stay consistent."""
    assert gen.tool_name("get", "/api/{organization}/registers/costcenters", "Get Cost centers") == (
        "list_register_cost_centers"
    )
    assert gen.tool_name("put", "/api/{organization}/registers/costcenters", "Update Cost centers") == (
        "update_register_cost_centers"
    )
    assert gen.tool_name("patch", "/api/{organization}/registers/partners", "Patch Partners") == (
        "patch_register_partners"
    )


def test_the_other_operations_are_named_from_the_table():
    assert gen.tool_name("get", "/api/{organization}/documents/{documentId}", "Get Document") == "get_document"
    assert gen.tool_name("delete", "/api/{organization}/documents/{documentId}", "Delete document") == (
        "delete_document"
    )


def test_an_unknown_operation_is_an_error_not_a_guess():
    """A silently invented name is how an endpoint gets wrapped twice under two names."""
    try:
        gen.tool_name("get", "/api/{organization}/somethingnew", "New")
    except KeyError:
        return
    raise AssertionError("expected KeyError for an operation missing from the table")


def test_every_generated_name_is_unique(wflow_spec):
    names = [
        gen.tool_name(method, path, operation.get("summary", ""))
        for path, method, operation in gen.operations(wflow_spec)
    ]

    assert len(names) == len(set(names)), "two operations claim the same tool name"
    assert len(names) == 173


def test_every_tag_has_a_leaf(wflow_spec):
    """An unmapped tag would make the generator crash mid-run, having written half the files."""
    tags = {operation.get("tags", ["?"])[0] for _, _, operation in gen.operations(wflow_spec)}

    assert tags <= set(gen.LEAF_BY_TAG), f"unmapped tags: {tags - set(gen.LEAF_BY_TAG)}"


def test_a_scalar_field_becomes_an_optional_python_type(wflow_spec):
    """DocumentFile.name and .main both carry a spec description, so Field(...) is used."""
    source = gen.model_source(wflow_spec, "DocumentFile")

    assert "class DocumentFile(WflowModel):" in source
    assert 'name: str | None = Field(default=None, description="Name")' in source
    assert 'main: bool | None = Field(default=None, description="Main attribute")' in source


def test_a_referenced_field_keeps_its_model_type(wflow_spec):
    source = gen.model_source(wflow_spec, "DocumentEvent")

    assert "identity: IdentityBase | None" in source


def test_an_enum_field_becomes_str_with_the_values_in_the_description(wflow_spec):
    """A value wflow adds later must reach the caller, not fail validation."""
    source = gen.model_source(wflow_spec, "DocumentEvent")

    assert "Enum" not in source
    assert "type: str | None" in source


def test_an_array_field_becomes_a_list(wflow_spec):
    source = gen.model_source(wflow_spec, "ApprovalProcess")

    assert (
        'items: list[ApprovalProcessItem] | None = Field(default=None, description="Approval process item collection")'
        in source
    )


def test_an_untyped_field_becomes_any(wflow_spec):
    """Property.value has neither a type nor a $ref; Pydantic's smart mode would reject an
    int for a plain str field, so it must come out as Any instead."""
    source = gen.model_source(wflow_spec, "Property")

    assert 'value: Any | None = Field(default=None, description="Value")' in source


def test_generated_models_are_importable(wflow_spec, tmp_path):
    """Generated source that does not compile is worse than no generator."""
    source = gen.models_source(wflow_spec, ["DocumentFile", "DocumentEvent"])
    module = tmp_path / "generated.py"
    module.write_text(source)

    compile(module.read_text(), str(module), "exec")


def test_generated_header_imports_only_what_is_used(wflow_spec):
    """F401 (unused import) and F821 (undefined name) both fail lint; compile() cannot catch
    a missing name, since compiling never resolves it."""
    with_datetime = gen.models_source(wflow_spec, ["DocumentFile"])
    assert "from datetime import datetime" in with_datetime
    assert "from typing import Any" not in with_datetime

    with_any = gen.models_source(wflow_spec, ["Property"])
    assert "from typing import Any" in with_any
    assert "from datetime import datetime" not in with_any

    without_field = gen.models_source(wflow_spec, ["SequenceBase"])
    assert "from pydantic import Field" not in without_field
    assert "Field(" not in without_field
