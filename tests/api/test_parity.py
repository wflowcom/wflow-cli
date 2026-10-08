import wflow_spec as gen

from tests.api.operations.test_register_writes import UPDATE_OPERATIONS
from wflow_api.operations import operations

EXPECTED_OPERATIONS = 76


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
