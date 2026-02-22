"""Migration script: ingest legacy ferengi outputs into normalized enrichment DB.

Usage:
  python scripts/migrate_to_enrichment_db.py --dry-run
  python scripts/migrate_to_enrichment_db.py --apply --target ./outputs/enrichment.db --legacy-db ./outputs/ferengi_enrichment.db

This script is conservative by default: --dry-run only reports counts. --apply writes to target DB.
"""
import argparse
import json
import os
import sys
import sqlite3
from glob import glob
from pathlib import Path
from typing import Any, Dict, List

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def parse_dirty_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    lines = text.splitlines()
    # Trim up to 10 trailing lines trying to recover clean JSON
    for trim in range(1, min(len(lines), 10) + 1):
        candidate = "\n".join(lines[: len(lines) - trim]).strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    # final attempt: try to find first { and last }
    first = text.find("{")
    last = text.rfind("}")
    if first != -1 and last != -1 and last > first:
        try:
            return json.loads(text[first : last + 1])
        except Exception:
            pass
    raise json.JSONDecodeError("Cannot parse dirty JSON", text, 0)


def find_manifest_files(repo_root: Path) -> List[Path]:
    p = repo_root / "catalog_api" / "sources"
    files = []
    if p.exists():
        files.extend([f for f in p.glob("*.json")])
    # ferengi_master_catalog.json endpoints
    fc = repo_root / "outputs" / "ferengi_master_catalog.json"
    if fc.exists():
        files.append(fc)
    return files


def load_manifests_preview(files: List[Path]) -> List[Dict[str, Any]]:
    manifests = []
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
            doc = parse_dirty_json(text)
            manifests.append({"path": str(f), "doc": doc})
        except Exception as e:
            print(f"WARN: failed to parse manifest {f}: {e}")
    return manifests


def count_legacy_rows(legacy_db_path: Path) -> Dict[str, int]:
    if not legacy_db_path.exists():
        return {"contractors": 0, "possible_results": 0}
    conn = sqlite3.connect(str(legacy_db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM contractors")
    contractors = cur.fetchone()[0]

    # approximate results by checking known source columns per row
    source_mappings = {
        "google_places": [
            "gp_place_id",
            "gp_website",
            "gp_rating",
            "gp_review_count",
            "gp_phone_verified",
            "gp_hours",
            "gp_lat",
            "gp_lng",
        ],
        "osha_enforcement": [
            "osha_inspection_count",
            "osha_violation_count",
            "osha_penalty_total",
            "osha_last_inspection_date",
        ],
        "arcgis_permits": ["permit_active_count", "permit_total_value", "permit_last_issued_date"],
        "craigslist_recondon": ["cl_ad_found", "cl_ad_url", "cl_license_displayed"],
        "osint_social": ["osint_email_discovered", "osint_email_verified", "osint_cell_phone"],
        "court_records": ["court_case_count", "court_lien_count", "court_judgment_total"],
    }

    possible_results = 0
    batch = 1000
    cur.execute("SELECT * FROM contractors LIMIT 1")
    cols = [c[0] for c in cur.description]
    # Only estimate: scan in batches and count non-empty source columns
    cur.execute("SELECT * FROM contractors")
    rows = cur.fetchmany(batch)
    while rows:
        for r in rows:
            for src, cols_list in source_mappings.items():
                has = False
                for c in cols_list:
                    if c in r.keys():
                        v = r[c]
                        if v not in (None, "", 0, 0.0, False):
                            has = True
                            break
                if has:
                    possible_results += 1
        rows = cur.fetchmany(batch)
    conn.close()
    return {"contractors": contractors, "possible_results": possible_results}


def migrate_apply(target_db: Path, legacy_db: Path, repo_root: Path, batch_size: int = 500) -> Dict[str, Any]:
    # Initialize target DB
    from src.db_init import init_enrichment_db
    from src.enrichment_models import EnrichmentDB, SourceManifest, EnrichmentResult, Contractor, ProgressSnapshot

    engine, SessionLocal = init_enrichment_db(str(target_db))
    session = SessionLocal()

    summary = {"manifests": 0, "contractors": 0, "enrichment_results": 0, "snapshots": 0, "errors": []}

    # Step 1: load manifests
    manifest_files = find_manifest_files(repo_root)
    for mf in manifest_files:
        try:
            doc = parse_dirty_json(mf.read_text(encoding="utf-8"))
            # derive slug
            slug = doc.get("api_slug") or doc.get("slug") or mf.stem
            sm = session.query(SourceManifest).filter_by(slug=slug).one_or_none()
            cfg = json.dumps(doc)
            if sm is None:
                sm = SourceManifest(slug=slug, name=doc.get("name"), type=doc.get("type") or doc.get("source_type"), config_json=cfg)
                session.add(sm)
            else:
                sm.config_json = cfg
            session.commit()
            summary["manifests"] += 1
        except Exception as e:
            summary["errors"].append(f"manifest:{mf}:{e}")

    # Step 2: legacy DB -> contractors + enrichment_results
    if legacy_db.exists():
        src_conn = sqlite3.connect(str(legacy_db))
        src_conn.row_factory = sqlite3.Row
        src_cur = src_conn.cursor()
        src_cur.execute("SELECT * FROM contractors")
        cols = [c[0] for c in src_cur.description]

        # prepare source mappings as in preview
        source_mappings = {
            "google_places": ([
                "gp_place_id",
                "gp_website",
                "gp_rating",
                "gp_review_count",
                "gp_phone_verified",
                "gp_hours",
                "gp_lat",
                "gp_lng",
            ], "gp_enriched_at"),
            "osha_enforcement": ([
                "osha_inspection_count",
                "osha_violation_count",
                "osha_penalty_total",
                "osha_last_inspection_date",
            ], "osha_enriched_at"),
            "arcgis_permits": ((["permit_active_count", "permit_total_value", "permit_last_issued_date"], "permit_enriched_at"))[0],
        }

        # fallback: process rows in batches
        batch_rows = src_cur.fetchmany(batch_size)
        db = EnrichmentDB(str(target_db))
        processed_contractors = 0
        processed_results = 0
        while batch_rows:
            for r in batch_rows:
                license_number = r.get("license_number") or r.get("licenseno") or r.get("license_no")
                if not license_number:
                    continue
                # upsert contractor (pick a few fields)
                cid = db.upsert_contractor(
                    license_number,
                    business_name=r.get("business_name") or r.get("businessname"),
                    dba_name=r.get("dba_name") or r.get("dba"),
                    address_city=r.get("address_city") or r.get("city"),
                    address_state=r.get("address_state") or r.get("state"),
                    address_zip=r.get("address_zip") or r.get("zip"),
                    phone_business=r.get("phone_business") or r.get("phone"),
                )
                processed_contractors += 1

                # For each known source, extract columns if present
                # Google Places (explicit mapping)
                gp_keys = [
                    "gp_place_id",
                    "gp_website",
                    "gp_rating",
                    "gp_review_count",
                    "gp_phone_verified",
                    "gp_hours",
                    "gp_lat",
                    "gp_lng",
                ]
                gp_data = {k: r[k] for k in gp_keys if k in r.keys() and r[k] not in (None, "")}
                gp_done = (r.get("gp_enriched_at") not in (None, ""))
                if gp_data or gp_done:
                    payload = {"extracted": gp_data, "enriched_at": r.get("gp_enriched_at")}
                    db.upsert_enrichment_result(cid, "google_places", payload, success=True, latency_ms=None, phase=2)
                    processed_results += 1

                # OSHA
                osk_keys = [
                    "osha_inspection_count",
                    "osha_violation_count",
                    "osha_penalty_total",
                    "osha_last_inspection_date",
                ]
                osk_data = {k: r[k] for k in osk_keys if k in r.keys() and r[k] not in (None, "")}
                osk_done = (r.get("osha_enriched_at") not in (None, ""))
                if osk_data or osk_done:
                    payload = {"extracted": osk_data, "enriched_at": r.get("osha_enriched_at")}
                    db.upsert_enrichment_result(cid, "osha_enforcement", payload, success=True, latency_ms=None, phase=2)
                    processed_results += 1

                # ArcGIS
                arc_keys = ["permit_active_count", "permit_total_value", "permit_last_issued_date", "permit_types"]
                arc_data = {k: r[k] for k in arc_keys if k in r.keys() and r[k] not in (None, "")}
                arc_done = (r.get("permit_enriched_at") not in (None, ""))
                if arc_data or arc_done:
                    payload = {"extracted": arc_data, "enriched_at": r.get("permit_enriched_at")}
                    db.upsert_enrichment_result(cid, "arcgis_permits", payload, success=True, latency_ms=None, phase=2)
                    processed_results += 1

                # Craigslist (many cl_* columns) - coarse check
                cl_indicator = r.get("cl_ad_found") if "cl_ad_found" in r.keys() else None
                if cl_indicator not in (None, "", 0, False):
                    cl_data = {k: r[k] for k in r.keys() if k.startswith("cl_") and r[k] not in (None, "")}
                    payload = {"extracted": cl_data, "enriched_at": r.get("cl_enriched_at")}
                    db.upsert_enrichment_result(cid, "craigslist_recondon", payload, success=True, latency_ms=None, phase=3)
                    processed_results += 1

                # OSINT Social
                osint_keys = ["osint_email_discovered", "osint_email_verified", "osint_cell_phone", "osint_linkedin_url"]
                osint_data = {k: r[k] for k in osint_keys if k in r.keys() and r[k] not in (None, "")}
                osint_done = (r.get("osint_enriched_at") not in (None, ""))
                if osint_data or osint_done:
                    payload = {"extracted": osint_data, "enriched_at": r.get("osint_enriched_at")}
                    db.upsert_enrichment_result(cid, "osint_social", payload, success=True, latency_ms=None, phase=1)
                    processed_results += 1

                # Court records
                court_keys = ["court_case_count", "court_lien_count", "court_judgment_total", "court_bankruptcy"]
                court_data = {k: r[k] for k in court_keys if k in r.keys() and r[k] not in (None, "")}
                court_done = (r.get("court_enriched_at") not in (None, ""))
                if court_data or court_done:
                    payload = {"extracted": court_data, "enriched_at": r.get("court_enriched_at")}
                    db.upsert_enrichment_result(cid, "court_records", payload, success=True, latency_ms=None, phase=4)
                    processed_results += 1

            summary["contractors"] += processed_contractors
            summary["enrichment_results"] += processed_results
            # fetch next batch
            batch_rows = src_cur.fetchmany(batch_size)

        src_conn.close()

    else:
        # legacy DB missing; seed from CSV
        csv_path = repo_root / "sacramento_contractors_cslb_sac.csv"
        if csv_path.exists():
            import csv

            with open(csv_path, newline="", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                db = EnrichmentDB(str(target_db))
                cnt = 0
                for row in reader:
                    lic = row.get("license_number") or row.get("licensenumber") or row.get("license")
                    if not lic:
                        continue
                    db.upsert_contractor(lic, business_name=row.get("business_name"), address_city=row.get("city"))
                    cnt += 1
                summary["contractors"] = cnt

    # Step 3: progress snapshots
    snaps = list((repo_root / "outputs").glob("recursive_snapshot_*.json"))
    snaps += list((repo_root / "outputs").glob("ferengi_progress*.json"))
    snap_count = 0
    for s in snaps:
        try:
            doc = parse_dirty_json(s.read_text(encoding="utf-8"))
            iteration = doc.get("iteration") or doc.get("iter") or 0
            counts = doc.get("counts") or doc.get("stats") or {}
            total = counts.get("total") or doc.get("total_records") or 0
            completed = counts.get("completed") or doc.get("completed") or 0
            errors = counts.get("errors") or doc.get("errors") or 0
            completion_rate = (completed / total * 100.0) if total else 0.0
            ps = ProgressSnapshot(iteration=iteration, phase=doc.get("phase") or 0, total=total, completed=completed, errors=errors, completion_rate=completion_rate)
            session.add(ps)
            snap_count += 1
        except Exception as e:
            summary["errors"].append(f"snapshot:{s}:{e}")
    session.commit()
    summary["snapshots"] = snap_count

    session.close()
    return summary


def main():
    parser = argparse.ArgumentParser(description="Migrate legacy ferengi outputs to normalized enrichment DB")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="Preview counts only")
    group.add_argument("--apply", action="store_true", help="Perform migration")
    parser.add_argument("--target", default="./outputs/enrichment.db", help="Target DB path")
    parser.add_argument("--legacy-db", default="./outputs/ferengi_enrichment.db", help="Legacy flat DB path")
    parser.add_argument("--repo-root", default="..", help="Repository root relative to scripts/ (defaults to project root)")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1] if args.repo_root == ".." else Path(args.repo_root)
    target = Path(args.target)
    legacy = Path(args.legacy_db)

    manifest_files = find_manifest_files(repo_root)
    manifests = load_manifests_preview(manifest_files)

    if args.dry_run:
        print("🍄 MARIO MIGRATION PIPE — DRY RUN 🔍")
        print("  Target:", str(target))
        print("  🌍 WORLD 0: Loading source manifests...")
        for m in manifests:
            doc = m.get("doc")
            slug = doc.get("api_slug") or doc.get("slug") or Path(m.get("path")).stem
            print(f"    📋 {slug:30} ({doc.get('type') or 'unknown'})")
        print(f"    ✅ {len(manifests)} manifests loaded")

        print("  🌍 WORLD 1-4: Migrating legacy ferengi_enrichment.db...")
        counts = count_legacy_rows(legacy)
        print(f"    📊 Found {counts['contractors']} contractors in legacy DB")
        print(f"    📊 Estimated enrichment results: {counts['possible_results']}")

        # progress snapshots
        snaps = list((repo_root / "outputs").glob("recursive_snapshot_*.json"))
        snaps += list((repo_root / "outputs").glob("ferengi_progress*.json"))
        print(f"  🌍 BONUS: Loading progress snapshots...\n    📊 {len(snaps)} snapshots found")

        print("\n  ════════════════════════════════════")
        print("  🏰 MIGRATION SUMMARY — DRY RUN 🔍")
        print(f"  Contractors migrated:       {counts['contractors']}")
        print(f"  Enrichment results:       ~{counts['possible_results']}")
        print(f"  Source manifests:              {len(manifests)}")
        print(f"  Progress snapshots:             {len(snaps)}")
        print("  ════════════════════════════════════")
        # exit
        return

    # apply
    print("Starting migration (apply) -> writing to:", str(target))
    out = migrate_apply(target, legacy, repo_root)
    print("Migration complete. Summary:")
    print(json.dumps(out, indent=2))
    # write migration summary
    try:
        out_path = Path("outputs") / "migration_summary.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
        print("Wrote summary to", str(out_path))
    except Exception:
        pass


if __name__ == "__main__":
    main()
