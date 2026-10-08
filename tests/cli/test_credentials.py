import pytest

from wflow_api import ClientCredentials
from wflow_cli import __version__
from wflow_cli.credentials import HEADERS, ConfigError, client_from_env

CREDENTIALS = {"WFLOW_CLIENT_ID": "acme_client", "WFLOW_CLIENT_SECRET": "s3cret"}


def test_missing_credentials_name_both_variables_and_where_to_get_them():
    with pytest.raises(ConfigError) as refused:
        client_from_env({})

    message = str(refused.value)
    assert "WFLOW_CLIENT_ID" in message and "WFLOW_CLIENT_SECRET" in message
    assert "admin.wflow.com" in message and "API accesses" in message


def test_a_blank_secret_counts_as_missing():
    with pytest.raises(ConfigError, match="WFLOW_CLIENT_SECRET"):
        client_from_env({"WFLOW_CLIENT_ID": "acme_client", "WFLOW_CLIENT_SECRET": "  "})


def test_production_is_the_default():
    assert client_from_env(CREDENTIALS).api_base == "https://api.wflow.com"


def test_the_test_environment_and_the_overrides():
    assert client_from_env(CREDENTIALS | {"WFLOW_ENV": "test"}).api_base == "https://apitest.wflow.com"
    assert client_from_env(CREDENTIALS | {"WFLOW_API_BASE": "https://api.example"}).api_base == "https://api.example"


def test_an_unknown_environment_is_refused_by_name():
    with pytest.raises(ConfigError, match="staging"):
        client_from_env(CREDENTIALS | {"WFLOW_ENV": "staging"})


def test_the_token_comes_from_client_credentials_against_the_account_host():
    client = client_from_env(CREDENTIALS | {"WFLOW_ACCOUNT_BASE": "https://account.example"})

    assert isinstance(client._token, ClientCredentials)
    assert client._token._account_base == "https://account.example"


def test_the_cli_identifies_itself():
    assert {
        "X-Client-Id": "wflowinternal",
        "X-Integration-Id": "wflow_cli",
        "X-Integration-Version": __version__,
    } == HEADERS


def test_the_secret_never_appears_in_a_refusal():
    with pytest.raises(ConfigError) as refused:
        client_from_env({"WFLOW_CLIENT_SECRET": "s3cret"})

    assert "s3cret" not in str(refused.value)
