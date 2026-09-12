# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning follows
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.1] - 2026-09-12

### Changed

- `petstore-api`: bump `starlette` to `>=1.6.0`, `uvicorn` to `>=0.52.4`, `sqlalchemy` to `>=2.0.52`,
  `asyncpg` to `>=0.31.0`, `msgspec` to `>=0.21.1`, `python-multipart` to `>=0.0.32`.
- `petstore-web`: bump `starlette` to `>=1.6.0`, `uvicorn` to `>=0.52.4`, `python-multipart` to `>=0.0.32`.
- CI: bump `actions/checkout` to v7, `astral-sh/setup-uv` to v7, `softprops/action-gh-release` to v3.

## [0.1.0] - 2026-09-12

### Added

- `petstore-api`: JSON API (list/get/create/update/delete pets) over Starlette + SQLAlchemy/asyncpg.
- `petstore-web`: htmx-driven web UI (sidebar, detail pane, add/edit forms), talking to
  `petstore-api` in-process over an ASGI transport — no network hop, one deployable process.
  Also mounts the JSON API externally at `/api`.
- `petstore-cli`: command-line client for the JSON API, installable standalone (only
  depends on `httpx2` — no server dependencies pulled in).
- uv workspace split (`packages/petstore-api`, `packages/petstore-web`, `packages/petstore-cli`),
  each independently buildable/installable.
- Docker Compose stack (`db` + `migrate` + `petstore`) and a single production `Dockerfile`.
- Settings externalized to `.env` (`POSTGRES_*`, `APP_PORT`).

[Unreleased]: https://github.com/codcod/petstore/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/codcod/petstore/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/codcod/petstore/releases/tag/v0.1.0
