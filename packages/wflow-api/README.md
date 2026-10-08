# wflow-api

Async Python client for the [wflow.com](https://www.wflow.com) public API: one function per API operation, typed
with pydantic models. The [`wflow-cli`](https://pypi.org/project/wflow-cli/) command is generated from it.

```python
import asyncio

from wflow_api import ENVIRONMENTS, ClientCredentials, WflowClient
from wflow_api.operations.registers import list_register_partners

api_base, account_base = ENVIRONMENTS["prod"]
client = WflowClient(
    ClientCredentials("your-full-client-id", "your-client-secret", account_base),
    api_base=api_base,
    headers={"X-Integration-Id": "your-integration"},
)

page = asyncio.run(list_register_partners(client, "acme", pageSize=50))
print(page.totalItems, [partner.name for partner in page.items])
```

Every operation validates its arguments before a request leaves and raises `wflow_api.WflowError` (or
`WflowApiError`, with `status`, `method`, `path` and `detail`) on failure. Files are bytes: uploads take `content`,
downloads return `FileContent`.
