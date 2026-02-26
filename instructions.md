# From-Scratch Setup (New Databricks Workspace)

This guide is the execution order to stand up this solution in a brand-new workspace.

## 0) Prerequisites (manual)

- Databricks workspace access
- Databricks CLI installed and authenticated
- Python 3.10+ and Node 18+
- A Lakebase project + production branch endpoint available (or create one first)

## 1) Clone repo and install dependencies

```bash
git clone <repo-url>
cd jnj-batch-automation-demo

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install psycopg2-binary

cd frontend
npm install
cd ..
```

## 2) Configure Databricks profile (manual)

Authenticate your CLI profile (example: `DEFAULT`) and verify:

```bash
databricks auth profiles
databricks current-user me -p DEFAULT
```

If needed, set:

```bash
export DATABRICKS_PROFILE=DEFAULT
```

## 3) Configure bundle variables for your workspace

Update `databricks.yml` values for your environment:

- `targets.dev.workspace.host`
- `variables.pg_host` (Lakebase host)
- `variables.pg_endpoint` (Lakebase endpoint resource path)
- (optional) `variables.app_secret_scope`

## 4) Seed database objects/data

Run:

```bash
python db_setup/seed_db.py
```

What this does:

- creates `batch_release_db` if missing
- creates `batch_disposition` table
- inserts sample records (if table is empty)

## 5) Create native Postgres app role

Generate a password automatically:

```bash
python db_setup/create_native_app_role.py \
  --profile "${DATABRICKS_PROFILE:-DEFAULT}" \
  --project batch-release \
  --db-name batch_release_db \
  --role-name app_batch_release \
  --generate-password
```

Copy the printed `PGUSER` and `PGPASSWORD`.

## 6) Verify role connectivity

```bash
python db_setup/verify_native_role.py \
  --host <your-lakebase-host> \
  --db-name batch_release_db \
  --role-name app_batch_release \
  --role-password '<password>'
```

Expected output includes:

- `CONNECT_OK ...`
- `SELECT_OK ...`

## 7) Local app configuration and test

Create/update `.env`:

```bash
DATABRICKS_PROFILE=DEFAULT
PGHOST=<your-lakebase-host>
PGPORT=5432
PGDATABASE=batch_release_db
PG_ENDPOINT=<your-project-endpoint-path>
PGUSER=app_batch_release
PGPASSWORD=<password>
```

Run locally:

```bash
# terminal 1
source .venv/bin/activate
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# terminal 2
cd frontend
npm run dev
```

Open `http://localhost:5173`.

## 8) Create secret scope + store DB credentials

```bash
export APP_PGUSER=app_batch_release
export APP_PGPASSWORD='<password>'
export APP_SECRET_SCOPE=jnj-batch-release-secrets
export DATABRICKS_PROFILE=DEFAULT

bash db_setup/create_app_secrets.sh
```

This creates scope (if missing) and writes:

- key `PGUSER`
- key `PGPASSWORD`

## 9) Deploy Databricks App using secret-backed env vars

```bash
export APP_PGUSER=app_batch_release
export APP_PGPASSWORD='<password>'
export APP_SECRET_SCOPE=jnj-batch-release-secrets
export DATABRICKS_PROFILE=DEFAULT

bash db_setup/deploy_with_native_password.sh
```

What this does:

1. Ensures secret scope + keys exist
2. Runs `databricks bundle deploy` with `app_secret_scope` variable
3. Deploys app source via `databricks apps deploy`

## 10) Post-deploy verification (manual)

- Open app URL from Databricks Apps UI
- Confirm data loads
- Hit backend endpoint (if exposed): `/api/batches`
- Check app logs if needed:

```bash
databricks apps logs jnj-batch-release -p "${DATABRICKS_PROFILE:-DEFAULT}" --type app
```

## Manual Tasks Summary

You must do these manually:

- ensure Databricks + Lakebase resources exist in the target workspace
- set workspace-specific values in `databricks.yml`
- securely handle and rotate the native role password
- authenticate CLI profile with workspace access
