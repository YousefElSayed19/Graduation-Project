"""
sql_injection.py
------------------
Simple error-based SQLi check:
1. Collects every form on the page
2. Injects known payloads designed to break the SQL statement
3. Scans the response for well-known database error signatures
   (MySQL, PostgreSQL, SQLite...)

Note: this is a simple error-based check only. It doesn't cover Blind or
Time-based SQLi — that's a natural extension for the team to build on.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

PAYLOADS = ["'", "' OR '1'='1", "' OR 1=1--", '" OR "1"="1']

SQL_ERROR_SIGNATURES = [
    "sql syntax",
    "mysql_fetch",
    "you have an error in your sql syntax",
    "unclosed quotation mark",
    "sqlite3.operationalerror",
    "sqlalchemy",
    "pg_query",
    "odbc sql server driver",
    "syntax error",
]


def _get_forms(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    forms = []
    for form in soup.find_all("form"):
        details = {
            "action": urljoin(base_url, form.attrs.get("action", "")),
            "method": form.attrs.get("method", "get").lower(),
            "inputs": [tag.attrs.get("name") for tag in form.find_all(["input", "textarea"])
                       if tag.attrs.get("name")],
        }
        forms.append(details)
    return forms


def _looks_like_sql_error(text: str) -> bool:
    lowered = text.lower()
    return any(sig in lowered for sig in SQL_ERROR_SIGNATURES)


def scan(target_url: str, log=print):
    findings = []
    log(f"[SQLi] Starting scan on {target_url}")

    try:
        response = requests.get(target_url, timeout=10)
    except requests.RequestException as e:
        log(f"[SQLi] Failed to connect to target: {e}", "error")
        return findings

    forms = _get_forms(response.text, target_url)
    log(f"[SQLi] Found {len(forms)} form(s) on the page")

    for form in forms:
        if not form["inputs"]:
            continue

        for payload in PAYLOADS:
            data = {field: payload for field in form["inputs"]}
            log(f"[SQLi] Trying payload '{payload}' on {form['action']}")

            try:
                if form["method"] == "post":
                    res = requests.post(form["action"], data=data, timeout=10)
                else:
                    res = requests.get(form["action"], params=data, timeout=10)
            except requests.RequestException as e:
                log(f"[SQLi] Request failed: {e}", "error")
                continue

            if _looks_like_sql_error(res.text):
                log(f"[SQLi] Likely SQL Injection at {form['action']}", "warning")
                findings.append({
                    "type": "SQL Injection (Error-Based)",
                    "severity": "critical",
                    "location": form["action"],
                    "description": (
                        f"Injecting payload '{payload}' into field(s) {form['inputs']} "
                        "returned a database error, indicating the input reaches a SQL statement directly."
                    ),
                })
                break  # one indicator is enough, no need to try the rest of the payloads

    log(f"[SQLi] Scan finished - {len(findings)} likely vulnerability(ies)")
    return findings
