#!/usr/bin/env python3
"""Compare ANN preview vs TF-IDF+prefilter preview on the same contractor preview rows.

Produces overlap statistics for top-1 and top-5 candidates and writes a JSON report.
"""
from pathlib import Path
import json
import argparse
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ANN_CSV = ROOT / 'outputs' / 'oshadata' / 'ann_preview_tfidf.csv'
TFIDF_CSV = ROOT / 'outputs' / 'sacramento_contractors_cslb_sac_enriched_preview_tfidf.csv'
OUT_JSON = ROOT / 'outputs' / 'oshadata' / 'ann_tfidf_comparison.json'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--ann-csv', type=str, default=str(ANN_CSV))
    parser.add_argument('--tfidf-csv', type=str, default=str(TFIDF_CSV))
    parser.add_argument('--top-k', type=int, default=5)
    args = parser.parse_args()

    ann_path = Path(args.ann_csv)
    tfidf_path = Path(args.tfidf_csv)
    if not ann_path.exists() or not tfidf_path.exists():
        print('Missing preview files. ANN:', ann_path.exists(), 'TFIDF:', tfidf_path.exists())
        raise SystemExit(2)

    ann = pd.read_csv(ann_path, dtype=str, low_memory=False)
    tfidf = pd.read_csv(tfidf_path, dtype=str, low_memory=False)

    # ensure candidate_rank numeric
    if 'candidate_rank' in ann.columns:
        ann['candidate_rank'] = pd.to_numeric(ann['candidate_rank'], errors='coerce').fillna(1).astype(int)
    else:
        ann['candidate_rank'] = 1
    if 'candidate_rank' in tfidf.columns:
        tfidf['candidate_rank'] = pd.to_numeric(tfidf['candidate_rank'], errors='coerce').fillna(1).astype(int)
    else:
        tfidf['candidate_rank'] = 1

    # use a key derived from business_name + address_street to align rows across previews
    def make_key(row):
        name = str(row.get('business_name','')).strip().lower()
        street = str(row.get('address_street','')).strip().lower()
        return f"{name}||{street}"

    def topk_map_by_key(df, k):
        out = {}
        for _, r in df.iterrows():
            key = make_key(r)
            rank = int(r.get('candidate_rank', 1) or 1)
            rid = str(r.get('candidate_report_id','') or '')
            if key not in out:
                out[key] = []
            out[key].append((rank, rid))
        # sort and take top k
        for key, lst in list(out.items()):
            lst_sorted = [x[1] for x in sorted(lst, key=lambda x: x[0])]
            lst_sorted = [i for i in lst_sorted if i!=''][:k]
            out[key] = lst_sorted
        return out

    ann_map = topk_map_by_key(ann, args.top_k)
    tfidf_map = topk_map_by_key(tfidf, args.top_k)

    common_keys = sorted(set(ann_map.keys()).intersection(tfidf_map.keys()))
    total = len(common_keys)
    total = len(common_keys)

    top1_matches = 0
    topk_jaccard = []
    topk_intersection_counts = []
    any_overlap_count = 0

    for key in common_keys:
        a = ann_map.get(key, [])
        t = tfidf_map.get(key, [])
        if len(a)>0 and len(t)>0 and a[0]==t[0]:
            top1_matches += 1
        set_a = set(a)
        set_t = set(t)
        inter = set_a.intersection(set_t)
        union = set_a.union(set_t)
        j = len(inter)/len(union) if len(union)>0 else 0.0
        topk_jaccard.append(j)
        topk_intersection_counts.append(len(inter))
        if len(inter)>0:
            any_overlap_count += 1

    report = {
        'total_compared': total,
        'top1_match_count': top1_matches,
        'top1_match_pct': (top1_matches/total if total else 0.0),
        'topk_mean_jaccard': float(np.mean(topk_jaccard)) if topk_jaccard else 0.0,
        'topk_median_jaccard': float(np.median(topk_jaccard)) if topk_jaccard else 0.0,
        'topk_mean_intersection': float(np.mean(topk_intersection_counts)) if topk_intersection_counts else 0.0,
        'any_overlap_count': any_overlap_count,
        'any_overlap_pct': (any_overlap_count/total if total else 0.0)
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2))
    print('Wrote comparison summary to', OUT_JSON)
    print(json.dumps(report, indent=2))
