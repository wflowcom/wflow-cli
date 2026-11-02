import pytest
import typer.rich_utils


@pytest.fixture(autouse=True)
def plain_output(monkeypatch):
    """Typer forces colour under GITHUB_ACTIONS, FORCE_COLOR or PY_COLORS; tests read plain text."""
    monkeypatch.setattr(typer.rich_utils, "FORCE_TERMINAL", False)
