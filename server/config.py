import os
import json
import base64
from urllib import request, error
from databricks.sdk import WorkspaceClient

IS_DATABRICKS_APP = bool(os.environ.get("DATABRICKS_APP_NAME"))

_workspace_client = None


def get_workspace_client() -> WorkspaceClient:
    global _workspace_client
    if _workspace_client is None:
        if IS_DATABRICKS_APP:
            _workspace_client = WorkspaceClient()
        else:
            profile = os.environ.get("DATABRICKS_PROFILE", "DEFAULT")
            _workspace_client = WorkspaceClient(profile=profile)
    return _workspace_client


def get_oauth_token() -> str:
    client = get_workspace_client()
    auth_headers = client.config.authenticate()
    if auth_headers and "Authorization" in auth_headers:
        return auth_headers["Authorization"].replace("Bearer ", "")
    raise RuntimeError("Failed to get OAuth token")


def use_native_postgres_password() -> bool:
    """Return True when static Postgres password auth is configured."""
    return bool(os.environ.get("PGPASSWORD"))


def _decode_jwt_sub(token: str) -> str:
    """Decode JWT payload and return the subject claim."""
    parts = token.split(".")
    if len(parts) < 2:
        raise RuntimeError("Invalid credential token format")
    payload = parts[1]
    payload += "=" * (-len(payload) % 4)
    decoded = base64.urlsafe_b64decode(payload.encode("utf-8")).decode("utf-8")
    data = json.loads(decoded)
    sub = data.get("sub")
    if not sub:
        raise RuntimeError("Credential token missing subject")
    return sub


def _resolve_postgres_user(client: WorkspaceClient, token: str) -> str:
    """
    Resolve Postgres username for Lakebase auth.

    Priority:
    1) Explicit PGUSER override
    2) Databricks current principal identity
    3) JWT subject fallback
    """
    explicit_user = os.environ.get("PGUSER")
    if explicit_user:
        return explicit_user

    try:
        me = client.current_user.me()
        # user_name is the canonical principal name for both local users and app principals.
        identity_user = getattr(me, "user_name", None)
        if identity_user:
            return identity_user
    except Exception:
        # Fall back to token-derived identity if IAM lookup is unavailable.
        pass

    return _decode_jwt_sub(token)


def get_postgres_auth() -> tuple[str, str]:
    """
    Return (password, username) for Postgres connectivity.

    If PGPASSWORD is set, use native Postgres password auth.
    Otherwise, generate a Lakebase OAuth database credential.
    """
    native_password = os.environ.get("PGPASSWORD")
    if native_password:
        user = os.environ.get("PGUSER")
        if not user:
            raise RuntimeError("PGUSER is required when using PGPASSWORD")
        return native_password, user

    endpoint = os.environ.get("PG_ENDPOINT")
    if not endpoint:
        raise RuntimeError("PG_ENDPOINT is required for Lakebase authentication")

    client = get_workspace_client()
    workspace_token = get_oauth_token()
    url = f"{client.config.host}/api/2.0/postgres/credentials"
    req = request.Request(
        url=url,
        method="POST",
        data=json.dumps({"endpoint": endpoint}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {workspace_token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Failed to generate Lakebase credential: {e.code} {detail}") from e

    token = body.get("token")
    if not token:
        raise RuntimeError("Lakebase credential response missing token")

    user = _resolve_postgres_user(client, token)
    return token, user
