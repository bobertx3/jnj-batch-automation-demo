-- Usage:
--   psql ... -v role_name='app_batch_release' -v role_password='CHANGEME' -v db_name='batch_release_db' -f create_native_app_role.sql

DO $$
DECLARE
    role_name text := :'role_name';
    role_password text := :'role_password';
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = role_name) THEN
        EXECUTE format('CREATE ROLE %I LOGIN PASSWORD %L', role_name, role_password);
    ELSE
        EXECUTE format('ALTER ROLE %I WITH LOGIN PASSWORD %L', role_name, role_password);
    END IF;
END$$;

SELECT format('GRANT CONNECT ON DATABASE %I TO %I', :'db_name', :'role_name') \gexec
SELECT format('GRANT USAGE ON SCHEMA public TO %I', :'role_name') \gexec
SELECT format('GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO %I', :'role_name') \gexec
SELECT format('GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO %I', :'role_name') \gexec
SELECT format('ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO %I', :'role_name') \gexec
SELECT format('ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO %I', :'role_name') \gexec
