#!/usr/bin/env python3
"""Sweep combined-score thresholds and produce counts + samples for manual calibration.

Reads the preview CSV produced by `osha_contractor_tfidf_enrich.py` and computes the
combined score using provided weights or a preset. Outputs a JSON summary and a
CSV of rows with combined scores for manual inspection.
"""
from pathlib import Path
import json
import argparse
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PREVIEW_CSV = ROOT / 'outputs' / 'sacramento_contractors_cslb_sac_enriched_preview_tfidf.csv'
OUT_JSON = ROOT / 'outputs' / 'oshadata' / 'tfidf_threshold_sweep.json'
OUT_CSV = ROOT / 'outputs' / 'oshadata' / 'tfidf_threshold_rows.csv'

PRESETS = {
    'balanced': {'tfidf_w': 0.7, 'rf_w': 0.3},
    'stricter': {'tfidf_w': 0.8, 'rf_w': 0.2},
    'safer': {'tfidf_w': 0.6, 'rf_w': 0.4},
}


def sweep(df, tfidf_w, rf_w, thresholds):
    df = df.copy()
    df['tfidf_score'] = pd.to_numeric(df.get('tfidf_score', 0.0), errors='coerce').fillna(0.0)
    df['rapidfuzz_score'] = pd.to_numeric(df.get('rapidfuzz_score', 0.0), errors='coerce').fillna(0.0)
    df['combined'] = df['tfidf_score'] * tfidf_w + (df['rapidfuzz_score'] / 100.0) * rf_w
    total = len(df)
    results = {}
    for th in thresholds:
        cnt = int((df['combined'] >= th).sum())
        results[f"{th:.2f}"] = {'count': cnt, 'pct': cnt / total if total else 0.0}
    # top sample across whole set
    top = df.sort_values('combined', ascending=False).head(50)
    return results, df, top


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--preset', choices=list(PRESETS.keys()), default='safer')
    parser.add_argument('--tfidf-w', type=float, default=None)
    parser.add_argument('--rf-w', type=float, default=None)
    parser.add_argument('--start', type=float, default=0.30)
    parser.add_argument('--end', type=float, default=0.70)
    parser.add_argument('--step', type=float, default=0.01)
    parser.add_argument('--preview-csv', type=str, default=str(PREVIEW_CSV))
    args = parser.parse_args()

    if args.tfidf_w is None and args.rf_w is None:
        w = PRESETS[args.preset]
        tfidf_w = w['tfidf_w']
        rf_w = w['rf_w']
    else:
        tfidf_w = args.tfidf_w if args.tfidf_w is not None else 0.7
        rf_w = args.rf_w if args.rf_w is not None else 0.3
    # normalize
    s = tfidf_w + rf_w
    tfidf_w, rf_w = tfidf_w / s, rf_w / s

    csvp = Path(args.preview_csv)
    if not csvp.exists():
        print('Preview CSV not found:', csvp)
        raise SystemExit(2)

    df = pd.read_csv(csvp, dtype=str, low_memory=False)

    thresholds = list(np.arange(args.start, args.end + 1e-9, args.step))
    results, scored_df, top = sweep(df, tfidf_w=tfidf_w, rf_w=rf_w, thresholds=thresholds)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    out = {
        'preset': args.preset,
        'tfidf_w': tfidf_w,
        'rf_w': rf_w,
        'thresholds': results,
        'total_rows': int(len(df)),
    }
    OUT_JSON.write_text(json.dumps(out, indent=2))
    # write rows with combined score for manual inspection
    scored_df.to_csv(OUT_CSV, index=False)
    print('Wrote sweep summary to', OUT_JSON)
    print('Wrote scored rows to', OUT_CSV)
