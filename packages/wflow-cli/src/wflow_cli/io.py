"""JSON arguments in; JSON results and downloaded files out."""

import json
import sys
from pathlib import Path
from typing import Any

import typer
from pydantic_core import to_json

from wflow_api import FileContent

STDIN = "-"


def read_json(text: str, option: str) -> Any:
    if text == STDIN:
        raw = sys.stdin.read()
    elif text.startswith("@"):
        path = Path(text[1:])
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError as error:
            raise typer.BadParameter(f"cannot read {path}: {error.strerror or error}", param_hint=option) from None
    else:
        raw = text
    try:
        return json.loads(raw)
    except json.JSONDecodeError as error:
        raise typer.BadParameter(
            f"not valid JSON ({error.msg} at line {error.lineno} column {error.colno})", param_hint=option
        ) from None


def print_json(value: Any) -> None:
    typer.echo(to_json(value, indent=2).decode())


def check_output(output: str, force: bool) -> None:
    if output == STDIN:
        return
    path = Path(output)
    if path.is_dir():
        raise typer.BadParameter(f"{path} is a directory; name the file to write", param_hint="--output")
    if not path.parent.is_dir():
        raise typer.BadParameter(f"{path.parent} does not exist", param_hint="--output")
    if path.exists() and not force:
        raise typer.BadParameter(f"{path} already exists; pass --force to overwrite it", param_hint="--output")


def save_download(file: FileContent, output: str) -> None:
    if output == STDIN:
        sys.stdout.buffer.write(file.content)
        sys.stdout.buffer.flush()
        return
    path = Path(output)
    path.write_bytes(file.content)
    print_json(
        {"filename": file.filename, "contentType": file.content_type, "sizeBytes": len(file.content), "path": str(path)}
    )
