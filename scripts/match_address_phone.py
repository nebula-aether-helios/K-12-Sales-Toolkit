#!/usr/bin/env python3
"""Simple address+phone matching preview.

Normalizes addresses and phone numbers for contractors and accidents and
produces a lightweight preview by exact-match on normalized phone or
address, falling back to a fuzzy token_set_ratio on address when needed.
This avoids heavy TF-IDF sparse cosine work.
"""
from pathlib import Path
import argparse
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
CONTRACTOR_CSV = ROOT / "outputs" / "sacramento_contractors_cslb_sac.csv"
ACCIDENTS_ENRICHED_CSV = ROOT / "outputs" / "oshadata" / "OSHADataDoor_OshaScrapy" / "accidents_asof_022315_enriched.csv"
OUT_PREVIEW = ROOT / "outputs" / "oshadata" / "address_phone_preview.csv"


def normalize_address(addr: str) -> str:
    if addr is None:
        return ""
    s = str(addr).lower()
    # remove punctuation
    s = re.sub(r"[.,/]", " ", s)
    # remove unit tokens (apt, suite, ste, #, unit, floor)
    s = re.sub(r"\b(apt|suite|ste|#|unit|fl|floor|rm)\b[:\s]*[\w-]*", "", s)
    # common abbreviations
    abbr = {
        r"\bst\b": "street",
        r"\brd\b": "road",
        r"\bave\b": "avenue",
        r"\bblvd\b": "boulevard",
        r"\bln\b": "lane",
        r"\bdr\b": "drive",
        r"\bctr\b": "center",
        r"\bct\b": "court",
        r"\bpkwy\b": "parkway",
        r"\bste\b": "",
    }
    for k, v in abbr.items():
        s = re.sub(k, v, s)
    # collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s


def normalize_phone(ph: str) -> str:
    if ph is None:
        return ""
    s = re.sub(r"[^0-9]", "", str(ph))
    # prefer last 10 digits (US numbers)
    if len(s) >= 10:
        return s[-10:]
    return s


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--preview', type=int, default=500)
    parser.add_argument('--return-top', type=int, default=5)
    args = parser.parse_args()

    import pandas as pd
    from rapidfuzz import fuzz

    contractors = pd.read_csv(CONTRACTOR_CSV, dtype=str, low_memory=False)
    accidents = pd.read_csv(ACCIDENTS_ENRICHED_CSV, dtype=str, low_memory=False)

    def series_or_blank(df, col):
        import pandas as _pd
        if col in df.columns:
            return df[col].astype(str).fillna('')
        return _pd.Series([''] * len(df), index=df.index)

    contractors['norm_address'] = (series_or_blank(contractors, 'address_street') + ' ' + series_or_blank(contractors, 'address_city') + ' ' + series_or_blank(contractors, 'address_state') + ' ' + series_or_blank(contractors, 'address_zip')).apply(normalize_address)
    contractors['norm_phone'] = series_or_blank(contractors, 'phone').apply(normalize_phone)

    # accidents address
    acc_addr_field = 'address' if 'address' in accidents.columns else ('event_location' if 'event_location' in accidents.columns else None)
    if acc_addr_field:
        accidents['norm_address'] = series_or_blank(accidents, acc_addr_field).apply(normalize_address)
    else:
        accidents['norm_address'] = ''

    # try multiple phone columns
    phone_col = None
    for c in ['phone','contact_phone','phone_number']:
        if c in accidents.columns:
            phone_col = c
            break
    if phone_col:
        accidents['norm_phone'] = series_or_blank(accidents, phone_col).apply(normalize_phone)
    else:
        accidents['norm_phone'] = ''

    preview = contractors.head(args.preview).copy()

    rows = []
    for idx, c in preview.iterrows():
        c_addr = c.get('norm_address','')
        c_phone = c.get('norm_phone','')

        # exact phone matches
        phone_matches = accidents[accidents['norm_phone'] == c_phone] if c_phone else accidents.iloc[0:0]
        # exact address matches
        addr_matches = accidents[accidents['norm_address'] == c_addr] if c_addr else accidents.iloc[0:0]

        # union candidates
        cand_idxs = pd.Index(pd.concat([phone_matches, addr_matches]).index.unique())

        # if no exact candidates, perform fuzzy address scan (fast enough on moderate corpus)
        if len(cand_idxs) == 0:
            # compute token_set_ratio over accidents.norm_address and take top-k
            candidates = accidents[['norm_address']].copy()
            candidates['score'] = candidates['norm_address'].apply(lambda a: fuzz.token_set_ratio(c_addr, a) if a else 0)
            topc = candidates.sort_values('score', ascending=False).head(100)
            cand_idxs = topc.index

        # rank candidates: phone exact first, then address exact, then fuzzy score
        cand_rows = []
        for ai in cand_idxs:
            a = accidents.loc[ai]
            phone_match_flag = (c_phone and a.get('norm_phone','') == c_phone)
            addr_match_flag = (c_addr and a.get('norm_address','') == c_addr)
            if phone_match_flag:
                score = 1.0
            elif addr_match_flag:
                score = 0.95
            else:
                score = (fuzz.token_set_ratio(c_addr, a.get('norm_address','')) or 0) / 100.0
            cand_rows.append((ai, score))

        cand_rows = sorted(cand_rows, key=lambda t: t[1], reverse=True)[:args.return_top]
        for rank, (ai, score) in enumerate(cand_rows, start=1):
            a = accidents.loc[ai]
            rows.append({
                'contractor_index': int(idx),
                'business_name': c.get('business_name',''),
                'contractor_address': c.get('address_street',''),
                'contractor_city': c.get('address_city',''),
                'contractor_state': c.get('address_state',''),
                'contractor_phone': c.get('phone',''),
                'candidate_rank': rank,
                'candidate_report_id': a.get('report_id',''),
                'candidate_event_desc': a.get('event_desc',''),
                'match_score': float(score),
            })

    out_df = pd.DataFrame(rows)
    OUT_PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUT_PREVIEW, index=False)
    print('Wrote address+phone preview to', OUT_PREVIEW)
