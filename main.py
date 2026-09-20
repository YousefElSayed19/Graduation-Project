"""
main.py
--------
The orchestrator: the entry point that runs every scan script in sequence
against the same target and aggregates the results into one report.

Called either:
  - from the dashboard (app.py) in a separate thread so the scan runs
    in the background
  - directly from the terminal for a quick test: python main.py https://example.com
"""

import json
import sys
import time
from datetime import datetime

from scanners import security_headers, xss_scanner, sql_injection, idor_scanner, api_scanner
from scan_manager import scan_manager

# Scan execution order — add a new scanner here to include it in the pipeline
SCAN_PIPELINE = [
    ("Security Headers", security_headers),
    ("SQL Injection", sql_injection),
    ("XSS", xss_scanner),
    ("IDOR", idor_scanner),
    ("API Security", api_scanner),
]


def run_scan(target_url: str, scan_uid: str):
    """
    Runs every scanner in order against target_url, streaming logs and
    findings to scan_manager so the dashboard can follow along live.
    """
    def log(message, level="info"):
        scan_manager.log(scan_uid, message, level)

    scan_manager.set_status(scan_uid, "running")
    log(f"Starting full scan on: {target_url}")
    log(f"Scanners in the pipeline: {len(SCAN_PIPELINE)}")

    all_findings = []

    for name, module in SCAN_PIPELINE:
        log(f"───── Running scanner: {name} ─────")
        start = time.time()
        try:
            findings = module.scan(target_url, log=log)
            all_findings.extend(findings)
        except Exception as e:
            log(f"Scanner {name} crashed with an unexpected error: {e}", "error")
            findings = []

        elapsed = round(time.time() - start, 2)
        log(f"Scanner {name} finished in {elapsed}s - {len(findings)} finding(s)")

        for f in findings:
            scan_manager.add_finding(scan_uid, f)

    log(f"Scan complete. Total findings: {len(all_findings)}")
    scan_manager.set_status(scan_uid, "done")

    return all_findings


def run_from_cli(target_url: str):
    """Direct CLI run without the dashboard, for quick testing."""
    def log(message, level="info"):
        print(f"[{level.upper()}] {message}")

    all_findings = []
    for name, module in SCAN_PIPELINE:
        print(f"\n===== {name} =====")
        findings = module.scan(target_url, log=log)
        all_findings.extend(findings)

    report = {
        "target": target_url,
        "generated_at": datetime.utcnow().isoformat(),
        "findings_count": len(all_findings),
        "findings": all_findings,
    }

    filename = f"reports/report_{int(time.time())}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nReport saved to: {filename}")
    print(f"Total findings: {len(all_findings)}")
    return report


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <target_url>")
        sys.exit(1)

    run_from_cli(sys.argv[1])
