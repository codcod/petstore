# syntax=docker/dockerfile:1

FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder
WORKDIR /app
ENV UV_LINK_MODE=copy
# ponytail: single COPY + sync (no separate deps-only layer) since a uv workspace
# needs every member's pyproject.toml to resolve anyway. Loses the Docker layer
# cache for dependency installs — revisit if rebuild time on source-only changes
# becomes a problem.
COPY pyproject.toml uv.lock ./
COPY packages ./packages
COPY migrations ./migrations
COPY tests ./tests
COPY alembic.ini ./alembic.ini
RUN uv sync --no-dev --all-packages

# distroless debian13 ships Python 3.13 (3.14 has no distroless build yet) with no shell/package manager — smallest, lowest attack surface.
FROM gcr.io/distroless/python3-debian13
WORKDIR /app
COPY --from=builder /app/.venv/lib/python3.13/site-packages /app/site-packages
COPY packages/petstore-api/src/petstore_api ./petstore_api
COPY packages/petstore-cli/src/petstore_cli ./petstore_cli
COPY packages/petstore-web/src/petstore_web ./petstore_web
ENV PYTHONPATH=/app/site-packages
USER nonroot
EXPOSE 8000
ENTRYPOINT ["python", "-m", "uvicorn", "petstore_web.main:app", "--host", "0.0.0.0", "--port", "8000"]
