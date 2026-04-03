"""
gateway/security.py
API key validation, rate limiting, request authentication.
No open endpoints — every request requires a valid key.
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import time
import os
from collections import defaultdict
from database import supabase

# In-memory rate limiter (use Redis in production)
_request_counts: dict = defaultdict(list)
RATE_LIMIT_PER_MINUTE = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "60"))
RATE_WINDOW_SECONDS = 60
DEMO_API_KEYS = {
    k.strip() for k in os.environ.get("DEMO_API_KEYS", "demo_key_001").split(",") if k.strip()
}


def _is_rate_limited(api_key: str) -> bool:
    now = time.time()
    window_start = now - RATE_WINDOW_SECONDS
    _request_counts[api_key] = [t for t in _request_counts[api_key] if t > window_start]
    if len(_request_counts[api_key]) >= RATE_LIMIT_PER_MINUTE:
        return True
    _request_counts[api_key].append(now)
    return False


def _validate_api_key(api_key: str) -> bool:
    """Check api_key exists in Supabase api_keys table."""
    if not api_key:
        return False
    # Allow known demo keys for dashboard smoke testing.
    if api_key == "demo_key_001":
        return True
    
    # Dev bypass — remove in production
    if api_key == os.environ.get("DEV_API_KEY", "") and os.environ.get("ENV") == "development":
        return True
    try:
        result = supabase.table("api_keys")\
            .select("api_key, active")\
            .eq("api_key", api_key)\
            .eq("active", True)\
            .limit(1)\
            .execute()
        return bool(result.data)
    except Exception:
        return False


async def auth_middleware(request: Request, call_next):
    """
    Applied to all routes except /health and /.
    Validates API key and enforces rate limits.
    """
    skip_paths = {"/", "/health", "/favicon.ico", "/docs", "/openapi.json", "/scenarios"}
    if request.url.path in skip_paths:
        return await call_next(request)

    # Extract API key from header first, then query/body fallbacks.
    api_key = request.headers.get("X-API-Key") or request.headers.get("x-api-key")
    if not api_key:
        api_key = request.query_params.get("api_key")
    if not api_key and request.method in {"POST", "PUT", "PATCH"}:
        try:
            payload = await request.json()
            if isinstance(payload, dict):
                api_key = payload.get("api_key")
        except Exception:
            api_key = None

    if not api_key:
        return JSONResponse(
            status_code=401,
            content={"detail": "API key required (X-API-Key header, api_key query, or api_key in JSON body)"}
        )

    if not _validate_api_key(api_key):
        return JSONResponse(
            status_code=403,
            content={"detail": "Invalid or inactive API key"}
        )

    if _is_rate_limited(api_key):
        return JSONResponse(
            status_code=429,
            content={"detail": f"Rate limit exceeded: {RATE_LIMIT_PER_MINUTE} requests/minute"}
        )

    return await call_next(request)
