# Petstore

A small petstore app split into three independently installable Python packages
in a [uv workspace](pyproject.toml):

- **`petstore-api`** — JSON API (list/get/create/update/delete pets) over
  Starlette + SQLAlchemy/asyncpg.
- **`petstore-web`** — htmx-driven web UI, talking to `petstore-api` in-process
  over an ASGI transport (no network hop, one deployable process). Also mounts
  the JSON API externally at `/api`.
- **`petstore-cli`** — command-line client for the JSON API, installable
  standalone (only depends on `httpx2`, no server dependencies pulled in).

## Quickstart

```sh
just up   # db + migrations + app, at http://localhost:8000
```

## Development

See the [`justfile`](justfile) for the full recipe list (`just --list`), notably:

```sh
just dev      # run the app locally with autoreload
just lint     # ruff + type-check
just unit     # fast DB-less unit tests
just test     # full test suite against the dockerized db
just ci       # everything CI runs, locally
```

## More

- [`PACKAGING.md`](PACKAGING.md) — installing `petstore-cli` and building the
  other packages.
- [`RELEASING.md`](RELEASING.md) — cutting a release (tags, changelog, published
  artifacts).
- [`CHANGELOG.md`](CHANGELOG.md) — what shipped, by version.
