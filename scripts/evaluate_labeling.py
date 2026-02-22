#!/usr/bin/env python3
"""Evaluate labeled candidate CSV to compute precision@1, precision@5, and sample recall.

Expects a CSV with columns produced by `generate_labeling_csv.py` plus a column
`is_match` (1 if that candidate is the true match for the contractor, else 0).

Outputs a small JSON summary to outputs/oshadata/labeling_eval_summary.json
"""
from pathlib import Path
import pandas as pd
import json
import argparse

ROOT = Path(__file__).resolve().parents[1]
LAB_CSV = ROOT / 'outputs' / 'oshadata' / 'labeling_candidates_200_5.csv'
OUT_SUM = ROOT / 'outputs' / 'oshadata' / 'labeling_eval_summary.json'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--labeled-csv', type=str, default=str(LAB_CSV))
    args = parser.parse_args()

    df = pd.read_csv(args.labeled_csv, low_memory=False)
    if 'is_match' not in df.columns:
        print('Please add an `is_match` column (1 for correct candidate, 0 otherwise) to the CSV and re-run')
        raise SystemExit(2)

    df['is_match'] = pd.to_numeric(df['is_match'], errors='coerce').fillna(0).astype(int)

    # compute precision@1 and precision@5
    precision_at_1 = df[df['candidate_rank'] == 1]['is_match'].mean()
    precision_at_5 = df[df['candidate_rank'] <= 5]['is_match'].mean()

    # sample-level recall: number of contractors in sample with at least one positive / number of contractors sampled
    contractors = df.groupby('contractor_index')
    contractors_with_positive = contractors['is_match'].max()
    sample_recall = (contractors_with_positive > 0).sum() / contractors_with_positive.size

    out = {
        'rows': int(len(df)),
        'contractor_samples': int(contractors_with_positive.size),
        'precision_at_1': float(precision_at_1),
        'precision_at_5': float(precision_at_5),
        'sample_recall': float(sample_recall),
        'notes': 'Precision@K computed across labeled candidate rows; sample_recall = fraction of sampled contractors for which at least one candidate was labeled as the true match.'
    }

    OUT_SUM.parent.mkdir(parents=True, exist_ok=True)
    OUT_SUM.write_text(json.dumps(out, indent=2))
    print('Wrote evaluation summary to', OUT_SUM)
    print(json.dumps(out, indent=2))
