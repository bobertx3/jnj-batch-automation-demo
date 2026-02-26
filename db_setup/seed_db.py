"""Seed the Lakebase batch_release_db with batch_disposition table and sample data."""
import json
import subprocess
import psycopg2

PROFILE = "DEFAULT"
PROJECT = "batch-release"


def cli_json(args: list[str]) -> dict | list:
    result = subprocess.run(
        ["databricks"] + args + ["--profile", PROFILE, "--output", "json"],
        capture_output=True, text=True,
    )
    return json.loads(result.stdout)


def get_connection(dbname="postgres"):
    endpoints = cli_json(["postgres", "list-endpoints", f"projects/{PROJECT}/branches/production"])
    host = endpoints[0]["status"]["hosts"]["host"]

    cred = cli_json(["postgres", "generate-database-credential",
                     f"projects/{PROJECT}/branches/production/endpoints/primary"])
    token = cred["token"]

    user_info = cli_json(["current-user", "me"])
    email = user_info["userName"]

    return psycopg2.connect(host=host, port=5432, database=dbname, user=email, password=token, sslmode="require")


# Step 1: Create the database
print("Creating database batch_release_db...")
conn = get_connection("postgres")
conn.autocommit = True
cur = conn.cursor()
cur.execute("SELECT 1 FROM pg_database WHERE datname = 'batch_release_db'")
if not cur.fetchone():
    cur.execute("CREATE DATABASE batch_release_db")
    print("  Database created.")
else:
    print("  Database already exists.")
cur.close()
conn.close()

# Step 2: Create table and seed data
print("Creating table and seeding data...")
conn = get_connection("batch_release_db")
conn.autocommit = True
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS batch_disposition (
    batch_id TEXT PRIMARY KEY,
    drug_name TEXT NOT NULL,
    batch_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Pending',
    temp_actual FLOAT NOT NULL,
    temp_check BOOLEAN NOT NULL,
    purity_actual FLOAT NOT NULL,
    purity_check BOOLEAN NOT NULL,
    manufactured_date DATE NOT NULL,
    expiry_date DATE NOT NULL,
    cycle_time_hours FLOAT NOT NULL,
    last_updated TIMESTAMP NOT NULL DEFAULT NOW(),
    exceptions TEXT,
    signed_by TEXT
)
""")
print("  Table created.")

# Check if data already exists
cur.execute("SELECT COUNT(*) FROM batch_disposition")
count = cur.fetchone()[0]
if count > 0:
    print(f"  Table already has {count} rows. Skipping seed.")
else:
    # Seed 25 Stelara batches
    batches = [
        # 15 batches that pass all checks (~60%)
        ("BD-000401", "Stelara", "STL-2025-001", "Pending", 37.02, True, 99.3, True, "2025-11-01", "2027-11-01", 48.2, None),
        ("BD-000402", "Stelara", "STL-2025-002", "Released", 36.95, True, 99.1, True, "2025-11-05", "2027-11-05", 52.1, None),
        ("BD-000403", "Stelara", "STL-2025-003", "Released", 37.10, True, 98.8, True, "2025-11-10", "2027-11-10", 45.7, None),
        ("BD-000404", "Stelara", "STL-2025-004", "Pending", 36.88, True, 99.5, True, "2025-11-15", "2027-11-15", 50.3, None),
        ("BD-000405", "Stelara", "STL-2025-005", "Released", 37.15, True, 98.6, True, "2025-11-20", "2027-11-20", 47.8, None),
        ("BD-000406", "Stelara", "STL-2025-006", "Pending", 36.92, True, 99.0, True, "2025-12-01", "2027-12-01", 53.4, None),
        ("BD-000407", "Stelara", "STL-2025-007", "Released", 37.05, True, 98.9, True, "2025-12-05", "2027-12-05", 44.6, None),
        ("BD-000408", "Stelara", "STL-2025-008", "Pending", 37.20, True, 99.2, True, "2025-12-10", "2027-12-10", 49.1, None),
        ("BD-000409", "Stelara", "STL-2025-009", "Released", 36.85, True, 98.7, True, "2025-12-15", "2027-12-15", 51.5, None),
        ("BD-000410", "Stelara", "STL-2025-010", "Pending", 37.08, True, 99.4, True, "2025-12-20", "2027-12-20", 46.3, None),
        ("BD-000411", "Stelara", "STL-2026-001", "Released", 36.98, True, 98.5, True, "2026-01-05", "2028-01-05", 55.2, None),
        ("BD-000412", "Stelara", "STL-2026-002", "Pending", 37.12, True, 99.6, True, "2026-01-10", "2028-01-10", 43.8, None),
        ("BD-000413", "Stelara", "STL-2026-003", "Released", 36.90, True, 98.4, True, "2026-01-15", "2028-01-15", 50.7, None),
        ("BD-000414", "Stelara", "STL-2026-004", "Pending", 37.18, True, 99.1, True, "2026-01-20", "2028-01-20", 47.2, None),
        ("BD-000415", "Stelara", "STL-2026-005", "Released", 36.96, True, 98.8, True, "2026-01-25", "2028-01-25", 52.9, None),
        # 6 batches with temp exceptions (~25%)
        ("BD-000416", "Stelara", "STL-2026-006", "Pending", 37.72, False, 99.1, True, "2026-02-01", "2028-02-01", 58.3, "Temperature excursion: 37.72°C"),
        ("BD-000417", "Stelara", "STL-2026-007", "Pending", 36.38, False, 98.9, True, "2026-02-05", "2028-02-05", 62.1, "Temperature excursion: 36.38°C"),
        ("BD-000418", "Stelara", "STL-2026-008", "Rejected", 38.10, False, 99.0, True, "2026-02-08", "2028-02-08", 71.5, "Temperature excursion: 38.10°C"),
        ("BD-000419", "Stelara", "STL-2026-009", "Pending", 37.65, False, 98.7, True, "2026-02-10", "2028-02-10", 55.8, "Temperature excursion: 37.65°C"),
        ("BD-000420", "Stelara", "STL-2026-010", "Pending", 36.22, False, 99.3, True, "2026-02-12", "2028-02-12", 60.4, "Temperature excursion: 36.22°C"),
        ("BD-000421", "Stelara", "STL-2026-011", "Pending", 37.58, False, 98.6, True, "2026-02-14", "2028-02-14", 54.2, "Temperature excursion: 37.58°C"),
        # 4 batches with purity exceptions (~15%)
        ("BD-000422", "Stelara", "STL-2026-012", "Pending", 37.05, True, 97.2, False, "2026-02-15", "2028-02-15", 65.3, "Purity below threshold: 97.2%"),
        ("BD-000423", "Stelara", "STL-2026-013", "Pending", 36.92, True, 96.8, False, "2026-02-17", "2028-02-17", 68.7, "Purity below threshold: 96.8%"),
        ("BD-000424", "Stelara", "STL-2026-014", "Rejected", 37.10, True, 95.4, False, "2026-02-19", "2028-02-19", 72.1, "Purity below threshold: 95.4%"),
        ("BD-000425", "Stelara", "STL-2026-015", "Pending", 36.88, True, 97.6, False, "2026-02-21", "2028-02-21", 59.8, "Purity below threshold: 97.6%"),
    ]

    cur.executemany("""
        INSERT INTO batch_disposition
        (batch_id, drug_name, batch_name, status, temp_actual, temp_check, purity_actual, purity_check,
         manufactured_date, expiry_date, cycle_time_hours, exceptions)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, batches)
    print(f"  Seeded {len(batches)} batches.")

cur.execute("SELECT COUNT(*), COUNT(*) FILTER (WHERE status='Pending'), COUNT(*) FILTER (WHERE status='Released'), COUNT(*) FILTER (WHERE status='Rejected') FROM batch_disposition")
total, pending, released, rejected = cur.fetchone()
print(f"  Total: {total} | Pending: {pending} | Released: {released} | Rejected: {rejected}")

cur.close()
conn.close()
print("Done!")
