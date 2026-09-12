# Packaging

Petstore is a [uv workspace](pyproject.toml) with three independently installable
packages under `packages/`:

- **`petstore-api`** — the JSON API (Starlette + SQLAlchemy/asyncpg). Needs Postgres.
- **`petstore-web`** — the htmx UI, plus the JSON API mounted under `/api`. This is
  the one deployable service (see [`Dockerfile`](Dockerfile)/[`compose.yaml`](compose.yaml)).
- **`petstore-cli`** — a command-line client that talks to `petstore-api` over HTTP.
  Its only dependency is `httpx2`, so it installs cleanly without pulling in the
  server stack.

This doc covers installing `petstore-cli` for a user, and running the server it
talks to.

## 1. Get the server running

`petstore-cli` needs something to call. Easiest path is Docker (also runs the
htmx web UI on the same port):

```sh
docker compose up -d db migrate petstore
```

This starts Postgres, applies migrations, and serves the app at
`http://localhost:8000` — the JSON API `petstore-cli` uses lives under
`http://localhost:8000/api`.

If someone else already runs the server, skip this step and just point the CLI
at their URL (see step 3).

## 2. Install the CLI

**Released version:** grab the wheel from the GitHub release
([`RELEASING.md`](RELEASING.md) publishes one per tag) and install it as an
isolated tool so it doesn't collide with any other Python environment:

```sh
# either of these puts `petstore-cli` on PATH
pipx install https://github.com/OWNER/REPO/releases/download/vX.Y.Z/petstore_cli-X.Y.Z-py3-none-any.whl
uv tool install https://github.com/OWNER/REPO/releases/download/vX.Y.Z/petstore_cli-X.Y.Z-py3-none-any.whl
```

**Unreleased/dev version:** build the wheel from the workspace instead:

```sh
uv build --package petstore-cli
```

This produces `dist/petstore_cli-<version>-py3-none-any.whl`, installable the
same way (`pipx install dist/...` / `uv tool install dist/...`).

Installing it pulls in only `httpx2` and its transitive deps (~8 packages) —
none of `starlette`/`sqlalchemy`/`asyncpg`/`uvicorn` that the server needs.

Requires Python 3.13 (`>=3.13,<3.14`, per the workspace's `requires-python`).

## 3. Point the CLI at the server

Default base URL is `http://localhost:8000/api`. Override with `--base-url` or
the `PETSTORE_API_URL` environment variable if the server runs elsewhere:

```sh
export PETSTORE_API_URL=http://your-host:8000/api
```

## 4. Use it

```sh
petstore-cli list
petstore-cli list --status available
petstore-cli get 1
petstore-cli create --name Rex --category Dogs --tags "friendly,loud" --status available
petstore-cli update 1 --name Rex --category Cats --tags calm --status sold
petstore-cli delete 1
```

## Building/installing the other packages

Same pattern for `petstore-api` or `petstore-web` if you need them outside
Docker — `uv build --package petstore-api` / `--package petstore-web` — but
these pull in the full server dependency stack and `petstore-web` additionally
depends on the other two as local workspace packages, so building it standalone
outside this repo isn't meaningful; use the Docker image instead.
