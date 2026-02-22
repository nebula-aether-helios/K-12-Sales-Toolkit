#!/usr/bin/env python3
"""Prototype ANN retrieval using TF-IDF + TruncatedSVD + hnswlib.

Builds dense embeddings for the accidents corpus via TF-IDF -> SVD, indexes
with hnswlib, and retrieves nearest neighbors per contractor preview row.
Writes a preview CSV with TF-IDF-approx scores (from embeddings), rapidfuzz,
and combined score using the chosen preset.
"""
from pathlib import Path
import argparse
import sys

ROOT = Path(__file__).resolve().parents[1]
CONTRACTOR_CSV = ROOT / "outputs" / "sacramento_contractors_cslb_sac.csv"
ACCIDENTS_ENRICHED_CSV = ROOT / "outputs" / "oshadata" / "OSHADataDoor_OshaScrapy" / "accidents_asof_022315_enriched.csv"
OUT_PREVIEW = ROOT / "outputs" / "oshadata" / "ann_preview_tfidf.csv"


def normalize_text(s):
    if s is None:
        return ""
    return " ".join(str(s).split()).lower()


def ensure_deps():
    try:
        import hnswlib
        from sklearn.decomposition import TruncatedSVD
    except Exception:
        print('Installing hnswlib and scikit-learn...')
        import subprocess
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'hnswlib', 'scikit-learn'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--preview', type=int, default=100)
    parser.add_argument('--preset', choices=['balanced','stricter','safer'], default='safer')
    parser.add_argument('--svd-dim', type=int, default=128)
    parser.add_argument('--retrieval-k', type=int, default=50)
    parser.add_argument('--return-top', type=int, default=5)
    args = parser.parse_args()

    presets = {
        'balanced': {'tfidf_w': 0.7, 'rf_w': 0.3, 'threshold': 0.50},
        'stricter': {'tfidf_w': 0.8, 'rf_w': 0.2, 'threshold': 0.55},
        'safer': {'tfidf_w': 0.6, 'rf_w': 0.4, 'threshold': 0.45},
    }
    p = presets[args.preset]
    tfidf_w = p['tfidf_w']
    rf_w = p['rf_w']
    threshold = p['threshold']

    ensure_deps()
    import pandas as pd
    import numpy as np
    import hnswlib
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.decomposition import TruncatedSVD
    from sklearn.metrics.pairwise import linear_kernel
    from rapidfuzz import fuzz

    contractors = pd.read_csv(CONTRACTOR_CSV, dtype=str, low_memory=False)
    accidents = pd.read_csv(ACCIDENTS_ENRICHED_CSV, dtype=str, low_memory=False)

    contractors['match_text'] = (contractors.get('business_name','').fillna('') + ' ' + contractors.get('address_street','').fillna('') + ' ' + contractors.get('address_city','').fillna('') + ' ' + contractors.get('address_state','').fillna('') + ' ' + contractors.get('address_zip','').fillna('')).apply(normalize_text)
    accidents['match_text'] = (accidents.get('event_desc','').fillna('') + ' ' + accidents.get('event_keyword','').fillna('') + ' ' + accidents.get('abstract_text','').fillna('') + ' ' + accidents.get('report_id','').fillna('')).apply(normalize_text)

    preview = contractors.head(args.preview).copy()

    # fit TF-IDF on combined (preview + accidents)
    corpus = pd.concat([preview['match_text'], accidents['match_text']])
    vectorizer = TfidfVectorizer(ngram_range=(1,2), stop_words='english', max_features=20000)
    vectorizer.fit(corpus)

    acc_tfidf = vectorizer.transform(accidents['match_text'])

    # reduce dimensionality to dense embeddings
    svd = TruncatedSVD(n_components=args.svd_dim, random_state=42)
    acc_emb = svd.fit_transform(acc_tfidf)
    # normalize for cosine similarity in hnswlib (avoid divide-by-zero)
    acc_norms = np.linalg.norm(acc_emb, axis=1, keepdims=True)
    acc_norms[acc_norms == 0] = 1.0
    acc_emb_norm = acc_emb / acc_norms

    # build hnswlib index (cosine)
    dim = acc_emb_norm.shape[1]
    num_elements = acc_emb_norm.shape[0]
    index = hnswlib.Index(space='cosine', dim=dim)
    index.init_index(max_elements=num_elements, ef_construction=200, M=16)
    index.add_items(acc_emb_norm, np.arange(num_elements))
    index.set_ef(50)

    # prepare preview embeddings
    prev_tfidf = vectorizer.transform(preview['match_text'])
    prev_emb = svd.transform(prev_tfidf)
    prev_norms = np.linalg.norm(prev_emb, axis=1, keepdims=True)
    prev_norms[prev_norms == 0] = 1.0
    prev_emb_norm = prev_emb / prev_norms

    rows = []
    for i in range(len(preview)):
        q = prev_emb_norm[i]
        labels, distances = index.knn_query(q, k=args.retrieval_k)
        cand_idxs = labels[0]
        # compute exact TF-IDF cosine similarities for the ANN-proposed candidates
        try:
            sims = linear_kernel(prev_tfidf[i], acc_tfidf[cand_idxs]).flatten()
        except Exception:
            # fallback: approximate from embedding distances
            sims = (1.0 - distances[0])
        # take top return_top by exact tfidf sim
        top_pos = np.argsort(sims)[::-1][:args.return_top]
        for rank, pos in enumerate(top_pos, start=1):
            acc_idx = int(cand_idxs[pos])
            tfidf_sim = float(sims[pos])
            r_score = fuzz.token_set_ratio(preview.iloc[i]['match_text'], accidents.iloc[acc_idx]['match_text'])
            combined = tfidf_w * tfidf_sim + rf_w * (r_score / 100.0)
            rows.append({
                'contractor_index': int(preview.index[i]),
                'business_name': preview.iloc[i].get('business_name',''),
                'address_street': preview.iloc[i].get('address_street',''),
                'address_city': preview.iloc[i].get('address_city',''),
                'address_state': preview.iloc[i].get('address_state',''),
                'contractor_match_text': preview.iloc[i]['match_text'],
                'candidate_rank': rank,
                'candidate_report_id': accidents.iloc[acc_idx].get('report_id',''),
                'candidate_event_desc': accidents.iloc[acc_idx].get('event_desc',''),
                'tfidf_score': tfidf_sim,
                'rapidfuzz_score': r_score,
                'combined': combined,
            })

    out_df = pd.DataFrame(rows)
    OUT_PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUT_PREVIEW, index=False)
    print('Wrote ANN preview to', OUT_PREVIEW)
