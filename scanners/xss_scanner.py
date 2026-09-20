"""
xss_scanner.py
---------------
Simple Reflected XSS check:
1. Collects every <form> on the page
2. Injects a distinctive, harmless payload (alert with a unique marker)
   into each field
3. Submits the form and reads the response
4. If the payload comes back completely unescaped in the HTML, that's a
   strong indicator the field is vulnerable to XSS
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

PAYLOAD = "<script>alert('XSS_TEST_SCANNER')</script>"


def _get_forms(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    forms = []
    for form in soup.find_all("form"):
        details = {
            "action": urljoin(base_url, form.attrs.get("action", "")),
            "method": form.attrs.get("method", "get").lower(),
            "inputs": [],
        }
        for tag in form.find_all(["input", "textarea"]):
            name = tag.attrs.get("name")
            if name:
                details["inputs"].append(name)
        forms.append(details)
    return forms


def scan(target_url: str, log=print):
    findings = []
    log(f"[XSS] Starting scan on {target_url}")

    try:
        response = requests.get(target_url, timeout=10)
    except requests.RequestException as e:
        log(f"[XSS] Failed to connect to target: {e}", "error")
        return findings

    forms = _get_forms(response.text, target_url)
    log(f"[XSS] Found {len(forms)} form(s) on the page")

    for form in forms:
        if not form["inputs"]:
            continue

        data = {field: PAYLOAD for field in form["inputs"]}
        log(f"[XSS] Trying injection on {form['action']} (method={form['method']})")

        try:
            if form["method"] == "post":
                res = requests.post(form["action"], data=data, timeout=10)
            else:
                res = requests.get(form["action"], params=data, timeout=10)
        except requests.RequestException as e:
            log(f"[XSS] Request failed: {e}", "error")
            continue

        if PAYLOAD in res.text:
            log(f"[XSS] Likely XSS vulnerability at {form['action']}", "warning")
            findings.append({
                "type": "Reflected XSS",
                "severity": "high",
                "location": form["action"],
                "description": (
                    f"Field(s) {form['inputs']} reflect the payload without escaping, "
                    "allowing JavaScript injection."
                ),
            })

    log(f"[XSS] Scan finished - {len(findings)} likely vulnerability(ies)")
    return findings
