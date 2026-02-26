"""Create/update a native Postgres login role and grants for Lakebase."""

import argparse
import getpass
import json
import secrets
import string
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


def generate_password(length: int = 24) -> str:
    alphabet = string.ascii_letters + string.digits + "_-"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def apply_role(
    profile: str,
    project: str,
    db_name: str,
    role_name: str,
    role_password: str,
    branch: str,
    endpoint: str,
) -> None:
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
    admin_user = cli_json(["current-user", "me"], profile)["userName"]

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

    cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (role_name,))
    if cur.fetchone() is None:
        cur.execute(f'CREATE ROLE "{role_name}" LOGIN PASSWORD %s', (role_password,))
        print(f"Created role: {role_name}")
    else:
        cur.execute(f'ALTER ROLE "{role_name}" WITH LOGIN PASSWORD %s', (role_password,))
        print(f"Updated password for existing role: {role_name}")

    cur.execute(f'GRANT CONNECT ON DATABASE "{db_name}" TO "{role_name}"')
    cur.execute(f'GRANT USAGE ON SCHEMA public TO "{role_name}"')
    cur.execute(f'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO "{role_name}"')
    cur.execute(f'GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO "{role_name}"')
    cur.execute(
        f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "{role_name}"'
    )
    cur.execute(
        f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO "{role_name}"'
    )

    cur.close()
    conn.close()

    print("")
    print("Native role setup complete.")
    print(f"PGUSER={role_name}")
    print(f"PGPASSWORD={role_password}")
    print("Store PGPASSWORD in app secrets, not in git.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create/update a native Postgres app role in Lakebase.")
    parser.add_argument("--profile", default="DEFAULT")
    parser.add_argument("--project", default="batch-release")
    parser.add_argument("--db-name", default="batch_release_db")
    parser.add_argument("--branch", default="production")
    parser.add_argument("--endpoint", default="primary")
    parser.add_argument("--role-name", default="app_batch_release")
    parser.add_argument("--role-password", default="")
    parser.add_argument("--generate-password", action="store_true")
    args = parser.parse_args()

    if args.generate_password:
        password = generate_password()
    elif args.role_password:
        password = args.role_password
    else:
        password = getpass.getpass(f"Password for role {args.role_name}: ")

    apply_role(
        profile=args.profile,
        project=args.project,
        db_name=args.db_name,
        role_name=args.role_name,
        role_password=password,
        branch=args.branch,
        endpoint=args.endpoint,
    )


if __name__ == "__main__":
    main()
