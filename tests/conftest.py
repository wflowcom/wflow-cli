import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


@pytest.fixture(scope="session")
def wflow_spec():
    """The vendored OpenAPI document; refresh with `uv run scripts/wflow_spec.py --fetch`."""
    path = Path(__file__).resolve().parents[1] / "scripts" / "wflow-openapi.json"
    assert path.exists(), "run `uv run scripts/wflow_spec.py --fetch` to vendor the spec"
    return json.loads(path.read_text())
