import pytest

from tests.helpers import ACCOUNT_BODY, ORGS_BODY, mock_response, mock_wflow
from wflow_api.errors import WflowApiError, WflowError
from wflow_api.models import OrganizationDomain
from wflow_api.operations import account, operations


async def test_get_me_reads_the_org_scoped_account_with_the_clients_bearer():
    client, requests = mock_response(200, json=ACCOUNT_BODY)

    result = await account.get_me(client, "produkt-testovaci")

    assert result.identity.login == ACCOUNT_BODY["identity"]["login"]
    (sent,) = requests
    assert sent.url.path == "/api/produkt-testovaci/account"
    assert sent.headers["authorization"] == "Bearer test-token"


async def test_404_names_the_slug():
    client, _ = mock_response(404, json={"title": "Not Found"})

    with pytest.raises(WflowApiError, match="bad-slug"):
        await account.get_me(client, "bad-slug")


async def test_200_with_null_body_is_not_reported_as_an_account():
    client, _ = mock_response(200, content=b"null")

    with pytest.raises(WflowError, match="empty account") as refused:
        await account.get_me(client, "data-test")

    assert "list_organizations" in str(refused.value)


async def test_list_organizations_needs_no_org_argument():
    client, requests = mock_wflow({"/api/user/myorganizations": ORGS_BODY})

    result = await account.list_organizations(client)

    assert [org.subdomain for org in result] == ["data-test"]
    assert requests[-1].url.path == "/api/user/myorganizations"
    assert requests[-1].headers["authorization"] == "Bearer test-token"


async def test_the_response_is_typed_not_a_bare_dict():
    client, _ = mock_response(200, json=ACCOUNT_BODY)

    result = await account.get_me(client, "produkt-testovaci")

    assert result.hasFullAccess is True
    assert result.rights == ["CanApprove", "CanCreateDocument"]
    assert result.documentTypes[0].documentType.kind == "IncomingInvoice"
    assert result.documentTypes[0].permission == "OnlyAssigned"
    assert result.teams[0].system is False


async def test_a_field_wflow_adds_later_is_not_dropped():
    client, _ = mock_response(200, json=ACCOUNT_BODY | {"somethingNew": "keep me"})

    result = await account.get_me(client, "produkt-testovaci")

    assert result.model_dump(mode="json")["somethingNew"] == "keep me"


async def test_missing_fields_do_not_break_the_call():
    client, _ = mock_response(200, json={"id": "u-1"})

    result = await account.get_me(client, "produkt-testovaci")

    assert result.id == "u-1"
    assert result.rights is None


async def test_list_organizations_returns_the_domain_shape():
    client, _ = mock_wflow({"/api/user/myorganizations": ORGS_BODY})

    result = await account.list_organizations(client)

    assert isinstance(result[0], OrganizationDomain)
    assert result[0].subdomain == "data-test"


@pytest.mark.parametrize("body", [42, "data-test", True])
async def test_a_scalar_where_the_organizations_belong_is_a_wflow_error(body):
    client, _ = mock_response(200, json=body)

    with pytest.raises(WflowError, match=r"myorganizations returned .*not an array"):
        await account.list_organizations(client)


def test_operations_lists_only_what_each_module_defines():
    found = operations()
    names = [fn.__name__ for _, fn in found]

    assert ("account", account.get_me) in found
    assert "current_account" not in names
    assert len(names) == len(set(names))
    assert found == sorted(found, key=lambda pair: (pair[0], pair[1].__name__))
    for module, fn in found:
        assert fn.__module__ == f"wflow_api.operations.{module}"
