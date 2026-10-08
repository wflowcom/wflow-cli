import inspect
from typing import Annotated, Any

import typer
from typer.testing import CliRunner

KEYWORD = inspect.Parameter.KEYWORD_ONLY


def build(seen: dict[str, Any]) -> typer.Typer:
    def run(**values: Any) -> None:
        seen.clear()
        seen.update(values)

    parameters = [
        inspect.Parameter(
            "organization",
            KEYWORD,
            annotation=Annotated[
                str, typer.Option("--organization", "-o", help="Workspace slug", envvar="WFLOW_ORGANIZATION")
            ],
        ),
        inspect.Parameter("documentId", KEYWORD, annotation=Annotated[str, typer.Option("--document-id")]),
        inspect.Parameter(
            "pageSize",
            KEYWORD,
            annotation=Annotated[int | None, typer.Option("--page-size", help="Records per page")],
            default=None,
        ),
        inspect.Parameter(
            "main", KEYWORD, annotation=Annotated[bool | None, typer.Option("--main/--no-main")], default=None
        ),
    ]
    target: Any = run
    target.__signature__ = inspect.Signature(parameters)
    target.__annotations__ = {parameter.name: parameter.annotation for parameter in parameters}

    app = typer.Typer()

    @app.callback()
    def main() -> None:
        pass

    app.command(name="get-document", help="Sample help.", rich_help_panel="Documents")(run)
    return app


def test_typer_builds_a_command_from_a_signature_made_at_runtime():
    seen: dict[str, Any] = {}
    app = build(seen)
    runner = CliRunner()

    ran = runner.invoke(app, ["get-document", "-o", "acme", "--document-id", "d-1", "--page-size", "5", "--no-main"])

    assert ran.exit_code == 0, ran.output
    assert seen == {"organization": "acme", "documentId": "d-1", "pageSize": 5, "main": False}


def test_unset_optionals_arrive_as_none_and_required_ones_are_enforced():
    seen: dict[str, Any] = {}
    app = build(seen)
    runner = CliRunner()

    assert runner.invoke(app, ["get-document", "-o", "acme", "--document-id", "d-1"]).exit_code == 0
    assert seen["pageSize"] is None and seen["main"] is None

    missing = runner.invoke(app, ["get-document", "-o", "acme"])
    assert missing.exit_code == 2
    assert "--document-id" in missing.output


def test_the_environment_fills_the_organization_and_help_shows_option_help():
    seen: dict[str, Any] = {}
    app = build(seen)
    runner = CliRunner()

    assert (
        runner.invoke(app, ["get-document", "--document-id", "d-1"], env={"WFLOW_ORGANIZATION": "from-env"}).exit_code
        == 0
    )
    assert seen["organization"] == "from-env"

    shown = runner.invoke(app, ["get-document", "--help"])
    assert shown.exit_code == 0
    assert "Records per page" in shown.output and "--page-size" in shown.output
