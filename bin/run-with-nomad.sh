#!/usr/bin/env bash
# Build the app's docker images and run them under a local Nomad dev agent.
#
# Usage:
#   bin/run-with-nomad.sh up      build images, start the dev agent (if needed), run the job
#   bin/run-with-nomad.sh down    stop the job and kill the dev agent
#   bin/run-with-nomad.sh status  show job/alloc status
#   bin/run-with-nomad.sh logs    tail the petstore task's logs
#
# See docs/nomad.md for what this does and why.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
JOB_FILE="$ROOT_DIR/nomad/petstore.nomad.hcl"
NOMAD_ADDR="${NOMAD_ADDR:-http://127.0.0.1:4646}"
NOMAD_LOG="$ROOT_DIR/.nomad-agent.log"
NOMAD_PID_FILE="$ROOT_DIR/.nomad-agent.pid"

require() {
  command -v "$1" >/dev/null 2>&1 || { echo "error: '$1' not found on PATH" >&2; exit 1; }
}

agent_running() {
  curl -fs "$NOMAD_ADDR/v1/status/leader" >/dev/null 2>&1
}

start_agent() {
  if agent_running; then
    echo "nomad dev agent already running at $NOMAD_ADDR"
    return
  fi
  echo "starting nomad dev agent (logs: $NOMAD_LOG)..."
  nohup nomad agent -dev -bind=127.0.0.1 >"$NOMAD_LOG" 2>&1 &
  echo $! >"$NOMAD_PID_FILE"
  for _ in $(seq 1 30); do
    agent_running && break
    sleep 1
  done
  agent_running || { echo "error: nomad agent did not come up, check $NOMAD_LOG" >&2; exit 1; }
}

stop_agent() {
  if [[ -f "$NOMAD_PID_FILE" ]]; then
    local pid
    pid="$(cat "$NOMAD_PID_FILE")"
    if kill -0 "$pid" 2>/dev/null; then
      echo "stopping nomad dev agent (pid $pid)..."
      kill "$pid"
    fi
    rm -f "$NOMAD_PID_FILE"
  else
    echo "no tracked nomad agent pid — leave any manually-started agent as is"
  fi
}

build_images() {
  echo "building petstore images..."
  docker build -t templ-petstore:local "$ROOT_DIR"
  docker build --target builder -t templ-migrate:local "$ROOT_DIR"
}

run_job() {
  echo "running nomad job..."
  nomad job run "$JOB_FILE"
  echo
  echo "petstore should come up at http://127.0.0.1:8000 once migrations finish."
  echo "check progress with: $0 status   or   $0 logs"
}

cmd_up() {
  require docker
  require nomad
  require curl
  build_images
  start_agent
  run_job
}

cmd_down() {
  require nomad
  require docker
  if agent_running; then
    nomad job stop -purge petstore || true
    # give the docker driver a moment to actually remove containers before
    # the agent process (which does that cleanup) is killed.
    sleep 3
  fi
  stop_agent
  # defensive: nomad names containers "<task>-<alloc-id>"; remove any left over.
  local leftover
  leftover="$(docker ps -aq --filter "name=^postgres-" --filter "name=^petstore-" --filter "name=^migrate-")"
  [[ -z "$leftover" ]] || docker rm -f $leftover >/dev/null
}

cmd_status() {
  require nomad
  nomad job status petstore
}

cmd_logs() {
  require nomad
  require jq
  local alloc_id
  # the "petstore" task lives in the "app" task group — pick its latest alloc.
  alloc_id="$(nomad job allocs -json petstore | jq -r '[.[] | select(.TaskGroup=="app")] | sort_by(.CreateIndex) | last | .ID // empty')"
  [[ -n "$alloc_id" ]] || { echo "error: no 'app' group allocation found for job 'petstore'" >&2; exit 1; }
  nomad alloc logs -f "$alloc_id" petstore
}

case "${1:-up}" in
  up) cmd_up ;;
  down) cmd_down ;;
  status) cmd_status ;;
  logs) cmd_logs ;;
  *) echo "usage: $0 {up|down|status|logs}" >&2; exit 1 ;;
esac
