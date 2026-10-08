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
    offenders = [
        str(path.relative_to(root))
        for path in root.rglob("*.py")
        if "os.environ" in path.read_text() or "getenv" in path.read_text()
    ]

    assert offenders == []


def test_the_library_never_imports_fastmcp():
    root = Path(wflow_api.__file__).parent

    assert [str(path) for path in root.rglob("*.py") if "fastmcp" in path.read_text()] == []
