#!/usr/bin/env python3
"""TF-IDF + rapidfuzz contractor -> OSHA accidents matching (fast local preview).

Adds CLI options for mode and explicit weights. Presets:
 - balanced:  TFIDF 0.7, rapidfuzz 0.3, threshold 0.50
 - stricter:  TFIDF 0.8, rapidfuzz 0.2, threshold 0.55
 - safer:     TFIDF 0.6, rapidfuzz 0.4, threshold 0.45

Default run uses the balanced preset.
"""
from pathlib import Path
import sys
import argparse
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CONTRACTOR_CSV = ROOT / "outputs" / "sacramento_contractors_cslb_sac.csv"
ACCIDENTS_ENRICHED_CSV = ROOT / "outputs" / "oshadata" / "OSHADataDoor_OshaScrapy" / "accidents_asof_022315_enriched.csv"
OUT_PREVIEW = ROOT / "outputs" / "sacramento_contractors_cslb_sac_enriched_preview_tfidf.csv"


def load_csv(path: Path, **kwargs) -> pd.DataFrame:
    if not path.exists():
        print(f"ERROR: missing file {path}")
        sys.exit(2)
    return pd.read_csv(path, dtype=str, low_memory=False, **kwargs)


def normalize_text(s: str) -> str:
    if pd.isna(s):
        return ""
    return " ".join(str(s).split()).lower()


def ensure_dependencies():
    # try imports; install scikit-learn if missing
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import linear_kernel
    except Exception:
        print("scikit-learn not installed. Installing now (this may take a moment)...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "scikit-learn"]) 
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import linear_kernel

    try:
        from rapidfuzz import fuzz
    except Exception:
        print("rapidfuzz not installed. Installing now...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "rapidfuzz"]) 


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", type=int, default=100, help="number of contractor rows to preview")
    parser.add_argument("--mode", choices=["balanced", "stricter", "safer"], default="safer", help="preset weighting/threshold mode")
    parser.add_argument("--tfidf-weight", type=float, default=None, help="explicit TF-IDF weight (overrides mode)")
    parser.add_argument("--rf-weight", type=float, default=None, help="explicit rapidfuzz weight (overrides mode)")
    parser.add_argument("--threshold", type=float, default=None, help="combined score threshold (0-1). If omitted, uses mode default")
    parser.add_argument("--candidate-limit", type=int, default=5000, help="if state candidate count > this, prefilter with rapidfuzz")
    parser.add_argument("--prefilter-top", type=int, default=500, help="number of top candidates to keep after prefilter")
    args = parser.parse_args()

    # presets
    presets = {
        'balanced': {'tfidf_w': 0.7, 'rf_w': 0.3, 'threshold': 0.50},
        'stricter': {'tfidf_w': 0.8, 'rf_w': 0.2, 'threshold': 0.55},
        'safer': {'tfidf_w': 0.6, 'rf_w': 0.4, 'threshold': 0.45},
    }

    # determine weights/threshold
    p = presets[args.mode]
    tfidf_w = args.tfidf_weight if args.tfidf_weight is not None else p['tfidf_w']
    rf_w = args.rf_weight if args.rf_weight is not None else p['rf_w']
    if tfidf_w + rf_w == 0:
        print("Invalid weights: sum to zero")
        sys.exit(2)
    # normalize if necessary
    s = tfidf_w + rf_w
    tfidf_w, rf_w = tfidf_w / s, rf_w / s
    threshold = args.threshold if args.threshold is not None else p['threshold']

    print(f"Running preview={args.preview}, mode={args.mode}, tfidf_w={tfidf_w:.2f}, rf_w={rf_w:.2f}, threshold={threshold:.2f}, candidate_limit={args.candidate_limit}, prefilter_top={args.prefilter_top}")

    ensure_dependencies()
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import linear_kernel
    from rapidfuzz import fuzz

    contractors = load_csv(CONTRACTOR_CSV)
    accidents = load_csv(ACCIDENTS_ENRICHED_CSV)

    # Prepare match text
    contractors['match_text'] = (contractors.get('business_name','').fillna('') + ' ' + contractors.get('address_street','').fillna('') + ' ' + contractors.get('address_city','').fillna('') + ' ' + contractors.get('address_state','').fillna('') + ' ' + contractors.get('address_zip','').fillna('')).apply(normalize_text)
    accidents['match_text'] = (accidents.get('event_desc','').fillna('') + ' ' + accidents.get('event_keyword','').fillna('') + ' ' + accidents.get('abstract_text','').fillna('') + ' ' + accidents.get('report_id','').fillna('')).apply(normalize_text)

    accidents['state_enriched'] = accidents.get('state_enriched', accidents.get('state_flag','')).fillna('').astype(str).str.upper()
    contractors['address_state_norm'] = contractors.get('address_state','').fillna('').astype(str).str.upper()

    # Fit TF-IDF on combined corpus for consistency (use preview contractor subset)
    corpus = pd.concat([contractors['match_text'].head(args.preview), accidents['match_text']])
    vectorizer = TfidfVectorizer(ngram_range=(1,2), stop_words='english', max_features=20000)
    vectorizer.fit(corpus)

    acc_tfidf = vectorizer.transform(accidents['match_text'])

    preview = contractors.head(args.preview).copy()
    preview['matched_report_id'] = ''
    preview['matched_similarity'] = 0.0
    preview['tfidf_score'] = 0.0
    preview['rapidfuzz_score'] = 0.0
    preview['matched_event_desc'] = ''
    preview['matched_event_date'] = ''

    # Compute TF-IDF for preview contractors
    contractor_tfidf = vectorizer.transform(preview['match_text'])

    # For each contractor, restrict by state when possible
    for i in range(len(preview)):
        state = preview.iloc[i].get('address_state_norm','')
        c_vec = contractor_tfidf[i]

        if state:
            mask = (accidents['state_enriched'] == state).values
            if mask.sum() == 0:
                candidate_idxs = np.arange(acc_tfidf.shape[0])
            else:
                candidate_idxs = np.where(mask)[0]
        else:
            candidate_idxs = np.arange(acc_tfidf.shape[0])

        if len(candidate_idxs) == 0:
            continue
        # If candidate set is large, prefilter with fast rapidfuzz scorer to keep only top-k
        if len(candidate_idxs) > args.candidate_limit:
            try:
                from rapidfuzz import fuzz as _rf_fuzz
            except Exception:
                _rf_fuzz = None
            if _rf_fuzz is not None:
                # constrain how many candidates we actually run the C-optimized scorer on
                search_idxs = candidate_idxs
                if len(search_idxs) > args.candidate_limit:
                    step = max(1, len(search_idxs) // args.candidate_limit)
                    search_idxs = search_idxs[::step][:args.candidate_limit]
                cand_texts = accidents['match_text'].iloc[search_idxs].fillna('').tolist()
                # use rapidfuzz.process.extract (C-optimized) to get top-k candidates
                try:
                    from rapidfuzz import process as _rf_process
                except Exception:
                    _rf_process = None
                preview_text = preview.iloc[i]['match_text']
                if _rf_process is not None:
                    top_k = min(args.prefilter_top, len(cand_texts))
                    results = _rf_process.extract(preview_text, cand_texts, scorer=_rf_fuzz.token_set_ratio, limit=top_k)
                    # results are tuples (match_str, score, index_in_choices)
                    if results:
                        top_pos = np.array([r[2] for r in results], dtype=int)
                        # map positions back to the original candidate_idxs
                        candidate_idxs = search_idxs[top_pos]
                else:
                    # fallback to python loop if process not available
                    scores = [_rf_fuzz.token_set_ratio(preview.iloc[i]['match_text'], t) for t in cand_texts]
                    top_k = min(args.prefilter_top, len(scores))
                    top_pos = np.argpartition(np.array(scores) * -1, top_k - 1)[:top_k]
                    top_pos = top_pos[np.argsort(np.array(scores)[top_pos])[::-1]]
                    candidate_idxs = candidate_idxs[top_pos]
            else:
                # fallback: reduce by sampling evenly to avoid huge slices
                step = max(1, len(candidate_idxs) // args.prefilter_top)
                candidate_idxs = candidate_idxs[::step][:args.prefilter_top]

        # compute cosine similarities using linear_kernel on slices
        sims = linear_kernel(c_vec, acc_tfidf[candidate_idxs]).flatten()
        best_pos = sims.argmax()
        best_sim = float(sims[best_pos]) if sims.size else 0.0
        acc_idx = candidate_idxs[best_pos]

        # rapidfuzz score between texts
        r_score = fuzz.token_set_ratio(preview.iloc[i]['match_text'], accidents.iloc[acc_idx]['match_text'])
        combined = tfidf_w * best_sim + rf_w * (r_score / 100.0)

        # record raw component scores as well
        preview.at[preview.index[i], 'tfidf_score'] = best_sim
        preview.at[preview.index[i], 'rapidfuzz_score'] = r_score

        if combined >= threshold:
            preview.at[preview.index[i], 'matched_report_id'] = accidents.iloc[acc_idx].get('report_id','')
            preview.at[preview.index[i], 'matched_similarity'] = combined
            preview.at[preview.index[i], 'matched_event_desc'] = accidents.iloc[acc_idx].get('event_desc','')
            preview.at[preview.index[i], 'matched_event_date'] = accidents.iloc[acc_idx].get('event_date','')

    OUT_PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    preview.to_csv(OUT_PREVIEW, index=False)
    print(f"Wrote TF-IDF preview to {OUT_PREVIEW}")
