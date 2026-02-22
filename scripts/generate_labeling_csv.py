#!/usr/bin/env python3
"""Generate a CSV of candidate matches for manual labeling.

For each contractor in the preview (or top N contractors), produce the top-K
candidate accident records (by TF-IDF similarity) along with rapidfuzz scores
and the combined score using the given weights. Outputs a CSV suitable for
manual labeling.
"""
from pathlib import Path
import argparse
import pandas as pd
import numpy as np
import sys

ROOT = Path(__file__).resolve().parents[1]
PREVIEW_CSV = ROOT / 'outputs' / 'sacramento_contractors_cslb_sac_enriched_preview_tfidf.csv'
ACCIDENTS_CSV = ROOT / 'outputs' / 'oshadata' / 'OSHADataDoor_OshaScrapy' / 'accidents_asof_022315_enriched.csv'
OUT_CSV = ROOT / 'outputs' / 'oshadata' / 'labeling_candidates_200_5.csv'

def normalize_text(s: str) -> str:
    if pd.isna(s):
        return ""
    return " ".join(str(s).split()).lower()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--preview-csv', type=str, default=str(PREVIEW_CSV))
    parser.add_argument('--top-n', type=int, default=200)
    parser.add_argument('--candidates', type=int, default=5)
    parser.add_argument('--tfidf-w', type=float, default=0.6)
    parser.add_argument('--rf-w', type=float, default=0.4)
    parser.add_argument('--candidate-limit', type=int, default=5000)
    parser.add_argument('--prefilter-top', type=int, default=500)
    args = parser.parse_args()

    preview_path = Path(args.preview_csv)
    if not preview_path.exists():
        print('Preview CSV not found:', preview_path)
        sys.exit(2)

    preview = pd.read_csv(preview_path, dtype=str, low_memory=False)
    accidents = pd.read_csv(ACCIDENTS_CSV, dtype=str, low_memory=False)

    # prepare texts
    preview['match_text'] = preview.get('match_text', preview.get('business_name','').fillna('') + ' ' + preview.get('address_street','').fillna('')).apply(normalize_text)
    accidents['match_text'] = (accidents.get('event_desc','').fillna('') + ' ' + accidents.get('event_keyword','').fillna('') + ' ' + accidents.get('abstract_text','').fillna('')).apply(normalize_text)
    accidents['state_enriched'] = accidents.get('state_enriched', accidents.get('state_flag','')).fillna('').astype(str).str.upper()
    preview['address_state_norm'] = preview.get('address_state','').fillna('').astype(str).str.upper()

    # choose contractors to label: first top-n rows in preview by combined if present, else head
    if 'combined' in preview.columns:
        preview['combined'] = pd.to_numeric(preview['combined'], errors='coerce').fillna(0.0)
        sel = preview.sort_values('combined', ascending=False).head(args.top_n).copy()
    else:
        sel = preview.head(args.top_n).copy()

    # fit vectorizer
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import linear_kernel
    vectorizer = TfidfVectorizer(ngram_range=(1,2), stop_words='english', max_features=20000)
    corpus = pd.concat([sel['match_text'], accidents['match_text']])
    vectorizer.fit(corpus)
    acc_tfidf = vectorizer.transform(accidents['match_text'])
    contractor_tfidf = vectorizer.transform(sel['match_text'])

    # attempt to import rapidfuzz process/scoring
    try:
        from rapidfuzz import process as _rf_process, fuzz as _rf_fuzz
    except Exception:
        _rf_process = None
        from rapidfuzz import fuzz as _rf_fuzz

    rows = []
    for idx in range(len(sel)):
        row = sel.iloc[idx]
        c_vec = contractor_tfidf[idx]
        state = row.get('address_state_norm','')
        if state:
            mask = (accidents['state_enriched'] == state).values
            candidate_idxs = np.where(mask)[0] if mask.sum() else np.arange(acc_tfidf.shape[0])
        else:
            candidate_idxs = np.arange(acc_tfidf.shape[0])

        # reduce search space for scoring
        search_idxs = candidate_idxs
        if len(search_idxs) > args.candidate_limit:
            step = max(1, len(search_idxs) // args.candidate_limit)
            search_idxs = search_idxs[::step][:args.candidate_limit]

        cand_texts = accidents['match_text'].iloc[search_idxs].fillna('').tolist()
        # use rapidfuzz.process.extract to get prefilter_top best
        top_k = min(args.prefilter_top, len(cand_texts))
        if _rf_process is not None:
            results = _rf_process.extract(row['match_text'], cand_texts, scorer=_rf_fuzz.token_set_ratio, limit=top_k)
            top_pos = [r[2] for r in results]
            candidate_idxs = np.array(search_idxs)[top_pos]
        else:
            scores = [_rf_fuzz.token_set_ratio(row['match_text'], t) for t in cand_texts]
            top_k2 = min(top_k, len(scores))
            top_pos = np.argpartition(np.array(scores)*-1, top_k2-1)[:top_k2]
            top_pos = top_pos[np.argsort(np.array(scores)[top_pos])[::-1]]
            candidate_idxs = np.array(search_idxs)[top_pos]

        # compute TF-IDF sims on the reduced candidates
        sims = linear_kernel(c_vec, acc_tfidf[candidate_idxs]).flatten()
        order = np.argsort(sims)[::-1][:args.candidates]
        for rank, pos in enumerate(order, start=1):
            acc_idx = int(candidate_idxs[pos])
            tfidf_score = float(sims[pos])
            rf_score = _rf_fuzz.token_set_ratio(row['match_text'], accidents.iloc[acc_idx]['match_text'])
            combined = args.tfidf_w * tfidf_score + args.rf_w * (rf_score / 100.0)
            rows.append({
                'contractor_index': int(row.name),
                'business_name': row.get('business_name',''),
                'address_street': row.get('address_street',''),
                'address_city': row.get('address_city',''),
                'address_state': row.get('address_state',''),
                'contractor_match_text': row.get('match_text',''),
                'candidate_rank': rank,
                'candidate_report_id': accidents.iloc[acc_idx].get('report_id',''),
                'candidate_event_desc': accidents.iloc[acc_idx].get('event_desc',''),
                'tfidf_score': tfidf_score,
                'rapidfuzz_score': rf_score,
                'combined': combined,
            })

    out_df = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUT_CSV, index=False)
    print('Wrote labeling candidates to', OUT_CSV)
