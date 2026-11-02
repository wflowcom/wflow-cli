"""Roles, Teams and Users tags: who exists in the workspace, and what they may do."""

from wflow_api.client import WflowClient
from wflow_api.guards import path_segment, query_params, write_json
from wflow_api.models import (
    OrgSlug,
    Page,
    Paged,
    PageSize,
    Query,
    Role,
    RoleBase,
    RoleUpdate,
    Search,
    Sort,
    Team,
    TeamBase,
    TeamUpdate,
    User,
    UserFull,
    UserUpdate,
    WriteResult,
)
from wflow_api.operation import operation


@operation
async def list_roles(
    client: WflowClient,
    organization: OrgSlug,
    search: Search = None,
    sort: Sort = None,
    query: Query = None,
    pageSize: PageSize = None,
    page: Page = None,
) -> Paged[RoleBase]:
    """Roles configured in the workspace — named bundles of rights assignable to users.

    Fields:

    - `id` — pass to `get_role`
    - `name`, `description`
    """
    payload = await client.request(
        "GET",
        f"/api/{organization}/roles",
        params=query_params(search=search, sort=sort, query=query, pageSize=pageSize, page=page),
    )
    return Paged[RoleBase].model_validate(payload or {})


@operation
async def get_role(client: WflowClient, organization: OrgSlug, id: str) -> Role:
    """One role in full, by its role id.

    Get the id from `list_roles`.

    Fields: beyond those on the list summary —

    - `users` — each user holding this role, as an id and identity
    - `rights` — the permission strings this role grants, e.g. CanApprove,
      CanCreateDocument, CanManageSettings
    """
    payload = await client.request("GET", f"/api/{organization}/roles/{path_segment(id)}") or {}
    return Role.model_validate(payload)


@operation
async def list_teams(
    client: WflowClient,
    organization: OrgSlug,
    search: Search = None,
    sort: Sort = None,
    query: Query = None,
    pageSize: PageSize = None,
    page: Page = None,
) -> Paged[TeamBase]:
    """Teams configured in the workspace — groups of users assignable to approval steps.

    Fields:

    - `id` — pass to `get_team`
    - `name`, `description`
    - `system` — true for a built-in team rather than one the organization created
    """
    payload = await client.request(
        "GET",
        f"/api/{organization}/teams",
        params=query_params(search=search, sort=sort, query=query, pageSize=pageSize, page=page),
    )
    return Paged[TeamBase].model_validate(payload or {})


@operation
async def get_team(client: WflowClient, organization: OrgSlug, id: str) -> Team:
    """One team in full, by its team id.

    Get the id from `list_teams`.

    Fields: beyond those on the list summary —

    - `users` — each member, as an id and identity
    """
    payload = await client.request("GET", f"/api/{organization}/teams/{path_segment(id)}") or {}
    return Team.model_validate(payload)


@operation
async def list_users(
    client: WflowClient,
    organization: OrgSlug,
    search: Search = None,
    sort: Sort = None,
    query: Query = None,
    pageSize: PageSize = None,
    page: Page = None,
) -> Paged[User]:
    """The people with access to this workspace.

    `get_me` answers this for the signed-in user only. Use this to see everyone, for
    example to work out who can approve a document that is waiting. For one user's
    role, team and per-document-type permissions, follow up with `get_user`.

    Fields:

    - `id` — pass to `get_user`
    - `identity` — login, first/last/full name and preferred language
    - `created` — when the account was created
    - `hasFullAccess` — full-access role indicator, which overrides per-type detail
    """
    payload = await client.request(
        "GET",
        f"/api/{organization}/users",
        params=query_params(search=search, sort=sort, query=query, pageSize=pageSize, page=page),
    )
    return Paged[User].model_validate(payload or {})


@operation
async def get_user(client: WflowClient, organization: OrgSlug, userId: str) -> UserFull:
    """One user in full, by their user id.

    Get the id from `list_users`. Same shape `get_me` returns for the signed-in user.

    Fields: beyond those on the list summary —

    - `roles`, `teams` — memberships
    - `documentTypes` — per document type: All, OnlyAssigned or FullAccess
    - `rights` — named rights held here, e.g. CanApprove, CanCreateDocument
    """
    payload = await client.request("GET", f"/api/{organization}/users/{path_segment(userId)}") or {}
    return UserFull.model_validate(payload)


@operation
async def delete_role(client: WflowClient, organization: OrgSlug, id: str) -> WriteResult:
    """Delete one role from the workspace.

    A role carries rights and holders. `get_role` lists both — read it first, because
    everyone under `users` loses what the role granted them.

    Fields: on the result —

    - `action` — "deleted"
    - `resource` — "roles"
    """
    await client.request("DELETE", f"/api/{organization}/roles/{path_segment(id)}")
    return WriteResult(action="deleted", resource="roles")


@operation
async def delete_team(client: WflowClient, organization: OrgSlug, id: str) -> WriteResult:
    """Delete one team from the workspace.

    Teams are what approval templates and document rights are assigned to, so a team in
    use is referenced well beyond its own record. `get_team` lists its members; system
    teams, flagged `system` by `list_teams`, are wflow's own rather than the
    organization's.

    Fields: on the result —

    - `action` — "deleted"
    - `resource` — "teams"
    """
    await client.request("DELETE", f"/api/{organization}/teams/{path_segment(id)}")
    return WriteResult(action="deleted", resource="teams")


@operation
async def delete_user(client: WflowClient, organization: OrgSlug, userId: str) -> WriteResult:
    """Remove one person's access to this workspace.

    Get the id from `list_users`; `get_user` shows the roles, teams and document-type
    permissions that go with them, which is what this takes away.

    Fields: on the result —

    - `action` — "deleted"
    - `resource` — "users"
    """
    await client.request("DELETE", f"/api/{organization}/users/{path_segment(userId)}")
    return WriteResult(action="deleted", resource="users")


@operation
async def create_role(client: WflowClient, organization: OrgSlug, role: RoleUpdate) -> WriteResult:
    """Create a role — a named bundle of rights that users and teams can be given.

    Use `list_roles` first to check the name is not already taken; this creates rather
    than upserts, so a duplicate name gives you two roles that look alike. `users` is a
    list of user ids, from `list_users`.

    Fields: on the result —

    - `action` — "created"
    - `resource` — "roles"
    - `id` — the new role's id
    """
    created = await client.request("POST", f"/api/{organization}/roles", json=write_json(role))
    return WriteResult(action="created", resource="roles", id=created)


@operation
async def create_team(client: WflowClient, organization: OrgSlug, team: TeamUpdate) -> WriteResult:
    """Create a team — the group approval steps and document rights are assigned to.

    Use `list_teams` first to check the name is not already taken; this creates rather
    than upserts, so a duplicate name gives you two teams that look alike. `users` is a
    list of user ids, from `list_users`.

    Fields: on the result —

    - `action` — "created"
    - `resource` — "teams"
    - `id` — the new team's id
    """
    created = await client.request("POST", f"/api/{organization}/teams", json=write_json(team))
    return WriteResult(action="created", resource="teams", id=created)


@operation
async def update_role(client: WflowClient, organization: OrgSlug, id: str, role: RoleUpdate) -> WriteResult:
    """Replace one role's name, description, holders and rights.

    The submitted object replaces the stored role, so a field you leave out can be
    cleared. `users` and `rights` are whole sets: a holder you omit loses the role, and a
    right you omit is taken off everyone who holds it. `get_role` returns both lists in
    full — read it first and send back everything you mean to keep, `users` as the `id` of
    each holder it lists. Get the role id from `list_roles`.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "roles"
    - `id` — the role's id
    """
    updated = await client.request("PUT", f"/api/{organization}/roles/{path_segment(id)}", json=write_json(role))
    return WriteResult(action="updated", resource="roles", id=updated)


@operation
async def update_team(client: WflowClient, organization: OrgSlug, id: str, team: TeamUpdate) -> WriteResult:
    """Replace one team's name, description and membership.

    Send the name and description along with the membership: a `description` you leave
    out is cleared, not kept, so the full record is the only correct payload. `users` is a
    whole set: a member you omit is removed from the team, and with it from every
    approval step and document right the team carries. `get_team` returns the membership
    in full — read it first and send back everyone you mean to keep, as the `id` of each
    member it lists. Get the team id from `list_teams`.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "teams"
    - `id` — the team's id
    """
    updated = await client.request("PUT", f"/api/{organization}/teams/{path_segment(id)}", json=write_json(team))
    return WriteResult(action="updated", resource="teams", id=updated)


@operation
async def update_user(client: WflowClient, organization: OrgSlug, user: UserUpdate) -> WriteResult:
    """Add a person to this workspace, or replace what an existing person may do.

    The person is matched by `login`: if no one in this workspace has it, they are added;
    if someone does, their record is replaced by what you send. Either way the result says
    `"updated"`, so it does not tell you which happened — call `get_user` or `list_users`
    first if that matters.

    `roles`, `teams` and `documentTypes` are whole sets: a membership you leave out is taken
    away, and omitting `documentTypes` can leave the person able to see nothing. Send the
    rest of the record too: whether a field you omit is kept or cleared is not guaranteed.

    To change an existing person, read them with `get_user` first and send back everything
    you mean to keep. It returns the same data in its own shape: `roles` and `teams` are
    `{"id": …}` references, `documentTypes` is `{"id": …, "permission": …}`, and `login`
    is the one inside its `identity`.

    Fields: on the result —

    - `action` — "updated", whether the person was added or changed
    - `resource` — "users"
    - `id` — the user's id
    """
    updated = await client.request("PUT", f"/api/{organization}/users", json=write_json(user))
    return WriteResult(action="updated", resource="users", id=updated)
