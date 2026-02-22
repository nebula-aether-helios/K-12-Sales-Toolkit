#!/usr/bin/env python3
"""Re-probe existing email candidates for DNS/MX and SMTP validation.

This script will load the first N prospects from the DB, for each candidate
resolve MX via `connectors.dns_helpers.get_dns_records`, run `enrichment.email_utils.smtp_probe`,
and update the candidate `source_signals` and `status` fields accordingly.

Usage:
  python tools/reprobe_candidates.py --db sqlite:///enrichment.db --limit 10
"""
import argparse
import json
import logging
import os
from db.models import get_session, EnrichedProspect, EmailCandidate
from connectors.dns_helpers import get_dns_records, parse_spf, is_valid_hostname, mx_provider_from_hostname
from enrichment.email_utils import smtp_probe
from db.models import acquire_lock, release_lock, ProbeLock

# Structured logger (JSON lines)
LOG_DIR = os.path.join(os.getcwd(), 'outputs', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
logger = logging.getLogger('reprobe')
if not logger.handlers:
    fh = logging.FileHandler(os.path.join(LOG_DIR, 'reprobe.log'))
    fh.setLevel(logging.INFO)
    logger.addHandler(fh)
    logger.setLevel(logging.INFO)


def reprobe(db_url: str, limit: int = 10, atomic_commit: bool = False, fixed_ids: list = None, fixed_file: str = None):
    sess = get_session(db_url)
    # If user requested a fixed sample, add a dedicated log file for reproducible runs
    if fixed_ids or fixed_file:
        try:
            fh_fixed = logging.FileHandler(os.path.join(LOG_DIR, 'reprobe_fixed.log'))
            fh_fixed.setLevel(logging.INFO)
            logger.addHandler(fh_fixed)
        except Exception:
            pass
    # Acquire a global named lock to prevent overlapping reprobes across processes
    global_lock_name = 'reprobe_global'
    got_global = acquire_lock(sess, name=global_lock_name, owner='reprobe_script')
    if not got_global:
        logger.info(json.dumps({"event": "abort", "reason": "another_reprobe_in_progress"}))
        print('Another reprobe appears to be in progress; aborting.')
        return
    logger.info(json.dumps({"event": "acquired_global_lock", "lock": global_lock_name}))
    provider_metrics = {}
    # Determine prospects to process. If fixed ids/file provided, use those deterministically.
    prospects = []
    if fixed_ids:
        # ensure integers
        ids = [int(x) for x in fixed_ids]
        prospects = sess.query(EnrichedProspect).filter(EnrichedProspect.id.in_(ids)).order_by(EnrichedProspect.id).limit(limit).all()
    elif fixed_file:
        try:
            with open(fixed_file, 'r') as fh:
                ids = [int(l.strip()) for l in fh if l.strip()]
            prospects = sess.query(EnrichedProspect).filter(EnrichedProspect.id.in_(ids)).order_by(EnrichedProspect.id).limit(limit).all()
        except Exception:
            prospects = sess.query(EnrichedProspect).order_by(EnrichedProspect.id).limit(limit).all()
    else:
        prospects = sess.query(EnrichedProspect).order_by(EnrichedProspect.id).limit(limit).all()
    print(f"Found {len(prospects)} prospects to reprobe (atomic_commit={atomic_commit})")
    for p in prospects:
        # Acquire a prospect-specific lock; skip if locked
        locked = acquire_lock(sess, prospect_id=p.id, owner='reprobe_script')
        if not locked:
            logger.info(json.dumps({"event": "skip_prospect", "prospect_id": p.id, "reason": "lock_held"}))
            print(f"Skipping prospect id={p.id} because lock is held")
            continue
        logger.info(json.dumps({"event": "start_prospect", "prospect_id": p.id, "source_row": p.source_row_id}))
        print(f"Prospect id={p.id} source_row={p.source_row_id} (emails={len(p.emails)})")
        try:
            for c in p.emails:
                email = c.email
                try:
                    domain = email.split('@', 1)[1].lower()
                except Exception:
                    domain = None
                dns = get_dns_records(domain) if domain else {"a": [], "aaaa": [], "mx": [], "txt": [], "ns": []}
                spf = parse_spf(dns.get('txt', []))
                mx = dns.get('mx', []) or []
                # normalize mx entries to list of (pref, host) tuples
                mx_tuples = []
                for m in mx:
                    if isinstance(m, tuple) and len(m) >= 2:
                        pref, host = m[0], m[1]
                    elif isinstance(m, str):
                        pref, host = 0, m
                    else:
                        continue
                    host = (host or '').strip().rstrip('.')
                    if is_valid_hostname(host):
                        mx_tuples.append((pref, host))
                print(f"  Candidate {c.email} -> mx hosts: {mx_tuples}")
                # Prepare mx_hosts as list of (pref, host) if available
                mx_hosts = mx_tuples
                probe = smtp_probe(email, mx_hosts)
                # infer providers for mx hosts
                providers = []
                for _pref, h in mx_hosts:
                    providers.append(mx_provider_from_hostname(h))
                probe_event = {"event": "candidate_probe", "prospect_id": p.id, "candidate": c.email, "mx_hosts": mx_hosts, "providers": providers, "probe": probe}
                logger.info(json.dumps(probe_event))
                # update provider_metrics
                if not providers:
                    prov_key = 'no_mx'
                    provider_metrics.setdefault(prov_key, {"probes": 0, "valid": 0, "invalid": 0, "codes": {}})
                    provider_metrics[prov_key]["probes"] += 1
                    status = probe.get('status')
                    if status == 'valid':
                        provider_metrics[prov_key]["valid"] += 1
                    elif status == 'invalid':
                        provider_metrics[prov_key]["invalid"] += 1
                    code = probe.get('code') or probe.get('smtp_code') or 'none'
                    provider_metrics[prov_key]["codes"][code] = provider_metrics[prov_key]["codes"].get(code, 0) + 1
                else:
                    for prov in providers:
                        prov_key = prov or 'unknown'
                        provider_metrics.setdefault(prov_key, {"probes": 0, "valid": 0, "invalid": 0, "codes": {}})
                        provider_metrics[prov_key]["probes"] += 1
                        status = probe.get('status')
                        if status == 'valid':
                            provider_metrics[prov_key]["valid"] += 1
                        elif status == 'invalid':
                            provider_metrics[prov_key]["invalid"] += 1
                        code = probe.get('code') or probe.get('smtp_code') or 'none'
                        provider_metrics[prov_key]["codes"][code] = provider_metrics[prov_key]["codes"].get(code, 0) + 1
                print(f"    smtp_probe -> {probe}")
                # Update candidate source_signals
                signals = c.source_signals or {}
                signals.update({
                    'dns_mx': mx_hosts,
                    'spf': spf,
                    'smtp_details': probe,
                })
                c.source_signals = signals
                # Update status on successful validation
                if probe.get('status') == 'valid':
                    c.status = 'validated_smtp'
                sess.add(c)
                # update prospect-level dns_mx for visibility
                p.dns_mx = mx_hosts if mx_hosts else (dns.get('mx') if 'dns' in locals() else p.dns_mx)
                sess.add(p)
                if atomic_commit:
                    try:
                        sess.commit()
                        logger.info(json.dumps({"event": "commit_candidate", "prospect_id": p.id, "candidate": c.email}))
                        print('    committed candidate to DB (atomic)')
                    except Exception as e:
                        logger.error(json.dumps({"event": "commit_failed", "prospect_id": p.id, "candidate": c.email, "error": str(e)}))
                        print('    atomic commit failed:', e)
        finally:
            # release prospect-specific lock
            try:
                release_lock(sess, prospect_id=p.id)
                logger.info(json.dumps({"event": "finish_prospect", "prospect_id": p.id}))
            except Exception as e:
                logger.error(json.dumps({"event": "finish_commit_failed", "prospect_id": p.id, "error": str(e)}))
    if not atomic_commit:
        sess.commit()
        print('Reprobe complete and committed (single commit)')
    else:
        print('Reprobe complete (atomic commits used)')
    # emit aggregated provider metrics
    try:
        logger.info(json.dumps({"event": "provider_metrics", "metrics": provider_metrics}))
    except Exception:
        pass
    # release global lock
    try:
        # persist provider metrics to DB
        try:
            from db.models import upsert_provider_metrics
            upsert_provider_metrics(sess, provider_metrics)
            logger.info(json.dumps({"event": "provider_metrics_persisted"}))
        except Exception as e:
            logger.error(json.dumps({"event": "provider_metrics_persist_failed", "error": str(e)}))
        release_lock(sess, name=global_lock_name)
        logger.info(json.dumps({"event": "released_global_lock", "lock": global_lock_name}))
    except Exception:
        pass


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--db', required=True)
    p.add_argument('--limit', type=int, default=10)
    p.add_argument('--atomic-commit', action='store_true', help='Commit each candidate update immediately')
    p.add_argument('--fixed-ids', help='Comma-separated prospect IDs to target (deterministic sample)')
    p.add_argument('--fixed-sample-file', help='File path containing prospect IDs (one per line)')
    args = p.parse_args()
    fixed_ids = None
    if args.fixed_ids:
        fixed_ids = [x.strip() for x in args.fixed_ids.split(',') if x.strip()]
    reprobe(args.db, args.limit, atomic_commit=args.atomic_commit, fixed_ids=fixed_ids, fixed_file=args.fixed_sample_file)


if __name__ == '__main__':
    main()
