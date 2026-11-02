"""The CLI's identity comes from the environment and nowhere else."""

import os
from collections.abc import Mapping

from wflow_api import ENVIRONMENTS, ClientCredentials, WflowClient
from wflow_cli import __version__

HEADERS = {"X-Client-Id": "wflowinternal", "X-Integration-Id": "wflow_cli", "X-Integration-Version": __version__}
REQUIRED = ("WFLOW_CLIENT_ID", "WFLOW_CLIENT_SECRET")


class ConfigError(Exception):
    """The environment does not say how to reach wflow."""


def client_from_env(environ: Mapping[str, str] | None = None) -> WflowClient:
    env = os.environ if environ is None else environ
    values = {name: env.get(name, "").strip() for name in REQUIRED}
    if missing := [name for name, value in values.items() if not value]:
        raise ConfigError(
            f"{' and '.join(missing)} must be set. Create an API client with the client_credentials grant "
            "in admin.wflow.com, then allow it in each workspace under Settings → Integrations → API accesses."
        )
    name = env.get("WFLOW_ENV", "").strip().lower() or "prod"
    if name not in ENVIRONMENTS:
        raise ConfigError(f"WFLOW_ENV={name!r} is not one of: {', '.join(sorted(ENVIRONMENTS))}.")
    api_base, account_base = ENVIRONMENTS[name]
    token = ClientCredentials(
        values["WFLOW_CLIENT_ID"],
        values["WFLOW_CLIENT_SECRET"],
        env.get("WFLOW_ACCOUNT_BASE", "").strip() or account_base,
    )
    return WflowClient(token, api_base=env.get("WFLOW_API_BASE", "").strip() or api_base, headers=HEADERS)
