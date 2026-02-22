#!/usr/bin/env python3
import pandas as pd
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / 'outputs' / 'sacramento_contractors_cslb_sac_enriched_preview_tfidf.csv'
OUT = ROOT / 'outputs' / 'oshadata' / 'tfidf_perf_summary_safer.json'

df = pd.read_csv(CSV, dtype=str, low_memory=False)
df['tfidf_score'] = pd.to_numeric(df.get('tfidf_score',0.0), errors='coerce').fillna(0.0)
df['rapidfuzz_score'] = pd.to_numeric(df.get('rapidfuzz_score',0.0), errors='coerce').fillna(0.0)

tfidf_w = 0.6
rf_w = 0.4

df['combined'] = df['tfidf_score'] * tfidf_w + (df['rapidfuzz_score']/100.0) * rf_w

total = len(df)
matched = df['matched_report_id'].fillna('').astype(bool).sum()

summary = {
    'total_rows': int(total),
    'matched_rows': int(matched),
    'pct_matched': float(matched/total) if total else 0.0,
    'tfidf_score_mean': float(df['tfidf_score'].mean()),
    'tfidf_score_median': float(df['tfidf_score'].median()),
    'rf_score_mean': float(df['rapidfuzz_score'].mean()),
    'rf_score_median': float(df['rapidfuzz_score'].median()),
    'combined_mean': float(df['combined'].mean()),
    'combined_median': float(df['combined'].median()),
    'thresholds': {}
}
for th in [0.4,0.45,0.5]:
    cnt = int((df['combined'] >= th).sum())
    summary['thresholds'][str(th)] = {'count': cnt, 'pct': cnt/total if total else 0.0}

summary['top_matches_sample'] = df.sort_values('combined', ascending=False).head(10)[['business_name','address_street','address_city','address_state','matched_report_id','tfidf_score','rapidfuzz_score','combined']].to_dict(orient='records')
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(summary, indent=2))
print('Wrote', OUT)
print(json.dumps(summary, indent=2))
