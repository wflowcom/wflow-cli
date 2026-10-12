import re
from pathlib import Path

from wflow_api.operations import operations
from wflow_cli.commands import command_name

README = Path(__file__).resolve().parents[1] / "packages" / "wflow-cli" / "README.md"


def test_every_command_the_readme_shows_exists():
    known = {command_name(fn.__name__) for _, fn in operations()}
    shown = set(re.findall(r"^\s*(?:\$ )?wflow ([a-z][a-z-]+)", README.read_text(encoding="utf-8"), flags=re.MULTILINE))

    assert shown, "the README shows no commands"
    assert shown <= known, f"the README shows commands that do not exist: {sorted(shown - known)}"
