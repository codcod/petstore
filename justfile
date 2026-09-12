set dotenv-load

# List available recipes (default when running `just` with no args)
list:
    @just --list

# Start db + run migrations + start the app (detached)
[group('docker')]
up:
    docker compose up -d db migrate petstore

# Stop all containers, keep the db volume
[group('docker')]
down:
    docker compose down

# Stop all containers and wipe the db volume (clean slate)
[group('docker')]
reset:
    docker compose down -v

# Rebuild all images
[group('docker')]
build:
    docker compose build

# Tail the app's logs
[group('docker')]
logs:
    docker compose logs -f petstore

# Apply pending migrations against the dockerized db
[group('database')]
migrate:
    docker compose run --rm migrate

# Generate a new alembic revision, e.g. `just revision "add pet weight"`
[group('database')]
revision name:
    DATABASE_URL=postgresql+asyncpg://$POSTGRES_USER:$POSTGRES_PASSWORD@localhost:$POSTGRES_PORT/$POSTGRES_DB uv run --group dev alembic revision -m "{{ name }}"

# Open a psql shell against the dockerized db
[group('database')]
psql:
    docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB

# Run the test suite against the dockerized db
[group('test')]
test:
    docker compose run --rm test

# Run fast DB-less unit tests (no docker needed)
[group('test')]
unit:
    DATABASE_URL="postgresql+asyncpg://unit:test@unused/unit" uv run --group dev python -m unittest tests.test_pets_helpers tests.test_petstore_web_helpers tests.test_logging tests.test_petstore_cli -v

# Run the app locally with autoreload against the dockerized db
[group('dev')]
dev:
    DATABASE_URL=postgresql+asyncpg://$POSTGRES_USER:$POSTGRES_PASSWORD@localhost:$POSTGRES_PORT/$POSTGRES_DB uv run uvicorn petstore_web.main:app --reload

# Re-resolve and write uv.lock after editing pyproject.toml
[group('dev')]
lock:
    uv lock

# Lint, format-check, and type-check the codebase
[group('dev')]
lint:
    uv run --group dev ruff check packages tests
    uv run --group dev ruff format --check packages tests
    uv run --group dev ty check packages

# Auto-fix lint issues and reformat the codebase
[group('dev')]
format:
    uv run --group dev ruff check --fix packages tests
    uv run --group dev ruff format packages tests

# Run k6 load test against the running app (`just up` first)
[group('test')]
perf:
    k6 run tests/performance/petstore.js

# Run everything ci.yml runs, locally — do this before committing/pushing
[group('ci')]
ci: lint unit build migrate test
    docker compose down -v
    curl -s https://raw.githubusercontent.com/rhysd/actionlint/main/scripts/download-actionlint.bash | bash -s -- latest /tmp
    /tmp/actionlint -color .github/workflows/*.yml
