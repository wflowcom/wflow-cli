# wflow-cli

Source of two packages released together under one version:

- [`packages/wflow-api`](packages/wflow-api) — `wflow-api` on PyPI, the async Python client.
- [`packages/wflow-cli`](packages/wflow-cli) — `wflow-cli` on PyPI, the `wflow` command generated from it.

```bash
make install       # uv sync --all-packages
make test          # tests with coverage
make lint          # format check, lint, types
make release VERSION=x.y.z
```

A `v*` tag on `master` publishes both packages to PyPI; a manual run of the Publish workflow publishes to TestPyPI.
