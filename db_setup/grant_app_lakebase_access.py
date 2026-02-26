"""Grant Lakebase DB access to the Databricks App service principal."""

import argparse
import json
import subprocess

import psycopg2


def cli_json(args: list[str], profile: str) -> dict | list:
    result = subprocess.run(
        ["databricks"] + args + ["--profile", profile, "--output", "json"],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def apply_grants(profile: str, project: str, app_name: str, db_name: str, branch: str, endpoint: str) -> None:
    endpoints = cli_json(
        ["postgres", "list-endpoints", f"projects/{project}/branches/{branch}"],
        profile,
    )
    host = endpoints[0]["status"]["hosts"]["host"]

    cred = cli_json(
        ["postgres", "generate-database-credential", f"projects/{project}/branches/{branch}/endpoints/{endpoint}"],
        profile,
    )
    token = cred["token"]

    me = cli_json(["current-user", "me"], profile)
    admin_user = me["userName"]

    app = cli_json(["apps", "get", app_name], profile)
    sp_client_id = app["service_principal_client_id"]

    print(f"Connecting as admin user: {admin_user}")
    print(f"Lakebase host: {host}")
    print(f"Applying grants for app SP: {sp_client_id}")

    conn = psycopg2.connect(
        host=host,
        port=5432,
        dbname=db_name,
        user=admin_user,
        password=token,
        sslmode="require",
    )
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("SELECT current_user")
    print("DB current_user:", cur.fetchone()[0])

    cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (sp_client_id,))
    if cur.fetchone() is None:
        cur.execute(f'CREATE ROLE "{sp_client_id}" LOGIN')
        print("Created role")
    else:
        print("Role already exists")

    cur.execute(f'GRANT CONNECT ON DATABASE "{db_name}" TO "{sp_client_id}"')
    cur.execute(f'GRANT USAGE ON SCHEMA public TO "{sp_client_id}"')
    cur.execute(f'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO "{sp_client_id}"')
    cur.execute(f'GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO "{sp_client_id}"')
    cur.execute(
        f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "{sp_client_id}"'
    )
    cur.execute(
        f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO "{sp_client_id}"'
    )
    print("Applied grants and default privileges")

    cur.close()
    conn.close()
    print("Done")


def main() -> None:
    parser = argparse.ArgumentParser(description="Grant Lakebase DB privileges to Databricks App SP.")
    parser.add_argument("--profile", default="DEFAULT")
    parser.add_argument("--project", default="batch-release")
    parser.add_argument("--app-name", default="jnj-batch-release")
    parser.add_argument("--db-name", default="batch_release_db")
    parser.add_argument("--branch", default="production")
    parser.add_argument("--endpoint", default="primary")
    args = parser.parse_args()

    apply_grants(
        profile=args.profile,
        project=args.project,
        app_name=args.app_name,
        db_name=args.db_name,
        branch=args.branch,
        endpoint=args.endpoint,
    )


if __name__ == "__main__":
    main()
