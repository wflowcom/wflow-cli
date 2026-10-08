import json

import pytest

from tests.helpers import mock_wflow
from wflow_api.models.account import UserFull
from wflow_api.models.admin import Role, Team
from wflow_api.models.requests import IdType, RoleUpdate
from wflow_api.operations import admin


def test_a_role_carries_its_rights():
    role = Role.model_validate({"id": "r-1", "name": "Approver", "rights": ["CanApprove"]})

    assert (role.name, role.rights) == ("Approver", ["CanApprove"])


def test_a_team_knows_whether_it_is_built_in():
    assert Team.model_validate({"id": "t-1", "name": "Finance", "system": False}).system is False


def test_a_user_full_carries_its_identity_login():
    user = UserFull.model_validate({"id": "u-1", "identity": {"login": "jan@acme.cz"}, "hasFullAccess": False})

    assert user.identity.login == "jan@acme.cz"


def test_id_type_is_the_rights_payload():
    assert IdType.model_validate({"id": "t-1"}).id == "t-1"
    assert IdType.model_validate({}).model_dump() == {"id": None}


def test_a_role_update_carries_its_rights():
    role = RoleUpdate.model_validate({"name": "Approver", "rights": ["CanApprove"]})

    assert role.model_dump() == {"name": "Approver", "description": None, "users": None, "rights": ["CanApprove"]}


COLLECTIONS = [
    (
        "list_roles",
        "/api/acme/roles",
        {"items": [{"id": "r-1", "name": "Approver"}], "totalItems": 1},
        lambda result: result.items[0].name == "Approver",
    ),
    (
        "list_teams",
        "/api/acme/teams",
        {"items": [{"id": "t-1", "name": "Finance", "system": False}], "totalItems": 1},
        lambda result: result.items[0].system is False,
    ),
    (
        "list_users",
        "/api/acme/users",
        {"items": [{"id": "u-1", "identity": {"login": "jan@acme.cz"}}], "totalItems": 1},
        lambda result: result.items[0].identity.login == "jan@acme.cz",
    ),
]


@pytest.mark.parametrize("name,path,body,check", COLLECTIONS)
async def test_the_admin_collections(name, path, body, check):
    client, requests = mock_wflow({path: body})

    result = await getattr(admin, name)(client, "acme", search="Fin", pageSize=5)

    assert requests[0].url.path == path
    assert dict(requests[0].url.params) == {"search": "Fin", "pageSize": "5"}
    assert check(result)


SINGLES = [
    (
        "get_role",
        "/api/acme/roles/r-1",
        "id",
        {"id": "r-1", "name": "Approver"},
        lambda result: result.name == "Approver",
    ),
    (
        "get_team",
        "/api/acme/teams/t-1",
        "id",
        {"id": "t-1", "name": "Finance"},
        lambda result: result.name == "Finance",
    ),
    (
        "get_user",
        "/api/acme/users/u-1",
        "userId",
        {"id": "u-1", "hasFullAccess": True},
        lambda result: result.hasFullAccess,
    ),
]


@pytest.mark.parametrize("name,path,argument,body,check", SINGLES)
async def test_the_admin_singles(name, path, argument, body, check):
    client, requests = mock_wflow({path: body})

    result = await getattr(admin, name)(client, "acme", **{argument: path.rsplit("/", 1)[-1]})

    assert requests[0].url.path == path
    assert check(result)


DELETES = [
    ("delete_role", {"id": "r-1"}, "/api/acme/roles/r-1", "roles"),
    ("delete_team", {"id": "t-1"}, "/api/acme/teams/t-1", "teams"),
    ("delete_user", {"userId": "u-1"}, "/api/acme/users/u-1", "users"),
]


@pytest.mark.parametrize("name,arguments,path,resource", DELETES)
async def test_each_delete_hits_its_own_path(name, arguments, path, resource):
    client, requests = mock_wflow({path: None})

    result = await getattr(admin, name)(client, "acme", **arguments)

    assert requests[0].method == "DELETE"
    assert requests[0].url.path == path
    assert (result.action, result.resource) == ("deleted", resource)


BODY_WRITES = [
    (
        "create_role",
        {"role": {"name": "Approver"}},
        "POST",
        "/api/acme/roles",
        {"name": "Approver"},
        ("created", "roles"),
    ),
    (
        "create_team",
        {"team": {"name": "Finance"}},
        "POST",
        "/api/acme/teams",
        {"name": "Finance"},
        ("created", "teams"),
    ),
    (
        "update_role",
        {"id": "r-1", "role": {"name": "Approver"}},
        "PUT",
        "/api/acme/roles/r-1",
        {"name": "Approver"},
        ("updated", "roles"),
    ),
    (
        "update_team",
        {"id": "t-1", "team": {"name": "Finance"}},
        "PUT",
        "/api/acme/teams/t-1",
        {"name": "Finance"},
        ("updated", "teams"),
    ),
    (
        "update_user",
        {"user": {"login": "jan@acme.cz"}},
        "PUT",
        "/api/acme/users",
        {"login": "jan@acme.cz"},
        ("updated", "users"),
    ),
]


@pytest.mark.parametrize("name,arguments,method,path,body,outcome", BODY_WRITES)
async def test_each_body_write_sends_its_own_payload(name, arguments, method, path, body, outcome):
    client, requests = mock_wflow({path: "new-id"})

    result = await getattr(admin, name)(client, "acme", **arguments)

    assert requests[0].method == method
    assert requests[0].url.path == path
    assert json.loads(requests[0].content) == body
    assert (result.action, result.resource, result.id) == (*outcome, "new-id")


async def test_a_created_record_returns_its_new_id():
    client, _ = mock_wflow({"/api/acme/roles": "r-new"})

    result = await admin.create_role(client, "acme", {"name": "Approver"})

    assert (result.action, result.id) == ("created", "r-new")
