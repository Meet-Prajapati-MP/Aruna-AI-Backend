"""
app/middleware/rate_limiter.py
───────────────────────────────
FIX B6: get_remote_address returns Railway's reverse-proxy IP for all clients.

Original bug:
  limiter = Limiter(key_func=get_remote_address)
  → Railway (and most cloud hosts) sit behind a load balancer.
  → request.client.host is always the proxy's internal IP.
  → Every single user shares the same rate-limit bucket → rate limiting is useless.

Fix:
  Use X-Forwarded-For header, which Railway / Nginx sets to the real client IP.
  Take the FIRST entry (rightmost entries can be spoofed by clients).
  Fall back to direct connection IP if header is missing.
"""

import os

from fastapi import Request
from slowapi import Limiter


def get_real_client_ip(request: Request) -> str:
    """
    Extract the real client IP address, respecting proxy headers.

    Railway and most cloud platforms set X-Forwarded-For.
    The format is: "client, proxy1, proxy2" — we want the first value (client).
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the leftmost (original client) IP
        client_ip = forwarded_for.split(",")[0].strip()
        if client_ip:
            return client_ip

    # Fallback: direct connection (works in local dev)
    if request.client:
        return request.client.host

    return "unknown"


# ── Global limiter instance ───────────────────────────────────────────────────
_rate_limit = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "20"))

limiter = Limiter(
    key_func=get_real_client_ip,   # FIX B6: real IP, not proxy IP
    default_limits=[f"{_rate_limit}/minute"],
)
