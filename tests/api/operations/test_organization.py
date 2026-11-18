import inspect

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


async def test_the_organization_carries_its_limit_and_peppol_verification():
    limit = {"documentsPerMonth": 100, "period": 3, "validFrom": "2026-01-01"}
    client, _ = mock_wflow({"/api/acme/organization": ORG_BODY | {"peppolVerified": True, "limit": limit}})

    result = await organization.get_organization(client, "acme")

    assert result.peppolVerified is True
    assert result.limit is not None
    assert result.limit.documentsPerMonth == 100
    assert result.limit.period == 3
    assert result.limit.validFrom is not None and result.limit.validFrom.year == 2026
    assert not result.model_extra
    assert not result.limit.model_extra


async def test_an_unlimited_organization_has_no_limit():
    client, _ = mock_wflow({"/api/acme/organization": ORG_BODY | {"limit": None}})

    result = await organization.get_organization(client, "acme")

    assert result.limit is None


async def test_the_settings_carry_the_print_theme_and_colour():
    client, _ = mock_wflow(
        {"/api/acme/organization/settings": SETTINGS_BODY | {"printThemeId": "modern", "printColor": "#1A2B3C"}}
    )

    result = await organization.get_organization_settings(client, "acme")

    assert result.printThemeId == "modern"
    assert result.printColor == "#1A2B3C"
    assert not result.model_extra


def test_the_organization_explains_its_limit_window():
    description = " ".join((inspect.getdoc(organization.get_organization) or "").split())

    assert (
        "`limit` — the workspace's document limit; null means unlimited. The workspace gets `documentsPerMonth` "
        "times `period` documents per window, `period` is in months, and the windows run back to back from "
        "`validFrom`"
    ) in description
    assert "`peppolVerified` — wflow has verified the workspace for Peppol" in description


def test_the_settings_explain_the_print_theme_and_colour():
    description = " ".join((inspect.getdoc(organization.get_organization_settings) or "").split())

    assert (
        "`printThemeId` — the theme the PDF engine prints the workspace's documents with; null keeps them on the "
        "legacy print"
    ) in description
    assert "`printColor` — the accent colour of printed documents, as `#RRGGBB`" in description
