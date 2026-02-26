# DB Setup

This folder contains Lakebase setup scripts for the app:

- `seed_db.py` - Creates `batch_release_db`, creates `batch_disposition`, and seeds sample records.
- `grant_app_lakebase_access.py` - Grants database/schema/table privileges to the Databricks App service principal (OAuth role flow).
- `grant_app_lakebase_access.sql` - SQL-only equivalent for service principal grants.
- `create_native_app_role.py` - Creates/updates a native Postgres login role and applies grants.
- `create_native_app_role.sql` - SQL-only version of native role provisioning.
- `verify_native_role.py` - Validates role/password login and query access.
- `create_app_secrets.sh` - Creates Databricks secret scope and stores `PGUSER`/`PGPASSWORD`.
- `deploy_with_native_password.sh` - Deploy helper that provisions secrets and deploys app with secret-backed env vars.

## Quick Start

1. Create a local venv and install dependency:

```bash
python3 -m venv .venv_local
./.venv_local/bin/python -m pip install psycopg2-binary
```

2. Seed the database (if needed):

```bash
./.venv_local/bin/python db_setup/seed_db.py
```

3. Create native app role and grants:

```bash
./.venv_local/bin/python db_setup/create_native_app_role.py \
  --profile DEFAULT \
  --project batch-release \
  --db-name batch_release_db \
  --role-name app_batch_release \
  --generate-password
```

4. Verify native role credentials:

```bash
./.venv_local/bin/python db_setup/verify_native_role.py \
  --host ep-wandering-scene-d2440hao.database.us-east-1.cloud.databricks.com \
  --db-name batch_release_db \
  --role-name app_batch_release \
  --role-password '<password>'
```

## Local Runtime (Native Password)

Set these in your local `.env` (do not commit secrets):

```bash
PGUSER=app_batch_release
PGPASSWORD=<strong-password>
```

When `PGPASSWORD` is set, backend code uses native Postgres password auth.

## Databricks App Deployment (Native Password)

Yes, treat `PGPASSWORD` as a secret.

Recommended options:

1. **Create/update secret scope keys**:

```bash
export APP_PGUSER=app_batch_release
export APP_PGPASSWORD='<strong-password>'
bash db_setup/create_app_secrets.sh
```

2. **Scripted deployment**:

```bash
export APP_PGUSER=app_batch_release
export APP_PGPASSWORD='<strong-password>'
bash db_setup/deploy_with_native_password.sh
```

Notes:
- Rotate passwords regularly (`create_native_app_role.py` can update an existing role password).
- Never commit `PGPASSWORD` into repo files.
