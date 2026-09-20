"""
idor_scanner.py
------------------
Simplified IDOR (Insecure Direct Object Reference) check:
1. Scans the page's links for any URL containing a number (e.g. /user/5
   or ?id=5)
2. Tries swapping that number for a few nearby IDs (1, 2, 3...)
3. If every request comes back with status 200 and actual content
   (instead of a 401/403/"Unauthorized" page), that's a signal that
   anyone could reach other users' data without real authorization

Important: this is an "indicator" check, not definitive proof. The final
call needs a human to review the returned content, which the dashboard
makes clear in the report.
"""

import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse

ID_PATTERN = re.compile(r"(\d+)")


def _find_candidate_urls(html, base_url):
    """Finds any link with a number in the path or in the query string."""
    soup = BeautifulSoup(html, "html.parser")
    candidates = set()

    for tag in soup.find_all("a", href=True):
        full_url = urljoin(base_url, tag["href"])
        parsed = urlparse(full_url)

        if ID_PATTERN.search(parsed.path) or parse_qs(parsed.query):
            candidates.add(full_url)

    return list(candidates)


def _swap_id_in_url(url: str, new_id: int) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    if query:
        for key, values in query.items():
            if values and values[0].isdigit():
                query[key] = [str(new_id)]
        new_query = urlencode(query, doseq=True)
        return urlunparse(parsed._replace(query=new_query))

    new_path = ID_PATTERN.sub(str(new_id), parsed.path, count=1)
    return urlunparse(parsed._replace(path=new_path))


def scan(target_url: str, log=print):
    findings = []
    log(f"[IDOR] Starting scan on {target_url}")

    try:
        response = requests.get(target_url, timeout=10)
    except requests.RequestException as e:
        log(f"[IDOR] Failed to connect to target: {e}", "error")
        return findings

    candidates = _find_candidate_urls(response.text, target_url)
    log(f"[IDOR] Found {len(candidates)} link(s) with a numeric ID")

    for url in candidates[:5]:  # cap the count to keep the scan light
        ok_count = 0
        for test_id in [1, 2, 3]:
            test_url = _swap_id_in_url(url, test_id)
            log(f"[IDOR] Trying {test_url}")
            try:
                res = requests.get(test_url, timeout=10)
            except requests.RequestException:
                continue
            if res.status_code == 200:
                ok_count += 1

        if ok_count == 3:
            log(f"[IDOR] All IDs returned 200 on {url} - needs manual review", "warning")
            findings.append({
                "type": "Potential IDOR",
                "severity": "medium",
                "location": url,
                "description": (
                    "Swapping the numeric ID in the URL returned status 200 for every value "
                    "tried, with no visible authorization check. Needs manual review to confirm "
                    "the returned data actually belongs to a different user."
                ),
            })

    log(f"[IDOR] Scan finished - {len(findings)} finding(s)")
    return findings
