#!/usr/bin/env bash
set -Eeuo pipefail

# Automated project-level GitLab Runner setup.
# Diagnostics intentionally go to stderr so stdout remains safe for command substitutions.

SCRIPT_NAME="$(basename "$0")"
LOG_FILE="${LOG_FILE:-./gitlab-runner-setup.log}"

log() {
  local level="$1"
  shift
  printf '[%s] [%s] %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$level" "$*" | tee -a "$LOG_FILE" >&2
}

fail() {
  log "ERROR" "$*"
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "Required command '$1' was not found in PATH."
}

urlencode() {
  local raw="${1}"
  local length="${#raw}"
  local encoded=""
  local pos char hex

  for ((pos = 0; pos < length; pos++)); do
    char="${raw:pos:1}"
    case "$char" in
      [a-zA-Z0-9.~_-]) encoded+="$char" ;;
      *) printf -v hex '%%%02X' "'$char"; encoded+="$hex" ;;
    esac
  done

  printf '%s' "$encoded"
}

json_get_string() {
  local key="$1"
  python3 -c '
import json
import sys

key = sys.argv[1]
payload = json.load(sys.stdin)
value = payload.get(key)
if value is None:
    sys.exit(1)
print(value)
' "$key"
}

json_get_runner_token() {
  python3 -c '
import json
import sys

payload = json.load(sys.stdin)
for key in ("token", "runner_token"):
    value = payload.get(key)
    if value:
        print(value)
        sys.exit(0)
sys.exit(1)
'
}

detect_environment() {
  local os arch init_system user_name
  os="$(uname -s | tr '[:upper:]' '[:lower:]')"
  arch="$(uname -m)"
  user_name="$(id -un)"

  if command -v systemctl >/dev/null 2>&1 && [[ -d /run/systemd/system ]]; then
    init_system="systemd"
  else
    init_system="background"
  fi

  log "INFO" "Detected OS=${os}, ARCH=${arch}, INIT=${init_system}, USER=${user_name}."
}

api_get() {
  local endpoint="$1"
  curl --silent --show-error --fail \
    --header "PRIVATE-TOKEN: ${GITLAB_PAT}" \
    "${GITLAB_URL%/}/api/v4/${endpoint}"
}

api_post_form() {
  local endpoint="$1"
  shift
  curl --silent --show-error --fail \
    --request POST \
    --header "PRIVATE-TOKEN: ${GITLAB_PAT}" \
    "$@" \
    "${GITLAB_URL%/}/api/v4/${endpoint}"
}

resolve_project_id() {
  if [[ -n "${GITLAB_PROJECT_ID:-}" ]]; then
    printf '%s' "$GITLAB_PROJECT_ID"
    return
  fi

  [[ -n "${GITLAB_PROJECT_PATH:-}" ]] || fail "Set GITLAB_PROJECT_PATH, for example 'group/subgroup/project', or set GITLAB_PROJECT_ID."

  local encoded_project response project_id
  encoded_project="$(urlencode "$GITLAB_PROJECT_PATH")"
  log "INFO" "Fetching GitLab project ID for '${GITLAB_PROJECT_PATH}'."
  response="$(api_get "projects/${encoded_project}")"
  project_id="$(printf '%s' "$response" | json_get_string "id")" || fail "Could not parse project ID from GitLab API response."

  printf '%s' "$project_id"
}

create_project_runner_token() {
  local project_id="$1"
  local response token

  log "INFO" "Creating project runner registration token for project ID ${project_id}."
  response="$(
    api_post_form "user/runners" \
      --form "runner_type=project_type" \
      --form "project_id=${project_id}" \
      --form "description=${RUNNER_DESCRIPTION}" \
      --form "tag_list=${RUNNER_TAGS}" \
      --form "run_untagged=${RUN_UNTAGGED}" \
      --form "locked=${RUNNER_LOCKED}"
  )"

  token="$(printf '%s' "$response" | json_get_runner_token)" || fail "Could not parse runner token from GitLab API response."
  printf '%s' "$token"
}

register_runner() {
  local runner_token="$1"

  log "INFO" "Registering GitLab Runner '${RUNNER_DESCRIPTION}' with executor '${RUNNER_EXECUTOR}'."
  gitlab-runner register --non-interactive \
    --url "${GITLAB_URL%/}" \
    --token "$runner_token" \
    --executor "$RUNNER_EXECUTOR" \
    --description "$RUNNER_DESCRIPTION" \
    --tag-list "$RUNNER_TAGS" \
    --run-untagged="${RUN_UNTAGGED}" \
    --locked="${RUNNER_LOCKED}"
}

start_runner() {
  if command -v systemctl >/dev/null 2>&1 && [[ -d /run/systemd/system ]]; then
    log "INFO" "Installing and starting GitLab Runner as a systemd service."
    if [[ "$(id -u)" -eq 0 ]]; then
      gitlab-runner install --user="${RUNNER_SERVICE_USER:-gitlab-runner}" --working-directory="${RUNNER_WORKDIR:-/home/gitlab-runner}" || true
      systemctl enable gitlab-runner
      systemctl restart gitlab-runner
    else
      sudo gitlab-runner install --user="${RUNNER_SERVICE_USER:-gitlab-runner}" --working-directory="${RUNNER_WORKDIR:-/home/gitlab-runner}" || true
      sudo systemctl enable gitlab-runner
      sudo systemctl restart gitlab-runner
    fi
  else
    log "INFO" "systemd is unavailable; starting GitLab Runner in the background."
    mkdir -p .gitlab-runner
    nohup gitlab-runner run --working-directory "$(pwd)/.gitlab-runner" >>"$LOG_FILE" 2>&1 &
    printf '%s\n' "$!" > .gitlab-runner/gitlab-runner.pid
    log "INFO" "Background GitLab Runner PID $(cat .gitlab-runner/gitlab-runner.pid)."
  fi
}

main() {
  : >"$LOG_FILE"

  GITLAB_URL="${GITLAB_URL:-https://gitlab.com}"
  RUNNER_DESCRIPTION="${RUNNER_DESCRIPTION:-$(hostname)-project-runner}"
  RUNNER_EXECUTOR="${RUNNER_EXECUTOR:-shell}"
  RUNNER_TAGS="${RUNNER_TAGS:-local,shell}"
  RUN_UNTAGGED="${RUN_UNTAGGED:-true}"
  RUNNER_LOCKED="${RUNNER_LOCKED:-true}"

  [[ -n "${GITLAB_PAT:-}" ]] || fail "Set GITLAB_PAT to a GitLab Personal Access Token with API access."

  require_cmd curl
  require_cmd gitlab-runner
  require_cmd python3

  detect_environment

  local project_id runner_token
  project_id="$(resolve_project_id)"
  runner_token="$(create_project_runner_token "$project_id")"

  register_runner "$runner_token"
  start_runner

  log "INFO" "GitLab Runner setup completed for project ID ${project_id}."
}

main "$@"
