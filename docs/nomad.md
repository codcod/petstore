# Running Petstore under local Nomad

This runs the same `postgres` + `migrate` + `petstore` stack as `compose.yaml`,
but scheduled by a local [Nomad](https://developer.hashicorp.com/nomad) agent
instead of `docker compose`. It's meant for trying out / learning Nomad
against this app, not as a production deployment pattern.

## 1. Install Nomad

```
brew install nomad          # macOS
```

Or download a binary from
[developer.hashicorp.com/nomad/install](https://developer.hashicorp.com/nomad/install).
Verify with:

```
nomad version
```

## 2. The quick way: `bin/run-with-nomad.sh`

```
bin/run-with-nomad.sh up       # build images, start a dev agent, run the job
bin/run-with-nomad.sh status   # show job/allocation status
bin/run-with-nomad.sh logs     # tail the petstore task's logs
bin/run-with-nomad.sh down     # stop the job and the dev agent
```

Once `up` finishes and migrations have run (check with `status` or `logs`),
the app is at **http://127.0.0.1:8000**.

## 3. Doing it by hand

If you'd rather run each step yourself (or the script doesn't fit your
setup):

```
# 1. build the two images the job needs
docker build -t templ-petstore:local .
docker build --target builder -t templ-migrate:local .

# 2. start a local, single-node, in-memory Nomad dev agent
nomad agent -dev -bind=127.0.0.1

# in another terminal:
# 3. submit the job
nomad job run nomad/petstore.nomad.hcl

# 4. watch it come up
nomad job status petstore

# 5. tear down
nomad job stop -purge petstore
```

`nomad agent -dev` runs a throwaway single-node cluster (server + client in
one process, in-memory state) — perfect for this, useless for anything you
want to survive a restart.

## 4. How the job is put together, and why

See [`nomad/petstore.nomad.hcl`](../nomad/petstore.nomad.hcl). Two things
about it aren't obvious, and both come from limitations of running Nomad
natively on macOS (not Linux) against Docker Desktop:

**Networking uses `mode = "host"`, not `"bridge"`.** Nomad's usual trick for
letting sibling tasks reach each other over `localhost` is a shared network
namespace via CNI bridge plugins — but those need Linux network namespaces on
the machine the *nomad agent* runs on. On macOS that's not available, and job
placement fails with:

```
Constraint "${attr.plugins.cni.version.bridge} semver >= 0.4.0": 1 nodes excluded by filter
```

`mode = "host"` sidesteps CNI. On this setup it ends up publishing each
declared port to the docker host's `127.0.0.1` (visible via `docker ps`),
while containers still land on Docker's own default bridge network
underneath — so, counterintuitively, tasks *still can't reach each other via
`localhost`* the way a real host-network container would on Linux.

**Tasks reach postgres via `host.docker.internal`, not `localhost`.** Since
postgres's port 5432 is published to the docker host's `127.0.0.1` (per
above), and Docker Desktop gives every container a `host.docker.internal`
DNS name that resolves back to that same host, `migrate` and `petstore` use
`DATABASE_URL=postgresql+asyncpg://app:app@host.docker.internal:5432/app`
to reach it. This is a Docker Desktop convenience, not a general Docker
feature — on a real Linux Nomad cluster you'd use CNI bridge networking (or
Consul Connect) and plain `localhost` instead.

**`postgres` and `migrate`/`petstore` are in separate task groups.** A task
with `lifecycle { hook = "prestart" }` blocks every other task *in its own
group* from starting until it succeeds — including tasks with no lifecycle
block. Putting `migrate` in the same group as `postgres` would deadlock:
`migrate` waits to run before `postgres` starts, but `postgres` never gets a
chance to start. Splitting them into a `db` group and an `app` group (with
`migrate` as `app`'s prestart hook) fixes the ordering: `postgres` starts
immediately in its own group, `migrate` retries against it (see the `restart`
block — 10 attempts, 5s apart) until it succeeds, then `petstore` starts.

That retry budget is generous on purpose: each `migrate` attempt re-runs
`uv sync --group dev` from scratch (a network fetch, no persistent cache) and
also rebuilds the project's own wheel, and postgres's own startup is two
phases (a brief bootstrap start/stop, then the real start) — a tight budget
just burns through the first allocation before either is warm. A too-tight
budget doesn't fail loudly: Nomad reschedules a fresh allocation, which then
succeeds because postgres is already warm, so `nomad job status petstore`
ends up healthy overall but shows one allocation `failed` and a second
`running` one that replaced it. If you see that, the fix is the same: widen
`attempts`/`delay` on the `restart` block so the *first* allocation succeeds.

**Resource requests are intentionally tiny** (`cpu = 10`, well under one CPU
core's worth of MHz). A `nomad agent -dev` node's fingerprinted CPU capacity
can be surprisingly small in constrained environments (e.g. CI runners,
sandboxes); these values are chosen to fit comfortably anywhere. Raise them
freely for a real cluster.

## 5. Troubleshooting

- **`Placement Failure` / CNI bridge constraint** — see the networking note
  above; make sure the job still uses `mode = "host"`.
- **`migrate` task OOM-killed (exit 137)** — `uv sync --group dev` (installing
  Alembic) plus building the project needs a bit of headroom; the job already
  gives it 512 MiB, raise it further if your machine still OOMs.
- **`migrate` can't connect / connection refused** — confirm `postgres` is
  actually running: `nomad job status petstore` should show the `db` group
  healthy before `app` comes up. The `restart` block gives it several tries.
- **`status` shows one `app` allocation `failed` and another `running`** — the
  first allocation exhausted its retries before postgres/migrate warmed up
  and Nomad rescheduled a second one that succeeded; the job still ends up
  healthy, but see the retry-budget note in §4 if you want the first
  allocation to succeed outright instead.
- **Port 8000 or 5432 already in use** — something else (maybe
  `docker compose up`) is already bound to it; stop that first, or edit the
  `static` port numbers in the job file.
