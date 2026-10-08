from tests.helpers import mock_wflow
from wflow_api.operations import organization

ORG_BODY = {
    "id": "o-1",
    "name": "Noname Ltd.",
    "organizationUrlPart": "nonameorg",
    "vatCountry": "CZ",
    "vatNonPayer": False,
    "allowSupportAccess": True,
    "trialExpiration": None,
}
SETTINGS_BODY = {
    "name": "Noname Ltd.",
    "vatCountry": "CZ",
    "vatNonPayer": False,
    "defaultLanguage": "cs",
    "processIsdoc": True,
    "fiscalYearStart": 1,
}


async def test_the_current_organization_is_returned_typed():
    client, _ = mock_wflow({"/api/acme/organization": ORG_BODY})

    result = await organization.get_organization(client, "acme")

    assert result.name == "Noname Ltd."
    assert result.vatCountry == "CZ"


async def test_the_settings_are_a_different_endpoint():
    client, requests = mock_wflow({"/api/acme/organization/settings": SETTINGS_BODY})

    result = await organization.get_organization_settings(client, "acme")

    assert requests[0].url.path == "/api/acme/organization/settings"
    assert result.defaultLanguage == "cs"


async def test_an_unknown_settings_field_still_reaches_the_caller():
    client, _ = mock_wflow({"/api/acme/organization/settings": SETTINGS_BODY | {"newToggle": True}})

    result = await organization.get_organization_settings(client, "acme")

    assert result.model_dump(mode="json")["newToggle"] is True
