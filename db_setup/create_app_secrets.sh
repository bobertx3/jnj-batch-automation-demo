#!/usr/bin/env bash
set -euo pipefail

# Create/update Databricks secret scope + keys for app DB auth.
#
# Required env vars:
#   APP_PGUSER
#   APP_PGPASSWORD
#
# Optional env vars:
#   DATABRICKS_PROFILE (default: DEFAULT)
#   APP_SECRET_SCOPE (default: jnj-batch-release-secrets)

PROFILE="${DATABRICKS_PROFILE:-DEFAULT}"
SCOPE="${APP_SECRET_SCOPE:-jnj-batch-release-secrets}"

if [[ -z "${APP_PGUSER:-}" || -z "${APP_PGPASSWORD:-}" ]]; then
  echo "APP_PGUSER and APP_PGPASSWORD are required."
  echo "Example:"
  echo "  export APP_PGUSER=app_batch_release"
  echo "  export APP_PGPASSWORD='<strong-password>'"
  exit 1
fi

if databricks secrets list-scopes -p "${PROFILE}" -o json | python3 -c "import sys, json; scopes=json.load(sys.stdin); raise SystemExit(0 if any(x.get('name')=='${SCOPE}' for x in scopes) else 1)"; then
  echo "Secret scope already exists: ${SCOPE}"
else
  echo "Creating secret scope: ${SCOPE}"
  databricks secrets create-scope "${SCOPE}" --scope-backend-type DATABRICKS -p "${PROFILE}"
fi

echo "Storing PGUSER and PGPASSWORD in scope ${SCOPE}"
databricks secrets put-secret "${SCOPE}" PGUSER --string-value "${APP_PGUSER}" -p "${PROFILE}"
databricks secrets put-secret "${SCOPE}" PGPASSWORD --string-value "${APP_PGPASSWORD}" -p "${PROFILE}"

echo "Done. Scope=${SCOPE}, keys=[PGUSER, PGPASSWORD]"
