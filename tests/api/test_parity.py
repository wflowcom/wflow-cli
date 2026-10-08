import ast
import re

import wflow_spec as gen

from tests.api.operations.test_register_writes import UPDATE_OPERATIONS
from tests.helpers import body_source
from wflow_api.operations import operations

EXPECTED_OPERATIONS = 76
CALLS_THROUGH_A_HELPER = {
    "get_me": "reads through guards.current_account, which also refuses a null account",
}


def spec_names(wflow_spec) -> set[str]:
    return {gen.tool_name(m, p, o.get("summary", "")) for p, m, o in gen.operations(wflow_spec)}


def library_names() -> set[str]:
    return {fn.__name__ for _, fn in operations()}


def test_no_operation_wraps_an_endpoint_that_does_not_exist(wflow_spec):
    assert library_names() <= spec_names(wflow_spec), library_names() - spec_names(wflow_spec)


def test_the_operation_count():
    assert len(operations()) == len(library_names()) == EXPECTED_OPERATIONS


def test_the_spec_still_documents_173_operations(wflow_spec):
    assert len(spec_names(wflow_spec)) == 173


def writable_register_segments(wflow_spec) -> set[str]:
    paths = (path for path, method, _ in gen.operations(wflow_spec) if method == "put")
    return {path.rsplit("/registers/", 1)[1] for path in paths if "/registers/" in path}


def test_every_register_write_addresses_a_segment_the_spec_documents(wflow_spec):
    segments = writable_register_segments(wflow_spec)
    for name, segment, _ in UPDATE_OPERATIONS:
        assert segment in segments, f"{name} writes to registers/{segment}, which the spec does not document"


def path_text(node: ast.expr) -> str:
    if isinstance(node, ast.Constant):
        return node.value
    text = "".join(
        part.value if isinstance(part, ast.Constant) else f"{{{ast.unparse(part.value)}}}" for part in node.values
    )
    return re.sub(r"\{path_segment\((\w+)\)\}", r"{\1}", text)


def wire_calls(fn) -> list[tuple[str, str]]:
    """The (method, path) of every client.request / upload / download in an operation's body."""
    body = ast.parse(body_source(fn))
    assigned = {
        target.id: node.value
        for node in ast.walk(body)
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    calls = []
    for node in ast.walk(body):
        if not (isinstance(node, ast.Call) and ast.unparse(node.func).startswith("client.")):
            continue
        keywords = {keyword.arg: keyword.value for keyword in node.keywords}
        if node.func.attr == "download":
            path = node.args[0]
            method = node.args[1] if len(node.args) > 1 else keywords.get("method", ast.Constant("GET"))
        else:
            method, path = node.args[:2]
        path = assigned.get(path.id, path) if isinstance(path, ast.Name) else path
        calls.append((method.value.lower(), path_text(path)))
    return calls


def test_every_operation_calls_the_method_and_path_the_spec_documents_for_its_name(wflow_spec):
    routes = {gen.tool_name(m, p, o.get("summary", "")): (m, p) for p, m, o in gen.operations(wflow_spec)}
    assert set(CALLS_THROUGH_A_HELPER) <= library_names()
    for _, fn in operations():
        if fn.__name__ not in CALLS_THROUGH_A_HELPER:
            calls, route = wire_calls(fn), routes[fn.__name__]
            assert calls == [route], f"{fn.__name__} calls {calls}, the spec documents {route}"
