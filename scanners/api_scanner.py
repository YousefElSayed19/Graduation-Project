"""
api_scanner.py
------------------
Simplified check of common API endpoints:
1. Tries well-known API paths (e.g. /api/users, /api/admin) with no
   Authorization header
2. If it gets back 200 with JSON data instead of 401/403, that's an
   endpoint leaking data with no protection

This isn't an exhaustive API scan, but it covers one of the most common
mistakes: a dev team forgetting to add auth middleware to a new route.
"""

import requests
from urllib.parse import urljoin

COMMON_API_PATHS = [
    "/api/users",
    "/api/user",
    "/api/admin",
    "/api/config",
    "/api/accounts",
    "/api/v1/users",
    "/api/data",
]


def scan(target_url: str, log=print):
    findings = []
    log(f"[API] Starting scan on {target_url}")

    for path in COMMON_API_PATHS:
        full_url = urljoin(target_url, path)
        log(f"[API] Trying {full_url}")

        try:
            res = requests.get(full_url, timeout=8)
        except requests.RequestException as e:
            log(f"[API] Could not reach {full_url}: {e}", "error")
            continue

        content_type = res.headers.get("Content-Type", "")

        if res.status_code == 200 and "json" in content_type:
            log(f"[API] Unprotected endpoint exposed: {full_url}", "warning")
            findings.append({
                "type": "Exposed API Endpoint",
                "severity": "high",
                "location": full_url,
                "description": (
                    "This endpoint returned JSON data with status 200 and no Authorization "
                    "header. Confirm whether it's meant to be public or should require authentication."
                ),
            })
        elif res.status_code in (401, 403):
            log(f"[API] {full_url} is protected (status {res.status_code}) ✓")
        else:
            log(f"[API] {full_url} - status {res.status_code}")

    log(f"[API] Scan finished - {len(findings)} finding(s)")
    return findings
