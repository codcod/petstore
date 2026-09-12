# Releasing petstore

`petstore` ships three independently installable Python packages
(`petstore-api`, `petstore-web`, `petstore-cli`) as wheels/sdists attached to a GitHub
release, plus the deployable web app as a container image on GHCR
(`ghcr.io/OWNER/REPO`).

> This process is the same shape as [snowball's `RELEASING.md`](https://github.com/codcod/snowball/blob/main/RELEASING.md):
> a human stamps the changelog and tags, everything downstream is tag-driven. There is no
> goreleaser here (this isn't Go) and no Homebrew tap (nothing to brew) — the equivalent
> "build + publish artifacts" work is `uv build` for the wheels and
> `docker/build-push-action` for the image, both run from
> [`release.yml`](.github/workflows/release.yml).

## Cutting a release

Cutting a release is a deliberate human action. Tagging and pushing are never automated.

**1. Stamp the changelog and bump the version.** In [`CHANGELOG.md`](CHANGELOG.md),
retitle `[Unreleased]` to `[X.Y.Z] - YYYY-MM-DD`, add a fresh empty `[Unreleased]` above
it, and add a compare link at the bottom following the existing pattern. Reconcile the
entries by hand against what actually shipped since the last tag:

```sh
git log "$(git describe --tags --abbrev=0)..HEAD" --oneline
```

Then bump `version = "..."` to `X.Y.Z` in **all three** `packages/*/pyproject.toml` files
— they're released together, on one version, one tag. `release.yml` checks these match the
tag and fails the release if they don't, so this step isn't optional. Commit both changes
together.

**2. Tag and push.** Everything from here is tag-driven: the
[`release`](.github/workflows/release.yml) workflow runs on any `v*.*.*` tag.

```sh
git tag vX.Y.Z
git push origin vX.Y.Z
```

Never hand-edit a version some other way — the tag (and the pyproject versions it must
match) is the single source of truth.

## What a release produces

- A **GitHub release** with wheels + sdists for all three packages, plus `checksums.txt`,
  attached as assets. Release notes are auto-generated from merged PRs/commits since the
  last tag.
- A **container image** pushed to `ghcr.io/OWNER/REPO`, tagged both `X.Y.Z` and `latest`.
  This is the image `docker compose`/the `Dockerfile` produce — the single deployable
  process serving the htmx UI + JSON API.
- A **prerelease**, automatically, when the version looks like one (`vX.Y.Z-rc.1` etc. —
  detected by the presence of a `-` in the version).

Before publishing anything, the workflow runs lint, type-check, and the full test suite
(unit + the dockerized integration suite against a real Postgres). A failing check aborts
the release before a single artifact is built or uploaded.

## Re-running a release

The workflow can be re-run for an **existing** tag via *Actions → Release → Run workflow*,
passing the tag name (`workflow_dispatch`). Useful after fixing a missing/expired secret —
the GHCR push will happily overwrite the same image tag; a GitHub release re-run will fail
on the release-creation step if assets already exist, so delete the existing release first
if you need a clean re-upload.

## Validating locally (no publish)

```sh
just lint
just unit
docker compose build && docker compose run --rm migrate && docker compose run --rm test
uv build --package petstore-api && uv build --package petstore-web && uv build --package petstore-cli
```

This is exactly what CI (`.github/workflows/ci.yml`) and the release workflow's pre-publish
gates run — if this passes locally, the release gates will too (modulo secrets).

## What the release depends on

- **`GITHUB_TOKEN`** — provided automatically by Actions; granted `contents: write` (create
  the release, upload assets) and `packages: write` (push to GHCR). No extra PAT/secret is
  needed, unlike a project publishing to a separate tap/registry repo — GHCR under the same
  repo is covered by the default token.

## Versioning

Semantic versioning, one version across all three packages. While the version is below
`1.0.0`, breaking changes may land in a minor release. They must be labelled `### Breaking`
in the changelog and include a migration hint in the error the user actually sees, rather
than becoming silent behaviour drift.
