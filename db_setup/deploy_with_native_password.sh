#!/usr/bin/env bash
set -euo pipefail

# Deploy helper for native Postgres password auth using Databricks secrets.
# Required env vars:
#   APP_PGUSER
#   APP_PGPASSWORD
#
# Optional env vars:
#   DATABRICKS_PROFILE (default: DEFAULT)
#   APP_SECRET_SCOPE (default: jnj-batch-release-secrets)
#   SOURCE_PATH (default: /Workspace/Users/<you>/jnj-batch-automation-demo/files)

PROFILE="${DATABRICKS_PROFILE:-DEFAULT}"
APP_NAME="${APP_NAME:-jnj-batch-release}"
APP_SECRET_SCOPE="${APP_SECRET_SCOPE:-jnj-batch-release-secrets}"

if [[ -z "${APP_PGUSER:-}" || -z "${APP_PGPASSWORD:-}" ]]; then
  echo "APP_PGUSER and APP_PGPASSWORD are required."
  echo "Example:"
  echo '  export APP_PGUSER=app_batch_release'
  echo '  export APP_PGPASSWORD=<strong-password>'
  exit 1
fi

USER_EMAIL="$(databricks current-user me -p "${PROFILE}" -o json | python3 -c 'import sys,json; print(json.load(sys.stdin)["userName"])')"
SOURCE_PATH="${SOURCE_PATH:-/Workspace/Users/${USER_EMAIL}/jnj-batch-automation-demo/files}"

echo "Deploying bundle to ${SOURCE_PATH}"
echo "Ensuring secret scope/keys exist"
APP_SECRET_SCOPE="${APP_SECRET_SCOPE}" DATABRICKS_PROFILE="${PROFILE}" APP_PGUSER="${APP_PGUSER}" APP_PGPASSWORD="${APP_PGPASSWORD}" \
  bash "$(dirname "$0")/create_app_secrets.sh"

databricks bundle deploy -p "${PROFILE}" --var "app_secret_scope=${APP_SECRET_SCOPE}"

echo "Deploying app source"
databricks apps deploy "${APP_NAME}" --source-code-path "${SOURCE_PATH}" -p "${PROFILE}"

echo "Done."
