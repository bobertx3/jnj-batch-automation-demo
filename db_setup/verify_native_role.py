"""Verify native Postgres role connectivity and query access."""

import argparse

import psycopg2


def verify(host: str, port: int, db_name: str, role_name: str, role_password: str) -> None:
    conn = psycopg2.connect(
        host=host,
        port=port,
        dbname=db_name,
        user=role_name,
        password=role_password,
        sslmode="require",
        connect_timeout=10,
    )
    cur = conn.cursor()
    cur.execute("SELECT current_user, current_database()")
    who, db = cur.fetchone()
    print(f"CONNECT_OK user={who} db={db}")
    cur.execute("SELECT COUNT(*) FROM batch_disposition")
    count = cur.fetchone()[0]
    print(f"SELECT_OK batch_disposition_count={count}")
    cur.close()
    conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify native Postgres role against Lakebase.")
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, default=5432)
    parser.add_argument("--db-name", default="batch_release_db")
    parser.add_argument("--role-name", required=True)
    parser.add_argument("--role-password", required=True)
    args = parser.parse_args()
    verify(args.host, args.port, args.db_name, args.role_name, args.role_password)


if __name__ == "__main__":
    main()
