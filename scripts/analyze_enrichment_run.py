#!/usr/bin/env python3
"""Analyze Ferengi enrichment run and produce reports.

Produces:
- outputs/full_database_enrichment_report.json
- outputs/full_database_enrichment_report.md
- outputs/full_database_sample_50.csv
- outputs/full_database_sample_50.json

Read-only analysis; does not modify .env or other source files.
"""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


OUT = Path('outputs')
OUT.mkdir(exist_ok=True)


def read_db(db_path: str) -> Dict[str, Any]:
    info: Dict[str, Any] = {}
    if not Path(db_path).exists():
        info['error'] = f'DB not found: {db_path}'
        return info

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # schema
    cur.execute("PRAGMA table_info(contractors)")
    cols = cur.fetchall()
    info['schema'] = [{'cid': c[0], 'name': c[1], 'type': c[2], 'notnull': c[3], 'dflt_value': c[4], 'pk': c[5]} for c in cols]

    # counts
    def one(q):
        try:
            cur.execute(q)
            return cur.fetchone()[0]
        except Exception:
            return None

    info['counts'] = {
        'total': one("SELECT COUNT(*) FROM contractors"),
        'completed': one("SELECT COUNT(*) FROM contractors WHERE enrich_status='completed'"),
        'errors': one("SELECT COUNT(*) FROM contractors WHERE error_message IS NOT NULL AND TRIM(error_message)<>''")
    }

    # top error messages (first 200 chars)
    try:
        cur.execute("SELECT error_message FROM contractors WHERE error_message IS NOT NULL AND TRIM(error_message)<>''")
        rows = [r[0] for r in cur.fetchall()]
        freq: Dict[str, int] = {}
        for t in rows:
            k = (t or '')[:200]
            freq[k] = freq.get(k, 0) + 1
        info['error_summary'] = sorted([{'message': k, 'count': v} for k, v in freq.items()], key=lambda x: x['count'], reverse=True)[:20]
    except Exception:
        info['error_summary'] = []

    # sample 50
    try:
        cur.execute('SELECT * FROM contractors ORDER BY RANDOM() LIMIT 50')
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        sample = [dict(zip(cols, r)) for r in rows]
        info['sample_count'] = len(sample)
        # write sample files
        import csv
        csv_path = OUT / 'full_database_sample_50.csv'
        with open(csv_path, 'w', encoding='utf-8', newline='') as fh:
            writer = csv.DictWriter(fh, fieldnames=cols)
            writer.writeheader()
            for r in sample:
                writer.writerow({k: (v if v is not None else '') for k, v in r.items()})
        json_path = OUT / 'full_database_sample_50.json'
        with open(json_path, 'w', encoding='utf-8') as fh:
            json.dump(sample, fh, indent=2, ensure_ascii=False)
        info['sample_csv'] = str(csv_path)
        info['sample_json'] = str(json_path)
    except Exception as e:
        info['sample_count'] = 0
        info['sample_error'] = str(e)

    conn.close()
    return info


def parse_snapshots() -> List[Dict[str, Any]]:
    out = []
    for p in sorted(Path('outputs').glob('recursive_snapshot_*.json')):
        try:
            j = json.loads(p.read_text(encoding='utf-8'))
            j['_path'] = str(p)
            out.append(j)
        except Exception:
            continue
    return out


def parse_progress() -> Dict[str, Any]:
    p = Path('outputs') / 'ferengi_progress.json'
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        return {}


def parse_http_calls() -> Dict[str, Any]:
    calls = []
    logp = Path('outputs') / 'http_calls.log'
    if logp.exists():
        for line in logp.read_text(encoding='utf-8', errors='ignore').splitlines():
            try:
                calls.append(json.loads(line))
            except Exception:
                # best-effort parse: store raw
                calls.append({'raw': line})

    # responses directory listing (do not load huge bodies)
    resp_dir = Path('outputs') / 'responses'
    responses = []
    if resp_dir.exists():
        for p in sorted(resp_dir.glob('*.json'))[:200]:
            try:
                txt = p.read_text(encoding='utf-8', errors='ignore')
                # try to load small JSON preview
                try:
                    obj = json.loads(txt)
                except Exception:
                    obj = {'_raw_preview': txt[:200]}
                responses.append({'path': str(p), 'preview': obj})
            except Exception:
                continue

    # aggregate endpoints
    endpoints: Dict[str, int] = {}
    for c in calls:
        url = c.get('url') if isinstance(c, dict) else None
        if url:
            endpoints[url] = endpoints.get(url, 0) + 1

    return {'calls': calls, 'responses': responses, 'endpoint_counts': sorted([{'url': u, 'count': v} for u, v in endpoints.items()], key=lambda x: x['count'], reverse=True)}


def gather_env_keys() -> Dict[str, Any]:
    keys = ['RECORD_HTTP', 'FERENGI_DB', 'GOOGLE_PLACES_API_KEY', 'DCA_API', 'US_DEPT_OF_LABOR_API']
    out = {}
    for k in keys:
        out[k] = os.environ.get(k)
    return out


def main():
    db_path = os.environ.get('FERENGI_DB', 'outputs/ferengi_enrichment.db')
    start = datetime.utcnow().isoformat()
    report: Dict[str, Any] = {'generated_at': start, 'db_path': db_path}

    report['env'] = gather_env_keys()

    report['db'] = read_db(db_path)
    report['snapshots'] = parse_snapshots()
    report['progress'] = parse_progress()
    report['http'] = parse_http_calls()

    # high level reconciliation
    try:
        report['reconciliation'] = {
            'db_total': report['db']['counts'].get('total') if report.get('db') else None,
            'progress_total': report['progress'].get('total_prospects') if report.get('progress') else None,
            'snapshots_latest': report['snapshots'][-1] if report['snapshots'] else None
        }
    except Exception:
        report['reconciliation'] = {}

    # write JSON and markdown summary
    out_json = OUT / 'full_database_enrichment_report.json'
    out_md = OUT / 'full_database_enrichment_report.md'
    with open(out_json, 'w', encoding='utf-8') as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)

    with open(out_md, 'w', encoding='utf-8') as fh:
        fh.write(f"# Ferengi Enrichment Run Analysis\nGenerated: {start}\n\n")
        fh.write("## Summary\n\n")
        fh.write(f"DB path: {db_path}\n\n")
        cnts = report.get('db', {}).get('counts', {})
        fh.write(f"- total rows: {cnts.get('total')}\n")
        fh.write(f"- completed: {cnts.get('completed')}\n")
        fh.write(f"- errors: {cnts.get('errors')}\n\n")
        fh.write("## Top error messages (sample)\n\n")
        for e in report.get('db', {}).get('error_summary', [])[:10]:
            fh.write(f"- ({e['count']}) {e['message'][:200].replace('\n',' ')}\n")
        fh.write('\n')
        fh.write('## Top HTTP endpoints called\n\n')
        for e in report.get('http', {}).get('endpoint_counts', [])[:20]:
            fh.write(f"- {e['count']:>6}  {e['url']}\n")

    print('Analysis complete — reports written:')
    print(' -', out_json)
    print(' -', out_md)


if __name__ == '__main__':
    main()
