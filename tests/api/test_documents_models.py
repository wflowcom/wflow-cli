import typing

from wflow_api.models.account import DocumentTypeBase
from wflow_api.models.documents import Accounting, Document, DocumentBase, Partner, Property
from wflow_api.models.registers import PartnerFull, Register


def test_unknown_fields_survive():
    """wflow adding a field to Document must not mean the caller stops seeing it."""
    document = Document.model_validate({"id": "d-1", "somethingNew": "keep me"})

    assert document.model_dump()["somethingNew"] == "keep me"


def test_every_field_is_optional():
    """A missing field must not turn a working call into an opaque failure."""
    assert Document.model_validate({}).id is None


def test_an_untyped_property_value_accepts_a_non_string():
    """Property.value has no declared type in the spec; Any keeps Pydantic's smart mode
    from rejecting an int the way a plain str field would."""
    assert Property.model_validate({"value": 42000}).value == 42000


def test_document_base_reuses_the_shared_document_type_base():
    """DocumentTypeBase already lives in models/account.py; a regenerated copy here would
    let a caller validate against the wrong class."""
    assert typing.get_args(DocumentBase.model_fields["type"].annotation)[0] is DocumentTypeBase


def test_accounting_reuses_the_shared_register():
    """Register already lives in models/registers.py, the same class the 24 register tools use."""
    assert typing.get_args(Accounting.model_fields["activity"].annotation)[0] is Register


def test_partner_is_kept_generated_not_aliased_to_partner_full():
    """Partner and PartnerFull are different schemas in the spec; Partner must stay its own
    generated class rather than being folded into registers.PartnerFull."""
    assert Partner is not PartnerFull
