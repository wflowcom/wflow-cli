import inspect
import re

import pytest

from tests.helpers import body_source, mock_wflow
from wflow_api.errors import WflowApiError, WflowError
from wflow_api.models.common import Paged
from wflow_api.models.registers import (
    BusinessItemUpdateC,
    KindRegister,
    Location,
    PartnerFull,
    Register,
    Serie,
    VATReturnLine,
)
from wflow_api.operations import registers


def test_the_shared_register_fields():
    register = Register.model_validate(
        {"id": "r-1", "externalId": "ERP-9", "code": "600", "description": "Sales", "isValid": True}
    )

    assert (register.code, register.externalId, register.isValid) == ("600", "ERP-9", True)


def test_kind_register_adds_the_document_kind():
    assert KindRegister.model_validate({"code": "A", "kind": "IncomingInvoice"}).kind == "IncomingInvoice"


def test_serie_carries_both_kind_and_invoice_type():
    serie = Serie.model_validate({"code": "FP", "kind": "IncomingInvoice", "invoiceType": "TaxInvoice"})

    assert (serie.kind, serie.invoiceType) == ("IncomingInvoice", "TaxInvoice")


def test_location_adds_address_and_contact():
    location = Location.model_validate({"code": "PRG", "address": "Praha 1", "contact": "Jan Novak"})

    assert (location.address, location.contact) == ("Praha 1", "Jan Novak")


def test_vat_return_line_adds_the_reverse_charge_flag():
    assert VATReturnLine.model_validate({"code": "1", "reverseCharge": True}).reverseCharge is True


def test_partner_carries_its_bank_accounts():
    partner = PartnerFull.model_validate(
        {
            "name": "Noname Ltd.",
            "ic": "12345678",
            "vat": "CZ12345678",
            "supplier": True,
            "mainAccount": {"accountNo": "123", "bankCode": "0800", "currency": "CZK"},
            "accounts": [{"iban": "CZ65 0800 0000 1920 0014 5399"}],
        }
    )

    assert partner.mainAccount.bankCode == "0800"
    assert partner.accounts[0].iban.startswith("CZ65")


def test_business_item_carries_its_price_and_unit():
    item = BusinessItemUpdateC.model_validate(
        {"code": "SVC-1", "unitPrice": 1500.5, "vatType": "Basic", "currency": "CZK", "sales": True}
    )

    assert (item.unitPrice, item.vatType) == (1500.5, "Basic")


def test_an_unexpected_field_still_reaches_the_caller():
    register = Register.model_validate({"code": "600", "surprise": 42})

    assert register.model_dump()["surprise"] == 42


PARTNERS_BODY = {
    "items": [
        {
            "id": "p-1",
            "externalId": "ERP-1",
            "name": "Noname Ltd.",
            "ic": "12345678",
            "supplier": True,
            "isValid": True,
        },
        {"id": "p-2", "name": "Retired s.r.o.", "isValid": False},
    ],
    "totalItems": 2,
    "pageSize": 20,
    "page": 0,
}


async def test_partners_are_returned_typed():
    client, _ = mock_wflow({"/api/acme/registers/partners": PARTNERS_BODY})

    result = await registers.list_register_partners(client, "acme")

    assert [p.name for p in result.items] == ["Noname Ltd.", "Retired s.r.o."]
    assert result.items[0].supplier is True


async def test_the_paging_envelope_survives_onto_the_result():
    client, _ = mock_wflow({"/api/acme/registers/partners": {"items": [{"name": "Noname Ltd."}], "totalItems": 137}})

    result = await registers.list_register_partners(client, "acme")

    assert result.totalItems == 137
    assert result.items[0].name == "Noname Ltd."
    assert "mainAccount" in type(result.items[0]).model_fields


async def test_the_paging_arguments_reach_wflow():
    client, requests = mock_wflow({"/api/acme/registers/partners": PARTNERS_BODY})

    await registers.list_register_partners(client, "acme", search="noname", sort="name asc", pageSize=50, page=0)

    params = requests[0].url.params
    assert params["search"] == "noname"
    assert params["sort"] == "name asc"
    assert params["pageSize"] == "50"
    assert params["page"] == "0"


async def test_unset_paging_arguments_are_not_sent():
    client, requests = mock_wflow({"/api/acme/registers/partners": PARTNERS_BODY})

    await registers.list_register_partners(client, "acme", search="noname")

    assert set(requests[0].url.params.keys()) == {"search"}


async def test_an_empty_register_is_an_empty_list_not_an_error():
    client, _ = mock_wflow({"/api/acme/registers/partners": {"items": [], "totalItems": 0}})

    result = await registers.list_register_partners(client, "acme")

    assert result.items == []


async def test_a_null_items_page_is_an_empty_list():
    client, _ = mock_wflow({"/api/acme/registers/partners": {"items": None, "totalItems": 0}})

    assert (await registers.list_register_partners(client, "acme")).items == []


async def test_a_bad_slug_names_itself():
    client, _ = mock_wflow({})

    with pytest.raises(WflowApiError, match="bad-slug"):
        await registers.list_register_partners(client, "bad-slug")


@pytest.mark.parametrize("slug", ["acme/../admin", "acme?x=1", "acme/registers", ""])
async def test_a_slug_that_would_rewrite_the_path_is_rejected(slug):
    client, requests = mock_wflow({})

    with pytest.raises(WflowError, match="should match pattern"):
        await registers.list_register_partners(client, slug)

    assert requests == []


SPECIFIC = [
    ("list_register_accounting_rules", "accountingrules", {"code": "5xx", "kind": "IncomingInvoice"}, "kind"),
    ("list_register_business_items", "businessitems", {"code": "SVC", "unitPrice": 100.0}, "unitPrice"),
    ("list_register_locations", "locations", {"code": "PRG", "address": "Praha 1"}, "address"),
    (
        "list_register_organization_persons",
        "organizationpersons",
        {"firstName": "Jan", "contractRole": "Sign"},
        "contractRole",
    ),
    ("list_register_partner_persons", "partnerpersons", {"firstName": "Eva", "partner": {"id": "p-1"}}, "partner"),
    ("list_register_payment_methods", "paymentmethods", {"code": "BANK", "kind": "IncomingInvoice"}, "kind"),
    ("list_register_series", "series", {"code": "FP", "invoiceType": "TaxInvoice"}, "invoiceType"),
    ("list_register_vat_return_lines", "vatreturnlines", {"code": "1", "reverseCharge": True}, "reverseCharge"),
]


@pytest.mark.parametrize("name,segment,item,field", SPECIFIC)
async def test_each_specific_register_parses_its_own_field(name, segment, item, field):
    client, requests = mock_wflow({f"/api/acme/registers/{segment}": {"items": [item], "totalItems": 1}})

    result = await getattr(registers, name)(client, "acme")

    assert requests[0].url.path == f"/api/acme/registers/{segment}"
    assert getattr(result.items[0], field) is not None
    assert field in type(result.items[0]).model_fields


async def test_a_partner_reference_parses_every_field_wflow_sends_on_a_read():
    partner = {
        "id": "p-1",
        "externalId": "ERP-1",
        "ic": "12345678",
        "vat": "CZ12345678",
        "name": "Noname Ltd.",
        "address": "Nadrazni 1, 602 00 Brno, CZ",
    }
    body = {"items": [{"id": "pp-1", "firstName": "Eva", "partner": partner}], "totalItems": 1}
    client, _ = mock_wflow({"/api/acme/registers/partnerpersons": body})

    result = await registers.list_register_partner_persons(client, "acme")

    assert result.items[0].partner.model_dump(exclude_none=True) == partner
    assert set(type(result.items[0].partner).model_fields) == set(partner)


async def test_a_business_item_parses_every_field_wflow_sends_on_a_read():
    item = {
        "id": "bi-1",
        "code": "SVC-1",
        "unitPrice": 1500.5,
        "updated": "2026-04-23T22:05:48.553",
        "category": {"id": "c-1", "externalId": "ERP-C", "code": "SRV", "description": "Services", "isValid": True},
        "measureUnit": {"id": "mu-1", "externalId": "ERP-H", "code": "hod", "description": "Hodina", "isValid": True},
    }
    client, _ = mock_wflow({"/api/acme/registers/businessitems": {"items": [item], "totalItems": 1}})

    result = await registers.list_register_business_items(client, "acme")

    parsed = result.items[0]
    assert parsed.model_dump(exclude_none=True) == item
    assert "updated" in type(parsed).model_fields
    assert set(type(parsed.category).model_fields) == set(item["category"])
    assert set(type(parsed.measureUnit).model_fields) == set(item["measureUnit"])


PLAIN = [
    ("list_register_activities", "activities"),
    ("list_register_business_cases", "businesscases"),
    ("list_register_business_item_categories", "businessitemcategories"),
    ("list_register_card_document_types", "carddocumenttypes"),
    ("list_register_cash_document_types", "cashdocumenttypes"),
    ("list_register_cash_registers", "cashregisters"),
    ("list_register_chart_of_accounts", "chartofaccounts"),
    ("list_register_contracts", "contracts"),
    ("list_register_cost_centers", "costcenters"),
    ("list_register_employees", "employees"),
    ("list_register_measure_units", "measureunits"),
    ("list_register_projects", "projects"),
    ("list_register_vat_control_statement_lines", "vatcontrolstatementlines"),
    ("list_register_vat_reverse_charge_codes", "vatreversechargecodes"),
    ("list_register_vehicles", "vehicles"),
]


@pytest.mark.parametrize("name,segment", PLAIN)
async def test_each_plain_register_calls_its_own_path(name, segment):
    body = {"items": [{"id": "x-1", "code": "A", "description": "First", "isValid": True}], "totalItems": 1}
    client, requests = mock_wflow({f"/api/acme/registers/{segment}": body})

    result = await getattr(registers, name)(client, "acme")

    assert requests[0].url.path == f"/api/acme/registers/{segment}"
    assert result.items[0].code == "A"
    assert set(type(result.items[0]).model_fields) == {"id", "externalId", "code", "description", "isValid"}


READS = sorted(name for name in vars(registers) if name.startswith("list_register_"))


def test_all_twenty_four_register_reads_exist():
    assert len(READS) == 24


@pytest.mark.parametrize("name", READS)
def test_every_register_read_takes_the_five_paging_arguments(name):
    assert list(inspect.signature(getattr(registers, name)).parameters) == [
        "client",
        "organization",
        "search",
        "sort",
        "query",
        "pageSize",
        "page",
    ]


def register_template(fn) -> tuple[str, str]:
    """The body, docstring dropped, with its path segment and model name masked."""
    source = body_source(fn)
    (model,) = re.findall(r"Paged\[(\w+)\]", source)
    (segment,) = re.findall(r"/registers/(\w+)", source)
    return source.replace(model, "MODEL").replace(segment, "SEGMENT"), model


@pytest.mark.parametrize("name", READS)
def test_every_register_read_is_the_same_template(name):
    reference, _ = register_template(registers.list_register_partners)
    fn = getattr(registers, name)
    body, model = register_template(fn)

    assert body == reference, f"{name} drifted from the list_register_partners template:\n{body}"
    (returned,) = inspect.signature(fn).return_annotation.__pydantic_generic_metadata__["args"]
    assert inspect.unwrap(fn).__globals__[model] is returned, (
        f"{name} returns {returned.__name__} but validates {model}"
    )
    assert inspect.signature(fn).return_annotation.__pydantic_generic_metadata__["origin"] is Paged
