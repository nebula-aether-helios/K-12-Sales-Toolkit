#!/usr/bin/env python3
"""Measure runtime and compute simple stats for TF-IDF preview runs.

Runs scripts/osha_contractor_tfidf_enrich.py with provided args, times it,
then reads the produced preview CSV and computes match counts and score
statistics. Writes a small summary to outputs/oshadata/tfidf_perf_summary.txt
and prints to stdout.
"""
import time
import subprocess
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'osha_contractor_tfidf_enrich.py'
OUT_CSV = ROOT / 'outputs' / 'sacramento_contractors_cslb_sac_enriched_preview_tfidf.csv'
OUT_SUM = ROOT / 'outputs' / 'oshadata' / 'tfidf_perf_summary.json'

def run_and_time(args):
    cmd = [sys.executable, str(SCRIPT)] + args
    t0 = time.time()
    subprocess.check_call(cmd)
    t1 = time.time()
    return t1 - t0

def analyze(csv_path, tfidf_w=0.7, rf_w=0.3, thresholds=[0.45,0.50,0.55]):
    import pandas as pd
    df = pd.read_csv(csv_path, dtype=str, low_memory=False)
    # ensure numeric
    df['tfidf_score'] = pd.to_numeric(df.get('tfidf_score', 0.0), errors='coerce').fillna(0.0)
    df['rapidfuzz_score'] = pd.to_numeric(df.get('rapidfuzz_score', 0.0), errors='coerce').fillna(0.0)
    # recompute combined
    df['combined'] = df['tfidf_score'] * tfidf_w + (df['rapidfuzz_score']/100.0) * rf_w
    total = len(df)
    matched = df['matched_report_id'].fillna('').astype(bool).sum()
    pct_matched = matched / total if total else 0.0
    stats = {
        'total_rows': int(total),
        'matched_rows': int(matched),
        'pct_matched': float(pct_matched),
        'tfidf_score_mean': float(df['tfidf_score'].mean()),
        'tfidf_score_median': float(df['tfidf_score'].median()),
        'rf_score_mean': float(df['rapidfuzz_score'].mean()),
        'rf_score_median': float(df['rapidfuzz_score'].median()),
        'combined_mean': float(df['combined'].mean()),
        'combined_median': float(df['combined'].median()),
        'thresholds': {}
    }
    for th in thresholds:
        cnt = int((df['combined'] >= th).sum())
        stats['thresholds'][str(th)] = {'count': cnt, 'pct': cnt/total if total else 0.0}
    # top matches
    top = df.sort_values('combined', ascending=False).head(10)[['business_name','address_street','address_city','address_state','matched_report_id','tfidf_score','rapidfuzz_score','combined']]
    stats['top_matches_sample'] = top.to_dict(orient='records')
    return stats

if __name__ == '__main__':
    # run a timed preview using the user-selected 'safer' preset (prefilter guard enabled)
    # reduce candidate_limit and prefilter_top to keep the timed run responsive
    args = ['--preview','500','--mode','safer','--candidate-limit','1000','--prefilter-top','200']
    print('Running (or using existing CSV if present):', SCRIPT, ' '.join(args))
    runtime = None
    try:
        runtime = run_and_time(args)
        print(f'Run time: {runtime:.2f}s')
    except KeyboardInterrupt:
        print('Run interrupted by user')
    except Exception as e:
        print('Run failed:', e)
        print('Proceeding to analyze existing CSV if present...')

    if not OUT_CSV.exists():
        print('Error: expected output CSV not found:', OUT_CSV)
        sys.exit(1)
    # analyze using the 'safer' preset weights and thresholds
    summary = analyze(OUT_CSV, tfidf_w=0.6, rf_w=0.4, thresholds=[0.40,0.45,0.50])
    # runtime may be None if we couldn't re-run; store as null in that case
    summary['runtime_seconds'] = float(runtime) if runtime is not None else None
    OUT_SUM.parent.mkdir(parents=True, exist_ok=True)
    OUT_SUM.write_text(json.dumps(summary, indent=2))
    print('Wrote summary to', OUT_SUM)
    print(json.dumps(summary, indent=2))
