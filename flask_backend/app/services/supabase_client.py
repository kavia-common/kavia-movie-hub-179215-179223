"""Supabase client service for server-side usage.

This module lazily initializes a singleton Supabase client using the environment
variables SUPABASE_URL and SUPABASE_SERVICE_KEY. It is intended for server-side
use only; do not expose keys to the frontend.

Environment variables required:
- SUPABASE_URL: Base URL of your Supabase project.
- SUPABASE_SERVICE_KEY: Service role key for privileged server-side access.

Usage:
    from app.services.supabase_client import get_supabase

    supabase = get_supabase()
    result = supabase.table("movies").select("*").execute()
"""
import os
import threading
import logging
import json
from typing import Optional

from supabase import Client, create_client

# Module-level lock and client for thread-safe lazy initialization
_client_lock = threading.Lock()
_client: Optional[Client] = None

_logger = logging.getLogger("app.supabase")


def _create_client() -> Client:
    """Create a new Supabase client using environment variables.

    Raises:
        RuntimeError: If required environment variables are missing or client init fails.
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")

    _logger.info(json.dumps({
        "event": "supabase_create_client_attempt",
        "has_url": bool(url),
        "has_service_key": bool(key),
    }))

    if not url or not key:
        missing = []
        if not url:
            missing.append("SUPABASE_URL")
        if not key:
            missing.append("SUPABASE_SERVICE_KEY")
        _logger.error(json.dumps({
            "event": "supabase_missing_configuration",
            "missing": missing,
        }))
        raise RuntimeError(
            f"Missing required Supabase configuration: {', '.join(missing)}. "
            "Ensure these are set on the server environment (not exposed to the frontend)."
        )

    try:
        client = create_client(url, key)
        _logger.info(json.dumps({"event": "supabase_client_initialized"}))
        return client
    except Exception as exc:
        # Do not expose secret values in logs; record structured exception and raise a safe message
        _logger.exception("Supabase client creation failed")
        raise RuntimeError("Failed to initialize Supabase client") from exc


# PUBLIC_INTERFACE
def get_supabase() -> Client:
    """Return a lazily-initialized singleton Supabase client.

    Returns:
        Client: Supabase client instance.

    Raises:
        RuntimeError: If required environment variables are missing or initialization fails.

    Notes:
        This function is safe to call from multiple threads; the client is initialized once.
    """
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                _client = _create_client()
    return _client
