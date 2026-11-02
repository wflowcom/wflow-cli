from wflow_api.errors import WflowApiError, WflowError


def test_an_api_error_is_a_wflow_error_carrying_what_failed():
    error = WflowApiError("wflow h GET /x returned 404.", status=404, method="GET", path="/x", detail="Not Found")

    assert isinstance(error, WflowError)
    assert (error.status, error.method, error.path, error.detail) == (404, "GET", "/x", "Not Found")
    assert str(error) == "wflow h GET /x returned 404."
