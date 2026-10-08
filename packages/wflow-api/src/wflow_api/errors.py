class WflowError(Exception):
    """A wflow call that could not be made or did not succeed."""


class WflowApiError(WflowError):
    """wflow answered with an error status."""

    def __init__(self, message: str, *, status: int, method: str, path: str, detail: str) -> None:
        super().__init__(message)
        self.status = status
        self.method = method
        self.path = path
        self.detail = detail
