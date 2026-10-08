import inspect
import json
import re
import typing

import pytest

from tests.helpers import body_source, mock_wflow
from wflow_api.errors import WflowApiError, WflowError
from wflow_api.operations import registers

PARTNER = {"externalId": "ERP-1", "name": "Noname Ltd.", "ic": "12345678", "supplier": True}


async def test_an_update_sends_the_records_as_a_json_array():
    client, requests = mock_wflow({"/api/acme/registers/partners": None})

    result = await registers.update_register_partners(client, "acme", [PARTNER])

    assert requests[0].method == "PUT"
    assert json.loads(requests[0].content) == [PARTNER]
    assert result.action == "updated"
    assert result.resource == "registers/partners"


async def test_unset_fields_are_not_serialised_as_null():
    client, requests = mock_wflow({"/api/acme/registers/partners": None})

    await registers.update_register_partners(client, "acme", [{"name": "Only a name"}])

    assert json.loads(requests[0].content) == [{"name": "Only a name"}]


async def test_several_records_go_in_one_call():
    client, requests = mock_wflow({"/api/acme/registers/partners": None})

    await registers.update_register_partners(client, "acme", [PARTNER, {"name": "Second"}])

    assert len(json.loads(requests[0].content)) == 2


async def test_a_rejected_write_surfaces_the_reason():
    client, _ = mock_wflow({}, status=400)

    with pytest.raises(WflowApiError, match="Rejected"):
        await registers.update_register_partners(client, "acme", [PARTNER])


async def test_an_empty_payload_is_refused():
    client, requests = mock_wflow({"/api/acme/registers/partners": None})

    with pytest.raises(WflowError, match="isValid: false"):
        await registers.update_register_partners(client, "acme", [])

    assert requests == []


async def test_a_misspelt_field_is_refused_instead_of_being_dropped_upstream():
    client, requests = mock_wflow({"/api/acme/registers/partners": None})

    with pytest.raises(WflowError, match=r"\[0\]\.descr") as refused:
        await registers.update_register_partners(client, "acme", [{"name": "N", "descr": "typo"}])

    assert "the model declares" in str(refused.value)
    assert requests == []


async def test_the_refusal_names_every_unknown_field_and_which_record_it_is_on():
    client, _ = mock_wflow({"/api/acme/registers/partners": None})

    with pytest.raises(WflowError) as refused:
        await registers.update_register_partners(
            client, "acme", [{"name": "First"}, {"nme": "Second", "suplier": True}]
        )

    assert "[1].nme" in str(refused.value)
    assert "[1].suplier" in str(refused.value)


async def test_a_misspelt_field_inside_a_nested_object_is_refused():
    client, requests = mock_wflow({"/api/acme/registers/partners": None})

    with pytest.raises(WflowError, match=r"mainAddress\.citty"):
        await registers.update_register_partners(
            client, "acme", [{"name": "N", "mainAddress": {"city": "Brno", "citty": "Brno"}}]
        )

    assert requests == []


async def test_a_misspelt_field_inside_a_list_of_nested_objects_is_refused():
    client, requests = mock_wflow({"/api/acme/registers/partners": None})

    with pytest.raises(WflowError, match=r"accounts\[1\]\.ibn"):
        await registers.update_register_partners(client, "acme", [{"accounts": [{"iban": "CZ1"}, {"ibn": "CZ2"}]}])

    assert requests == []


async def test_nested_records_that_are_spelt_right_reach_wflow_whole():
    client, requests = mock_wflow({"/api/acme/registers/partners": None})
    partner = {
        "name": "Noname Ltd.",
        "mainAddress": {"city": "Brno", "countryCode": "CZ"},
        "mainAccount": {"iban": "CZ1"},
        "accounts": [{"iban": "CZ2"}, {"iban": "CZ3"}],
        "peppolIds": [{"peppolId": "0088:123", "isDefault": True}],
    }

    await registers.update_register_partners(client, "acme", [partner])

    assert json.loads(requests[0].content) == [partner]


async def test_a_partner_person_as_wflow_sends_it_survives_its_own_round_trip():
    client, requests = mock_wflow({"/api/acme/registers/partnerpersons": None})
    person = {
        "id": "pp-1",
        "firstName": "Eva",
        "lastName": "Nováková",
        "partner": {
            "id": "p-1",
            "externalId": "ERP-1",
            "ic": "12345678",
            "vat": "CZ12345678",
            "name": "Noname Ltd.",
            "address": "Nádražní 1, 602 00 Brno, CZ",
        },
    }

    await registers.update_register_partner_persons(client, "acme", [person])

    assert json.loads(requests[0].content) == [person]


async def test_a_business_item_as_wflow_sends_it_survives_its_own_round_trip():
    client, requests = mock_wflow({"/api/acme/registers/businessitems": None})
    item = {
        "id": "bi-1",
        "externalId": "ERP-7",
        "code": "SVC-1",
        "description": "Consulting hour",
        "isValid": True,
        "unitPrice": 1500.5,
        "vatType": "Basic",
        "currency": "CZK",
        "purchase": False,
        "sales": True,
        "updated": "2026-04-23T22:05:48.553",
        "category": {"id": "c-1", "externalId": "ERP-C", "code": "SRV", "description": "Services", "isValid": True},
        "partner": {
            "id": "p-1",
            "externalId": "ERP-1",
            "ic": "12345678",
            "vat": "CZ12345678",
            "name": "Noname Ltd.",
            "address": "Nádražní 1, 602 00 Brno, CZ",
        },
        "measureUnit": {"id": "mu-1", "externalId": "ERP-H", "code": "hod", "description": "Hodina", "isValid": True},
    }

    await registers.update_register_business_items(client, "acme", [item])

    assert json.loads(requests[0].content) == [item]


UPDATE_OPERATIONS = [
    ("update_register_accounting_rules", "accountingrules", "accountingRules"),
    ("update_register_activities", "activities", "activities"),
    ("update_register_business_cases", "businesscases", "businessCases"),
    ("update_register_business_item_categories", "businessitemcategories", "businessItemCategories"),
    ("update_register_business_items", "businessitems", "businessItems"),
    ("update_register_card_document_types", "carddocumenttypes", "cardDocumentTypes"),
    ("update_register_cash_document_types", "cashdocumenttypes", "cashDocumentTypes"),
    ("update_register_cash_registers", "cashregisters", "cashRegisters"),
    ("update_register_chart_of_accounts", "chartofaccounts", "accounts"),
    ("update_register_contracts", "contracts", "contracts"),
    ("update_register_cost_centers", "costcenters", "costCenters"),
    ("update_register_employees", "employees", "employees"),
    ("update_register_locations", "locations", "locations"),
    ("update_register_measure_units", "measureunits", "measureUnits"),
    ("update_register_organization_persons", "organizationpersons", "persons"),
    ("update_register_partner_persons", "partnerpersons", "persons"),
    ("update_register_payment_methods", "paymentmethods", "paymentMethods"),
    ("update_register_projects", "projects", "projects"),
    ("update_register_series", "series", "series"),
    ("update_register_vat_control_statement_lines", "vatcontrolstatementlines", "lines"),
    ("update_register_vat_return_lines", "vatreturnlines", "lines"),
    ("update_register_vat_reverse_charge_codes", "vatreversechargecodes", "codes"),
    ("update_register_vehicles", "vehicles", "vehicles"),
]


@pytest.mark.parametrize("name,segment,argument", UPDATE_OPERATIONS)
async def test_each_update_puts_to_its_own_path(name, segment, argument):
    client, requests = mock_wflow({f"/api/acme/registers/{segment}": None})

    result = await getattr(registers, name)(client, "acme", **{argument: [{"externalId": "X-1"}]})

    assert requests[0].method == "PUT"
    assert requests[0].url.path == f"/api/acme/registers/{segment}"
    assert result.resource == f"registers/{segment}"


WRITES = sorted(name for name in vars(registers) if name.startswith(("update_register_", "patch_register_")))
EXPECTED_WRITES = 48


def test_the_register_write_count():
    assert len(WRITES) == EXPECTED_WRITES, WRITES


def list_argument(fn) -> inspect.Parameter:
    (parameter,) = [p for p in inspect.signature(fn).parameters.values() if p.name not in ("client", "organization")]
    return parameter


def write_template(name: str) -> str:
    """The body with its list argument and its path segment masked."""
    fn = getattr(registers, name)
    body = re.sub(rf"\b{re.escape(list_argument(fn).name)}\b", "ITEMS", body_source(fn))
    return re.sub(r"registers/\w+", "registers/SEGMENT", body)


@pytest.mark.parametrize("name", WRITES)
def test_every_register_write_is_the_same_template(name):
    reference = "update_register_partners" if name.startswith("update_") else "patch_register_partners"
    body = write_template(name)
    assert body == write_template(reference), f"{name} drifted from the {reference} template:\n{body}"

    read = getattr(registers, f"list_register_{name.split('_', 2)[2]}")
    (sent,) = typing.get_args(list_argument(getattr(registers, name)).annotation)
    (returned,) = inspect.signature(read).return_annotation.__pydantic_generic_metadata__["args"]
    assert sent is returned, f"{name} takes {sent.__name__} but its read returns {returned.__name__}"


def written_segment(name: str) -> str:
    (segment,) = re.findall(r"\{organization\}/registers/(\w+)", body_source(getattr(registers, name)))
    return segment


@pytest.mark.parametrize("name", WRITES)
def test_the_written_path_and_the_reported_resource_agree(name):
    (reported,) = re.findall(r"resource='registers/(\w+)'", body_source(getattr(registers, name)))
    assert written_segment(name) == reported, f"{name} writes registers/{written_segment(name)} but reports {reported}"


DOCSTRING_ANCHORS = {
    "update_register_": ("marked invalid", "totalItems", "default"),
    "patch_register_": ("retire", "isValid", "default"),
}


@pytest.mark.parametrize("name", WRITES)
def test_every_write_says_what_happens_to_the_records_you_leave_out(name):
    ((prefix, anchors),) = [item for item in DOCSTRING_ANCHORS.items() if name.startswith(item[0])]
    description = " ".join((inspect.getdoc(getattr(registers, name)) or "").split())
    for anchor in anchors:
        assert anchor in description, (
            f"{name} never says {anchor!r}; every {prefix}* docstring carries all of {anchors}"
        )


async def test_a_patch_uses_the_patch_verb():
    client, requests = mock_wflow({"/api/acme/registers/partners": None})

    result = await registers.patch_register_partners(client, "acme", [PARTNER])

    assert requests[0].method == "PATCH"
    assert json.loads(requests[0].content) == [PARTNER]
    assert result.action == "patched"


async def test_an_empty_payload_is_refused_on_a_patch_too():
    client, requests = mock_wflow({"/api/acme/registers/partners": None})

    with pytest.raises(WflowError, match="patch_register_"):
        await registers.patch_register_partners(client, "acme", [])

    assert requests == []


PATCH_OPERATIONS = [
    (name.replace("update_", "patch_"), segment, argument) for name, segment, argument in UPDATE_OPERATIONS
]


@pytest.mark.parametrize("name,segment,argument", PATCH_OPERATIONS)
async def test_each_patch_patches_its_own_path(name, segment, argument):
    client, requests = mock_wflow({f"/api/acme/registers/{segment}": None})

    result = await getattr(registers, name)(client, "acme", **{argument: [{"id": "x-1", "externalId": "X-1"}]})

    assert requests[0].method == "PATCH"
    assert requests[0].url.path == f"/api/acme/registers/{segment}"
    assert result.action == "patched"


@pytest.mark.parametrize("name", [name for name in WRITES if name.startswith("patch_register_")])
def test_a_patch_writes_the_same_segment_as_its_update(name):
    twin = name.replace("patch_", "update_", 1)
    assert written_segment(name) == written_segment(twin), (
        f"{name} writes registers/{written_segment(name)} but {twin} writes registers/{written_segment(twin)}"
    )
