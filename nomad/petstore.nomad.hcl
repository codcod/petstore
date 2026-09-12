job "petstore" {
  type = "service"

  # network.mode = "host" below avoids Nomad's CNI-based bridge networking,
  # which needs Linux network-namespace/CNI plugins a macOS-hosted nomad
  # agent doesn't have. It still publishes each declared port to the docker
  # host's 127.0.0.1 (visible via `docker ps`), but containers stay on
  # docker's own default bridge network underneath — so they can't reach
  # each other by "localhost". Instead, tasks reach postgres via
  # host.docker.internal, the address Docker Desktop gives containers for
  # reaching ports published on their own host.

  group "db" {
    count = 1

    network {
      mode = "host"
      port "db" {
        static = 5432
      }
    }

    task "postgres" {
      driver = "docker"

      config {
        image          = "postgres:18-alpine"
        ports          = ["db"]
        auth_soft_fail = true
      }

      env {
        POSTGRES_USER     = "app"
        POSTGRES_PASSWORD = "app"
        POSTGRES_DB       = "app"
      }

      resources {
        cpu    = 10
        memory = 256
      }
    }
  }

  group "app" {
    count = 1

    network {
      mode = "host"
      port "http" {
        static = 8000
      }
    }

    # each migrate attempt re-runs `uv sync --group dev` from scratch (network
    # fetch, no persistent cache) and postgres's own two-phase init (bootstrap
    # start/stop, then real start) can take a few seconds too — a tight retry
    # budget here just burns the first allocation and makes Nomad reschedule
    # a second one, which then succeeds only because postgres is warm by then.
    # Give it enough budget to succeed on the first allocation instead.
    restart {
      attempts = 10
      delay    = "5s"
      interval = "5m"
      mode     = "fail"
    }

    # one-shot: runs before "petstore" starts, then exits.
    task "migrate" {
      driver = "docker"

      lifecycle {
        hook    = "prestart"
        sidecar = false
      }

      config {
        image          = "templ-migrate:local"
        auth_soft_fail = true
        command        = "sh"
        args           = ["-c", "uv sync --group dev && uv run alembic upgrade head"]
      }

      env {
        DATABASE_URL = "postgresql+asyncpg://app:app@host.docker.internal:5432/app"
      }

      resources {
        cpu    = 10
        memory = 512
      }
    }

    task "petstore" {
      driver = "docker"

      config {
        image          = "templ-petstore:local"
        ports          = ["http"]
        auth_soft_fail = true
      }

      env {
        DATABASE_URL = "postgresql+asyncpg://app:app@host.docker.internal:5432/app"
      }

      resources {
        cpu    = 10
        memory = 256
      }
    }
  }
}
