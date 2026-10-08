from pathlib import Path

import wflow_api


def test_the_public_surface():
    for name in (
        "WflowClient",
        "ClientCredentials",
        "ENVIRONMENTS",
        "WflowError",
        "WflowApiError",
        "FileContent",
        "operation",
    ):
        assert hasattr(wflow_api, name), name


def test_the_library_never_reads_the_environment():
    root = Path(wflow_api.__file__).parent
    sources = {str(path.relative_to(root)): path.read_text() for path in root.rglob("*.py")}
    offenders = [name for name, source in sources.items() if "environ" in source or "getenv" in source]

    assert offenders == []


def test_the_library_never_imports_fastmcp():
    root = Path(wflow_api.__file__).parent

    assert [str(path) for path in root.rglob("*.py") if "fastmcp" in path.read_text()] == []
