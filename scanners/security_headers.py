"""
security_headers.py
--------------------
The simplest scanner in the project: sends a single GET request to the
target and checks for well-known HTTP security headers. Missing headers
aren't a direct exploit, but they're a misconfiguration signal that shows
up in every real security assessment.
"""

import requests

REQUIRED_HEADERS = {
    "X-Content-Type-Options": "Prevents the browser from MIME-sniffing the response content type",
    "X-Frame-Options": "Prevents the site from being embedded in an iframe (Clickjacking)",
    "Content-Security-Policy": "Controls which sources scripts and content may load from",
    "Strict-Transport-Security": "Forces the browser to use HTTPS only",
}


def scan(target_url: str, log=print):
    findings = []
    log(f"[Security-Headers] Starting scan on {target_url}")

    try:
        response = requests.get(target_url, timeout=10)
    except requests.RequestException as e:
        log(f"[Security-Headers] Failed to connect to target: {e}", "error")
        return findings

    headers = response.headers
    for header_name, description in REQUIRED_HEADERS.items():
        if header_name not in headers:
            log(f"[Security-Headers] Missing header '{header_name}'", "warning")
            findings.append({
                "type": "Missing Security Header",
                "severity": "low",
                "location": target_url,
                "description": f"The {header_name} header is missing. {description}",
            })
        else:
            log(f"[Security-Headers] '{header_name}' present ✓")

    log(f"[Security-Headers] Scan finished - {len(findings)} finding(s)")
    return findings
