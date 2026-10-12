from wflow_cli.commands import build_app
from wflow_cli.credentials import client_from_env

app = build_app(client_from_env)
