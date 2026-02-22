#!/usr/bin/env python3
"""Two-stage enrichment pipeline: Stage1 exact joins (RID/phone/address),
Stage2 fuzzy TF-IDF only on leftovers (state-filtered + prefilter guard).

Writes combined enriched CSV and an unmatched leftovers CSV.
"""
from pathlib import Path
import argparse
import sys
import re

ROOT = Path(__file__).resolve().parents[1]
CONTRACTOR_CSV = ROOT / "outputs" / "sacramento_contractors_cslb_sac.csv"
ACCIDENTS_ENRICHED_CSV = ROOT / "outputs" / "oshadata" / "OSHADataDoor_OshaScrapy" / "accidents_asof_022315_enriched.csv"
OUT_COMBINED = ROOT / "outputs" / "oshadata" / "two_stage_enriched.csv"
OUT_LEFTOVERS = ROOT / "outputs" / "oshadata" / "two_stage_leftovers.csv"


def normalize_address(addr: str) -> str:
    if addr is None:
        return ""
    s = str(addr).lower()
    s = re.sub(r"[.,/]", " ", s)
    s = re.sub(r"\b(apt|suite|ste|#|unit|fl|floor|rm)\b[:\s]*[\w-]*", "", s)
    abbr = {r"\bst\b": "street", r"\brd\b": "road", r"\bave\b": "avenue", r"\bblvd\b": "boulevard", r"\bln\b": "lane", r"\bdr\b": "drive", r"\bct\b": "court", r"\bpk wy\b": "parkway"}
    for k, v in abbr.items():
        s = re.sub(k, v, s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def normalize_phone(ph: str) -> str:
    if ph is None:
        return ""
    s = re.sub(r"[^0-9]", "", str(ph))
    return s[-10:] if len(s) >= 10 else s


def normalize_text(s: str) -> str:
    if s is None:
        return ""
    return " ".join(str(s).split()).lower()


def stage1_exact_join(contractors, accidents):
    # prepare normalized keys
    # helper to return a Series even when column missing
    def series_or_blank(df, col):
        import pandas as _pd
        if col in df.columns:
            return df[col].astype(str).fillna('')
        return _pd.Series([''] * len(df), index=df.index)

    contractors['norm_phone'] = series_or_blank(contractors, 'phone').apply(normalize_phone)
    contractors['norm_address'] = (series_or_blank(contractors, 'address_street') + ' ' + series_or_blank(contractors, 'address_city') + ' ' + series_or_blank(contractors, 'address_state') + ' ' + series_or_blank(contractors, 'address_zip')).apply(normalize_address)

    # ensure accidents have normalized columns
    if 'phone' in accidents.columns:
        accidents['norm_phone'] = accidents['phone'].astype(str).fillna('').apply(normalize_phone)
    else:
        accidents['norm_phone'] = ''
    acc_addr_field = 'address' if 'address' in accidents.columns else ('event_location' if 'event_location' in accidents.columns else None)
    if acc_addr_field:
        accidents['norm_address'] = accidents[acc_addr_field].astype(str).fillna('').apply(normalize_address)
    else:
        accidents['norm_address'] = ''

    # init match columns
    contractors['matched_report_id'] = ''
    contractors['match_source'] = ''

    # build lookup maps for fast exact matches
    phone_map = {}
    if accidents['norm_phone'].dtype != object:
        accidents['norm_phone'] = accidents['norm_phone'].astype(str)
    for i, a in accidents.iterrows():
        p = str(a.get('norm_phone','') or '')
        if p:
            phone_map.setdefault(p, []).append(a.get('report_id',''))
    addr_map = {}
    for i, a in accidents.iterrows():
        ad = str(a.get('norm_address','') or '')
        if ad:
            addr_map.setdefault(ad, []).append(a.get('report_id',''))

    # run exact phone join then address
    for idx, c in contractors.iterrows():
        if contractors.at[idx,'matched_report_id']:
            continue
        p = c.get('norm_phone','')
        if p and p in phone_map:
            contractors.at[idx,'matched_report_id'] = phone_map[p][0]
            contractors.at[idx,'match_source'] = 'phone_exact'
            continue
        a = c.get('norm_address','')
        if a and a in addr_map:
            contractors.at[idx,'matched_report_id'] = addr_map[a][0]
            contractors.at[idx,'match_source'] = 'address_exact'
            continue
        # direct RID on contractor if present
        for col in ['report_id','matched_report_id','candidate_report_id']:
            if col in contractors.columns:
                rid = str(c.get(col,'') or '')
                if rid and (rid in set(accidents['report_id'].astype(str))):
                    contractors.at[idx,'matched_report_id'] = rid
                    contractors.at[idx,'match_source'] = 'rid_exact'
                    break

    matched = contractors[contractors['matched_report_id'].astype(bool)].copy()
    leftovers = contractors[~contractors['matched_report_id'].astype(bool)].copy()
    return matched, leftovers


def stage2_tfidf_fuzzy(leftovers, accidents, preset='safer', candidate_limit=5000, prefilter_top=500):
    # run TF-IDF fuzzy matching only on leftovers; returns matched subset
    if len(leftovers) == 0:
        return leftovers.iloc[0:0]

    presets = {
        'balanced': {'tfidf_w': 0.7, 'rf_w': 0.3, 'threshold': 0.50},
        'stricter': {'tfidf_w': 0.8, 'rf_w': 0.2, 'threshold': 0.55},
        'safer': {'tfidf_w': 0.6, 'rf_w': 0.4, 'threshold': 0.45},
    }
    p = presets.get(preset, presets['safer'])
    tfidf_w = p['tfidf_w']; rf_w = p['rf_w']; threshold = p['threshold']

    # prepare match_text
    leftovers['match_text'] = (leftovers.get('business_name','').fillna('') + ' ' + leftovers.get('address_street','').fillna('') + ' ' + leftovers.get('address_city','').fillna('') + ' ' + leftovers.get('address_state','').fillna('') + ' ' + leftovers.get('address_zip','').fillna('')).apply(normalize_text)
    accidents['match_text'] = (accidents.get('event_desc','').fillna('') + ' ' + accidents.get('event_keyword','').fillna('') + ' ' + accidents.get('abstract_text','').fillna('') + ' ' + accidents.get('report_id','').fillna('')).apply(normalize_text)

    # state norms
    accidents['state_enriched'] = accidents.get('state_enriched', accidents.get('state_flag','')).fillna('').astype(str).str.upper()
    leftovers['address_state_norm'] = leftovers.get('address_state','').fillna('').astype(str).str.upper()

    # vectorizer fit on leftovers + accidents
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import linear_kernel
    from rapidfuzz import fuzz
    import numpy as np

    corpus = list(leftovers['match_text']) + list(accidents['match_text'])
    vectorizer = TfidfVectorizer(ngram_range=(1,2), stop_words='english', max_features=20000)
    vectorizer.fit(corpus)
    acc_tfidf = vectorizer.transform(accidents['match_text'])
    leftover_tfidf = vectorizer.transform(leftovers['match_text'])

    matched_rows = []
    for i in range(len(leftovers)):
        state = leftovers.iloc[i].get('address_state_norm','')
        c_vec = leftover_tfidf[i]

        if state:
            mask = (accidents['state_enriched'] == state).values
            candidate_idxs = np.where(mask)[0] if mask.sum() else np.arange(acc_tfidf.shape[0])
        else:
            candidate_idxs = np.arange(acc_tfidf.shape[0])

        # candidate-size guard
        if len(candidate_idxs) > candidate_limit:
            try:
                from rapidfuzz import process as _rf_process, fuzz as _rf_fuzz
                cand_texts = accidents['match_text'].iloc[candidate_idxs].fillna('').tolist()
                preview_text = leftovers.iloc[i]['match_text']
                top_k = min(prefilter_top, len(cand_texts))
                results = _rf_process.extract(preview_text, cand_texts, scorer=_rf_fuzz.token_set_ratio, limit=top_k)
                if results:
                    top_pos = [r[2] for r in results]
                    candidate_idxs = np.array(candidate_idxs)[top_pos]
            except Exception:
                step = max(1, len(candidate_idxs) // prefilter_top)
                candidate_idxs = candidate_idxs[::step][:prefilter_top]

        sims = linear_kernel(c_vec, acc_tfidf[candidate_idxs]).flatten()
        if sims.size == 0:
            continue
        best_pos = sims.argmax()
        best_sim = float(sims[best_pos])
        acc_idx = int(candidate_idxs[best_pos])
        r_score = fuzz.token_set_ratio(leftovers.iloc[i]['match_text'], accidents.iloc[acc_idx]['match_text'])
        combined = tfidf_w * best_sim + rf_w * (r_score / 100.0)
        if combined >= threshold:
            row = leftovers.iloc[i].to_dict()
            row.update({'matched_report_id': accidents.iloc[acc_idx].get('report_id',''), 'match_source': 'tfidf_fuzzy', 'tfidf_score': best_sim, 'rapidfuzz_score': r_score, 'combined': combined})
            matched_rows.append(row)

    import pandas as pd
    if matched_rows:
        return pd.DataFrame(matched_rows)
    return leftovers.iloc[0:0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--preview', type=int, default=0, help='limit contractors processed (0 = all)')
    parser.add_argument('--candidate-limit', type=int, default=5000)
    parser.add_argument('--prefilter-top', type=int, default=500)
    parser.add_argument('--preset', choices=['balanced','stricter','safer'], default='safer')
    args = parser.parse_args()

    import pandas as pd
    import numpy as np

    contractors = pd.read_csv(CONTRACTOR_CSV, dtype=str, low_memory=False)
    accidents = pd.read_csv(ACCIDENTS_ENRICHED_CSV, dtype=str, low_memory=False)

    if args.preview and args.preview > 0:
        contractors = contractors.head(args.preview).copy()

    # Stage 1: exact joins
    matched1, leftovers = stage1_exact_join(contractors, accidents)

    # write stage1 results
    OUT_COMBINED.parent.mkdir(parents=True, exist_ok=True)
    matched1.to_csv(OUT_COMBINED.with_suffix('.stage1.csv'), index=False)
    leftovers.to_csv(OUT_LEFTOVERS.with_suffix('.stage1_leftovers.csv'), index=False)

    # Stage 2: fuzzy on leftovers
    try:
        matched2 = stage2_tfidf_fuzzy(leftovers, accidents, preset=args.preset, candidate_limit=args.candidate_limit, prefilter_top=args.prefilter_top)
    except Exception as e:
        print('Stage2 TF-IDF failed:', e)
        matched2 = leftovers.iloc[0:0]

    # combine
    import pandas as pd
    final = pd.concat([matched1, matched2], ignore_index=True, sort=False)
    final.to_csv(OUT_COMBINED, index=False)
    # leftovers after stage2
    remaining = contractors[~contractors.get('matched_report_id','').fillna('').astype(bool)]
    remaining.to_csv(OUT_LEFTOVERS, index=False)
    print('Wrote final two-stage enriched CSV to', OUT_COMBINED)
    print('Wrote leftovers to', OUT_LEFTOVERS)


if __name__ == '__main__':
    main()
