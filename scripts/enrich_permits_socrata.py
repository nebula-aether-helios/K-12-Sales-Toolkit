#!/usr/bin/env python3
"""Enrich CSV of prospects with permit data from a Socrata dataset.

This script supports a fast dry-run mode for quick iteration (no network, limited rows)
and a live mode that queries a Socrata dataset endpoint.

Usage:
  python scripts/enrich_permits_socrata.py --csv <csv_path> --endpoint <socrata_api_endpoint> [--limit N] [--run]

Flags:
  --run    Execute live Socrata queries. Without --run the script performs a dry-run (no network) for fast iteration.
  --limit N   Limit number of rows to process (dry-run or live).

Reads `SOCRATA_APP_TOKEN` from .env when running live.
"""
import sys
import csv
import time
import json
from datetime import datetime
import argparse
import requests
import concurrent.futures
import tempfile
import os
from datetime import timezone

ENV_PATH = ".env"


def load_env(path):
    env = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                k, v = line.split("=", 1)
                v = v.strip().strip('"')
                env[k.strip()] = v
    except FileNotFoundError:
        pass
    return env


def query_socrata(session, endpoint, app_token, q, limit=5):
    headers = {}
    if app_token:
        headers["X-App-Token"] = app_token
    params = {"$limit": limit, "q": q}
    resp = session.get(endpoint, params=params, headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.json()


def extract_permit_summary(records):
    if not records:
        return 0, 0.0, None, []
    count = len(records)
    total_value = 0.0
    last_dates = []
    types = set()
    for r in records:
        for k in ("total_estimated_cost", "value", "permit_value", "estimated_cost", "estimatedcost"):
            if k in r and r[k] not in (None, ""):
                try:
                    total_value += float(r[k])
                except Exception:
                    pass
        for k in ("issue_date", "issued_date", "permit_issued_date", "issued_dt", "issued"):
            if k in r and r[k]:
                last_dates.append(r[k])
        for k in ("permit_type", "type", "work_type", "permit_description", "description"):
            if k in r and r[k]:
                types.add(str(r[k]))
    last_date = sorted(last_dates)[-1] if last_dates else None
    return count, total_value, last_date, list(types)


def dry_query_simulator(q):
    # Fast-fail simulator: return empty for most queries, or a small fake permit for demo
    if not q:
        return []
    # If query contains 'ROOF' or 'roof' simulate a permit
    if "roof" in q.lower():
        return [{"permit_type": "Roofing", "estimated_cost": 12000, "issued_date": "2025-11-01"}]
    return []


def run(csv_path, endpoint, limit=None, live=False, workers=8, sleep=True):
    env = load_env(ENV_PATH)
    app_token = env.get("SOCRATA_APP_TOKEN")

    # Read input rows lazily
    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    add_fields = ["permit_active_count", "permit_total_value", "permit_last_issued_date", "permit_types", "permit_enriched_at"]
    for f in add_fields:
        if f not in fieldnames:
            fieldnames.append(f)

    indices = list(range(len(rows))) if limit is None else list(range(min(limit, len(rows))))

    session = requests.Session()

    def worker(idx):
        row = rows[idx]
        name = (row.get("business_name") or row.get("business") or "").strip()
        street = (row.get("address_street") or row.get("address") or "").strip()
        city = (row.get("address_city") or row.get("city") or "").strip()
        q = " ".join([name, street, city]).strip()
        if not q:
            return idx, "skip", {}
        try:
            if live:
                records = query_socrata(session, endpoint, app_token, q)
            else:
                records = dry_query_simulator(q)
        except Exception as e:
            return idx, "error", {"error": str(e)}

        count, total_value, last_date, types = extract_permit_summary(records)
        summary = {
            "permit_active_count": str(count),
            "permit_total_value": str(total_value),
            "permit_last_issued_date": last_date or "",
            "permit_types": ", ".join(types),
            "permit_enriched_at": datetime.now(timezone.utc).isoformat(),
        }
        return idx, "ok", summary

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(worker, idx): idx for idx in indices}
        for fut in concurrent.futures.as_completed(futures):
            idx = futures[fut]
            try:
                res = fut.result()
            except Exception as e:
                print(f"[{idx}] worker exception: {e}")
                results.append((idx, "error", {"error": str(e)}))
                continue
            print(f"[{res[0]}] -> {res[1]}")
            results.append(res)
            if live and sleep:
                # short pause to avoid aggressive hammering
                time.sleep(0.05)

    # Apply results and write file when live
    if live:
        for idx, status, summary in results:
            if status != "ok":
                continue
            rows[idx].update(summary)
        # write to temp file then replace
        fd, tmp_path = tempfile.mkstemp(prefix="enriched_", suffix=".csv", dir=os.path.dirname(csv_path))
        os.close(fd)
        with open(tmp_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)
        os.replace(tmp_path, csv_path)
        print("WROTE:", csv_path)
    else:
        print("Dry-run complete. No file changes made.")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--csv", required=True)
    p.add_argument("--endpoint", required=True)
    p.add_argument("--limit", type=int)
    p.add_argument("--run", action="store_true", help="Perform live queries")
    p.add_argument("--workers", type=int, default=8, help="Number of concurrent workers for live queries")
    return p.parse_args()


def main():
    args = parse_args()
    run(args.csv, args.endpoint, limit=args.limit, live=args.run)


if __name__ == "__main__":
    main()
