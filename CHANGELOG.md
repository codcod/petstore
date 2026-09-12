# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning follows
[Semantic Versioning](https://semver.org/).

## [Unreleased]

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

[Unreleased]: https://github.com/OWNER/REPO/compare/HEAD...HEAD
