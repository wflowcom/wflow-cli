"""One command per wflow_api operation, generated from its signature and docstring."""

import asyncio
import inspect
import re
from collections.abc import Awaitable, Callable, Coroutine
from pathlib import Path
from types import UnionType
from typing import Annotated, Any, Union, cast, get_args, get_origin, get_type_hints

import typer
from pydantic.fields import FieldInfo

from wflow_api import FileContent, WflowApiError, WflowClient, WflowError
from wflow_api.auth import TOKEN_PATH
from wflow_api.operations import operations
from wflow_cli import __version__
from wflow_cli.credentials import ConfigError
from wflow_cli.io import STDIN, check_output, print_json, read_json, save_download

SIMPLE = (str, int, float, bool)
KEYWORD = inspect.Parameter.KEYWORD_ONLY
EMPTY = inspect.Parameter.empty
SIZE_LIMIT = "max_bytes"
DOWNLOAD_HELP = (
    "Writes the bytes to `--output` and prints their filename, contentType, sizeBytes and path as JSON; "
    "`--output -` writes only the bytes to stdout."
)

MakeClient = Callable[[], WflowClient]
Operation = Callable[..., Awaitable[Any]]


def command_name(name: str) -> str:
    return name.replace("_", "-")


def option_name(name: str) -> str:
    return "--" + re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "-", name).replace("_", "-").lower()


def explain(error: WflowError) -> str:
    message = str(error)
    if isinstance(error, WflowApiError) and (error.status == 401 or error.path == TOKEN_PATH):
        return f"{message} Check WFLOW_CLIENT_ID and WFLOW_CLIENT_SECRET."
    if isinstance(error, WflowApiError) and error.status == 403:
        return f"{message} Is this API client allowed in the workspace? Settings → Integrations → API accesses."
    return message


def _one_line(message: str) -> str:
    return "; ".join(line.strip() for line in message.splitlines() if line.strip())


def _described(annotation: Any) -> tuple[Any, str | None]:
    if get_origin(annotation) is not Annotated:
        return annotation, None
    base, *metadata = get_args(annotation)
    descriptions = [item.description for item in metadata if isinstance(item, FieldInfo) and item.description]
    return base, descriptions[-1] if descriptions else None


def _bare(annotation: Any) -> Any:
    if get_origin(annotation) in (Union, UnionType):
        rest = [arg for arg in get_args(annotation) if arg is not type(None)]
        if len(rest) == 1:
            return rest[0]
    return annotation


def _annotated(base: Any, option: Any) -> Any:
    return cast(Any, Annotated)[base, option]


def _option(name: str, bare: Any, description: str | None) -> Any:
    if name == "organization":
        return typer.Option("--organization", "-o", help=description, envvar="WFLOW_ORGANIZATION")
    if name == SIZE_LIMIT:
        return typer.Option(option_name(name), min=0, help="Refuse a file larger than this many bytes.")
    if bare is bool:
        flag = option_name(name)
        return typer.Option(f"{flag}/--no-{flag[2:]}", help=description)
    return typer.Option(option_name(name), help=description)


def _options(fn: Operation) -> tuple[list[inspect.Parameter], dict[str, str]]:
    original = inspect.unwrap(fn)
    hints = get_type_hints(original, include_extras=True)
    uploads = "content" in hints and _bare(_described(hints["content"])[0]) is bytes
    parameters: list[inspect.Parameter] = []
    kinds: dict[str, str] = {}
    for name, parameter in inspect.signature(original).parameters.items():
        if name == "client" or (parameter.kind is KEYWORD and name != SIZE_LIMIT):
            continue
        annotation, description = _described(hints[name])
        bare = _bare(annotation)
        optional = parameter.default is not EMPTY or (uploads and name == "filename")
        default = (None if parameter.default is EMPTY else parameter.default) if optional else EMPTY
        if uploads and name == "content":
            kinds[name] = "file"
            option = typer.Option("--file", help="The file to upload.", exists=True, dir_okay=False, readable=True)
            parameters.append(inspect.Parameter(name, KEYWORD, annotation=_annotated(Path, option)))
            continue
        if bare in SIMPLE:
            kinds[name] = "value"
            option = _option(name, bare, description)
            typed = bare | None if optional else bare
        else:
            kinds[name] = "json"
            option = typer.Option(
                option_name(name), help=f"{description or 'JSON value'}. Inline JSON, @file.json, or - for stdin."
            )
            typed = str | None if optional else str
        if uploads and name == "filename":
            option = typer.Option(
                "--filename", help="Name wflow stores the file under; defaults to the file's own name."
            )
        parameters.append(inspect.Parameter(name, KEYWORD, annotation=_annotated(typed, option), default=default))
    if hints.get("return") is FileContent:
        if {"output", "force"} & set(kinds):
            raise RuntimeError(f"{original.__name__} already has a parameter named output or force")
        parameters.append(
            inspect.Parameter(
                "output",
                KEYWORD,
                annotation=_annotated(
                    str,
                    typer.Option(
                        "--output",
                        help="File to write, then print its filename, contentType, sizeBytes and path as JSON; "
                        "- writes the bytes to stdout instead.",
                    ),
                ),
            )
        )
        parameters.append(
            inspect.Parameter(
                "force",
                KEYWORD,
                annotation=_annotated(bool, typer.Option("--force", help="Overwrite an existing file.")),
                default=False,
            )
        )
    return parameters, kinds


def _stdin_readers(kinds: dict[str, str], values: dict[str, Any]) -> list[str]:
    return [name for name, kind in kinds.items() if kind == "json" and values.get(name) == STDIN]


def _arguments(kinds: dict[str, str], values: dict[str, Any]) -> dict[str, Any]:
    arguments: dict[str, Any] = {}
    for name, value in values.items():
        if kinds[name] == "json":
            arguments[name] = None if value is None else read_json(value, option_name(name))
        elif kinds[name] == "file":
            arguments[name] = value.read_bytes()
        else:
            arguments[name] = value
    if "file" in kinds.values() and arguments.get("filename") is None:
        upload = next(name for name, kind in kinds.items() if kind == "file")
        arguments["filename"] = values[upload].name
    return arguments


def _command(fn: Operation, kinds: dict[str, str], make_client: MakeClient) -> Callable[..., None]:
    def run(**values: Any) -> None:
        output = values.pop("output", None)
        force = values.pop("force", False)
        if len(readers := _stdin_readers(kinds, values)) > 1:
            raise typer.BadParameter(
                f"only one option can read stdin, but {', '.join(map(option_name, readers))} all ask for it"
            )
        if output is not None:
            check_output(output, force)
        arguments = _arguments(kinds, values)
        try:
            result = asyncio.run(cast(Coroutine[Any, Any, Any], fn(make_client(), **arguments)))
        except ConfigError as error:
            typer.echo(_one_line(str(error)), err=True)
            raise typer.Exit(2) from None
        except WflowError as error:
            typer.echo(_one_line(explain(error)), err=True)
            raise typer.Exit(1) from None
        if isinstance(result, FileContent):
            save_download(result, output or STDIN)
        else:
            print_json(result)

    return run


def _register(app: typer.Typer, module: str, fn: Operation, make_client: MakeClient) -> None:
    parameters, kinds = _options(fn)
    run: Any = _command(fn, kinds, make_client)
    run.__signature__ = inspect.Signature(parameters)
    run.__annotations__ = {parameter.name: parameter.annotation for parameter in parameters}
    run.__name__ = fn.__name__
    help_text = inspect.getdoc(fn) or ""
    if "output" in {parameter.name for parameter in parameters}:
        help_text = f"{help_text}\n\n{DOWNLOAD_HELP}"
    app.command(name=command_name(fn.__name__), help=help_text, rich_help_panel=module.replace("_", " ").capitalize())(
        run
    )


def _version(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


def build_app(make_client: MakeClient) -> typer.Typer:
    app = typer.Typer(
        name="wflow",
        help="The wflow.com public API from the command line. Set WFLOW_CLIENT_ID and WFLOW_CLIENT_SECRET; "
        "every command prints JSON.",
        no_args_is_help=True,
        rich_markup_mode="markdown",
    )

    @app.callback()
    def main(
        version: Annotated[
            bool, typer.Option("--version", callback=_version, is_eager=True, help="Print the version and exit.")
        ] = False,
    ) -> None:
        pass

    for module, fn in operations():
        _register(app, module, fn, make_client)
    return app
