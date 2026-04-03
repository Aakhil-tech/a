"""
gateway/security.py
API key validation and rate limiting.
"""
from fastapi import Request
from fastapi.responses import JSONResponse
import time
import os
from collections import defaultdict
from database import supabase

_request_counts: dict = defaultdict(list)
RATE_LIMIT_PER_MINUTE = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "120"))
RATE_WINDOW_SECONDS = 60

# Always-allowed keys — demo_key_001 is hardcoded as fallback
# Set DEMO_API_KEYS=key1,key2 in Render env to add more
_HARDCODED_DEMO_KEYS = {"demo_key_001", "test123", "test_key_001"}

DEMO_API_KEYS = _HARDCODED_DEMO_KEYS | {
    k.strip()
    for k in os.environ.get("DEMO_API_KEYS", "").split(",")
    if k.strip()
}

# Paths that never require auth
SKIP_PATHS = {
    "/", "/health", "/favicon.ico",
    "/docs", "/openapi.json", "/redoc",
    "/scenarios",
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
    if not api_key:
        return False
    # Hardcoded demo keys always pass
    if api_key in DEMO_API_KEYS:
        return True
    # Check Supabase api_keys table
    try:
        result = supabase.table("api_keys")\
            .select("api_key, active")\
            .eq("api_key", api_key)\
            .eq("active", True)\
            .limit(1)\
            .execute()
        return bool(result.data)
    except Exception:
        # If Supabase is unreachable, fail open for demo keys only
        return False

async def auth_middleware(request: Request, call_next):
    """
    Applied to all routes except skip_paths.
    
    Key extraction order:
    1. X-API-Key header
    2. api_key query param (for GET requests)
    3. Request body is NOT read here — body reading in middleware
       breaks the route handler. POST body keys are validated
       inside the route handlers themselves after body is parsed.
    """
    if request.url.path in SKIP_PATHS:
        return await call_next(request)

    # Extract from header first
    api_key = (
        request.headers.get("X-API-Key")
        or request.headers.get("x-api-key")
    )

    # Extract from query params (works for GET and POST)
    if not api_key:
        api_key = request.query_params.get("api_key")

    # For POST/PUT requests with no header/query key:
    # We CANNOT read the body here (it breaks the route handler).
    # Instead — allow the request through if it's a POST to a known
    # endpoint, and let the route handler validate the key from the body.
    # The route handlers already raise 400/422 if api_key is missing.
    if not api_key and request.method in {"POST", "PUT", "PATCH"}:
        # Allow through — route handler will validate body api_key
        return await call_next(request)

    # At this point: GET request with no api_key at all
    if not api_key:
        return JSONResponse(
            status_code=401,
            content={"detail": "API key required (X-API-Key header or api_key query param)"}
        )

    if not _validate_api_key(api_key):
        return JSONResponse(
            status_code=403,
            content={"detail": f"Invalid or inactive API key: {api_key[:8]}..."}
        )

    if _is_rate_limited(api_key):
        return JSONResponse(
            status_code=429,
            content={"detail": f"Rate limit exceeded: {RATE_LIMIT_PER_MINUTE} req/min"}
        )

    return await call_next(request)
