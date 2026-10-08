# wflow CLI

The [wflow.com](https://www.wflow.com) public API from the command line. Every API operation is one
command, every command prints JSON (except a download to `--output -`, which writes the file's raw bytes to
stdout), and `wflow <command> --help` documents what it sends and returns.

## Install

```bash
pipx install wflow-cli        # or: uv tool install wflow-cli   or: pip install wflow-cli
wflow --version
```

Python 3.12 or newer. `pipx` and `uv tool` keep the CLI in its own environment.

## Set up an API client

The CLI signs in as an API client with the `client_credentials` grant — a machine identity, not a person.

1. Create an API client with the `client_credentials` grant in [admin.wflow.com](https://admin.wflow.com).
2. Allow the client in each workspace it should reach: in the workspace, **Settings → Integrations → API accesses**.
3. Give the CLI the credentials:

```bash
export WFLOW_CLIENT_ID="your-full-client-id"
export WFLOW_CLIENT_SECRET="your-client-secret"
export WFLOW_ORGANIZATION="your-workspace"   # optional: the default for --organization/-o
```

| Variable | Meaning |
|---|---|
| `WFLOW_CLIENT_ID`, `WFLOW_CLIENT_SECRET` | required |
| `WFLOW_ENV` | `prod` (default) or `test` |
| `WFLOW_ORGANIZATION` | default workspace slug for `-o` |
| `WFLOW_API_BASE`, `WFLOW_ACCOUNT_BASE` | override the API and identity hosts |

Credentials are read from the environment only; no option takes a secret.

## Use it

```bash
wflow --help                                              # every command, grouped by area
wflow get-organization -o acme
wflow list-register-partners -o acme --page-size 50 --query 'name = "Acme s.r.o."'
wflow list-documents -o acme --sort "created desc"
```

A list command that takes `--page` and `--page-size` returns one page: `{items, totalItems, pageSize, page}`.
Compare `totalItems` with what you have before assuming you have everything.

### Writing

Options that take a record or a list of records take JSON — inline, from a file with `@`, or from stdin with `-`
(one option per command can read stdin):

```bash
wflow patch-register-partners -o acme --partners @partners.json
cat partners.json | wflow patch-register-partners -o acme --partners -
```

`update-register-*` replaces the whole register: every record you leave out is retired. `patch-register-*` leaves
the records you do not send alone. Both replace each record you send as a whole, so send the full record. wflow
keeps no version history — read `wflow <command> --help` before writing.

### Files

```bash
wflow upload-document-file -o acme --document-id <id> --file ./invoice.pdf
wflow download-document-file -o acme --file-id <id> --output ./invoice.pdf
wflow download-document-file -o acme --file-id <id> --output - > invoice.pdf
```

An upload is stored under the file's own name unless you pass `--filename`. A download never overwrites an
existing file unless you pass `--force`.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | success; the result is on stdout as JSON, or the file's raw bytes for a download with `--output -` |
| `1` | wflow refused or failed the call, or the input was refused before anything was sent; one line on stderr says why |
| `2` | the command line or the environment is wrong; stderr has a usage message or says what to set |

## For AI agents

Every command prints its result as JSON on stdout and the reason for a failure on stderr, so an agent can run
`wflow` from a shell, check the exit code and parse the result. The one exception is a download with `--output -`,
which writes the file's raw bytes to stdout instead. `wflow <command> --help` is the documentation for
that command.

## Python

The commands are generated from the [`wflow-api`](https://pypi.org/project/wflow-api/) package, which you can use
directly.
