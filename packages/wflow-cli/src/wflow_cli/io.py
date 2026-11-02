"""JSON arguments in; JSON results and downloaded files out."""

import json
import os
import sys
from pathlib import Path
from typing import Any

import typer
from pydantic_core import to_json

from wflow_api import FileContent

STDIN = "-"


def read_json(text: str, option: str) -> Any:
    if text == STDIN:
        raw: bytes | str = sys.stdin.buffer.read()
    elif text.startswith("@"):
        path = Path(text[1:]).expanduser()
        try:
            raw = path.read_bytes()
        except OSError as error:
            raise typer.BadParameter(f"cannot read {path}: {error.strerror or error}", param_hint=option) from None
    else:
        raw = text
    try:
        return json.loads(raw.encode() if isinstance(raw, str) else raw)
    except json.JSONDecodeError as error:
        raise typer.BadParameter(
            f"not valid JSON ({error.msg} at line {error.lineno} column {error.colno})", param_hint=option
        ) from None
    except UnicodeError:
        raise typer.BadParameter("not UTF-8 text; save it as UTF-8 and try again", param_hint=option) from None


def print_json(value: Any) -> None:
    sys.stdout.buffer.write(to_json(value, indent=2) + b"\n")
    sys.stdout.buffer.flush()


def check_output(output: str, force: bool) -> None:
    if output == STDIN:
        return
    path = Path(output)
    if path.is_dir():
        raise typer.BadParameter(f"{path} is a directory; name the file to write", param_hint="--output")
    if not path.parent.is_dir():
        raise typer.BadParameter(f"{path.parent} does not exist", param_hint="--output")
    if path.exists() or path.is_symlink():
        if not force:
            raise typer.BadParameter(f"{path} already exists; pass --force to overwrite it", param_hint="--output")
        if path.exists() and not os.access(path, os.W_OK):
            raise typer.BadParameter(f"cannot write {path}: permission denied", param_hint="--output")
    elif not os.access(path.parent, os.W_OK):
        raise typer.BadParameter(f"cannot write {path}: {path.parent} is not writable", param_hint="--output")


def save_download(file: FileContent, output: str, force: bool) -> None:
    if output == STDIN:
        sys.stdout.buffer.write(file.content)
        sys.stdout.buffer.flush()
        return
    path = Path(output)
    try:
        with path.open("wb" if force else "xb") as target:
            target.write(file.content)
    except FileExistsError:
        raise typer.BadParameter(
            f"{path} already exists; pass --force to overwrite it", param_hint="--output"
        ) from None
    except OSError as error:
        raise typer.BadParameter(f"cannot write {path}: {error.strerror or error}", param_hint="--output") from None
    print_json(
        {"filename": file.filename, "contentType": file.content_type, "sizeBytes": len(file.content), "path": str(path)}
    )
