#!/usr/bin/env python3
"""Build and save ANN index for accidents corpus (TF-IDF -> SVD -> hnswlib).

Saves:
 - outputs/oshadata/ann_index/index.bin  (hnswlib index)
 - outputs/oshadata/ann_index/vectorizer.joblib
 - outputs/oshadata/ann_index/svd.joblib
 - outputs/oshadata/ann_index/accidents_meta.csv

Supports a --sample option to build a smaller index for testing.
"""
from pathlib import Path
import argparse

ROOT = Path(__file__).resolve().parents[1]
ACCIDENTS_ENRICHED_CSV = ROOT / "outputs" / "oshadata" / "OSHADataDoor_OshaScrapy" / "accidents_asof_022315_enriched.csv"
OUT_DIR = ROOT / "outputs" / "oshadata" / "ann_index"


def normalize_text(s):
    if s is None:
        return ""
    return " ".join(str(s).split()).lower()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--svd-dim', type=int, default=128)
    parser.add_argument('--ef-construction', type=int, default=200)
    parser.add_argument('--M', type=int, default=16)
    parser.add_argument('--sample', type=int, default=0, help='If >0, sample this many accidents for a quick test')
    args = parser.parse_args()

    try:
        import joblib
        import hnswlib
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import TruncatedSVD
    except Exception:
        print('Installing dependencies (hnswlib, scikit-learn, joblib)...')
        import subprocess, sys
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'hnswlib', 'scikit-learn', 'joblib'])
        import joblib
        import hnswlib
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import TruncatedSVD

    import pandas as pd
    import numpy as np

    acc = pd.read_csv(ACCIDENTS_ENRICHED_CSV, dtype=str, low_memory=False)
    acc['match_text'] = (acc.get('event_desc','').fillna('') + ' ' + acc.get('event_keyword','').fillna('') + ' ' + acc.get('abstract_text','').fillna('')).apply(normalize_text)

    if args.sample and args.sample > 0:
        acc = acc.sample(n=min(args.sample, len(acc)), random_state=42).reset_index(drop=True)

    vectorizer = TfidfVectorizer(ngram_range=(1,2), stop_words='english', max_features=20000)
    X = vectorizer.fit_transform(acc['match_text'])

    svd = TruncatedSVD(n_components=args.svd_dim, random_state=42)
    emb = svd.fit_transform(X)

    norms = np.linalg.norm(emb, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    emb_norm = emb / norms

    # build hnswlib index
    dim = emb_norm.shape[1]
    num_elements = emb_norm.shape[0]
    index = hnswlib.Index(space='cosine', dim=dim)
    index.init_index(max_elements=num_elements, ef_construction=args.ef_construction, M=args.M)
    index.add_items(emb_norm, np.arange(num_elements))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    index_path = OUT_DIR / 'index.bin'
    vec_path = OUT_DIR / 'vectorizer.joblib'
    svd_path = OUT_DIR / 'svd.joblib'
    meta_path = OUT_DIR / 'accidents_meta.csv'

    index.save_index(str(index_path))
    joblib.dump(vectorizer, vec_path)
    joblib.dump(svd, svd_path)
    # save minimal meta for mapping indices back to report_id and event_desc
    acc[['report_id','event_desc']].to_csv(meta_path, index=False)

    print('Saved ANN index to', OUT_DIR)
    print('Elements indexed:', num_elements)
