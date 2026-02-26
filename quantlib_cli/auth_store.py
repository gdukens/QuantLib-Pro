"""
QuantLib Pro CLI — Credential Storage

Stores JWT tokens securely using the keyring library or fallback to file.
"""

import json
import os
from pathlib import Path
from typing import Optional

# Try to use keyring for secure storage
try:
    import keyring
    HAS_KEYRING = True
except ImportError:
    HAS_KEYRING = False


CONFIG_DIR = Path.home() / ".quantlib"
CREDS_FILE = CONFIG_DIR / "credentials"
SERVICE_NAME = "quantlib-pro"


def _ensure_config_dir():
    """Create config directory if it doesn't exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def save_credentials(url: str, token: str, username: str = None):
    """
    Save API credentials.

    Uses keyring if available, otherwise saves to file with restricted permissions.
    """
    _ensure_config_dir()

    data = {
        "url": url,
        "token": token,
        "username": username or "",
    }

    if HAS_KEYRING:
        try:
            keyring.set_password(SERVICE_NAME, "credentials", json.dumps(data))
            return
        except Exception:
            pass  # Fall back to file

    # File-based storage with restricted permissions
    with open(CREDS_FILE, "w") as f:
        json.dump(data, f)

    # Restrict permissions on Unix
    if os.name != "nt":
        os.chmod(CREDS_FILE, 0o600)


def load_credentials() -> Optional[dict]:
    """
    Load saved credentials.

    Returns dict with 'url', 'token', 'username' or None if not found.
    """
    if HAS_KEYRING:
        try:
            data = keyring.get_password(SERVICE_NAME, "credentials")
            if data:
                return json.loads(data)
        except Exception:
            pass

    if CREDS_FILE.exists():
        try:
            with open(CREDS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return None

    return None


def clear_credentials():
    """Remove stored credentials."""
    if HAS_KEYRING:
        try:
            keyring.delete_password(SERVICE_NAME, "credentials")
        except Exception:
            pass

    if CREDS_FILE.exists():
        CREDS_FILE.unlink()


def get_token() -> Optional[str]:
    """Get the stored JWT token or None."""
    creds = load_credentials()
    return creds.get("token") if creds else None


def get_url() -> str:
    """Get the stored API URL or default."""
    creds = load_credentials()
    return creds.get("url", "http://localhost:8000") if creds else "http://localhost:8000"
