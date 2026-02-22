#!/usr/bin/env python3
"""Simple OSHA local enrichment smoke-test.

Reads the downloaded OSHA accidents CSV and RID lookup, enriches each accident row
with mapped state, normalized datetime, and a fatality boolean. Writes an
enriched CSV to outputs/oshadata/ and prints a short summary.

This is intentionally lightweight for a fast fail-fast smoke test across the
master OSHA dataset.
"""
from pathlib import Path
import sys
import pandas as pd
try:
    from rapidfuzz import process as rf_process
    from rapidfuzz import fuzz as rf_fuzz
    HAVE_RAPIDFUZZ = True
except Exception:
    HAVE_RAPIDFUZZ = False


ROOT = Path(__file__).resolve().parents[1]
OSHADATA_DIR = ROOT / "outputs" / "oshadata" / "OSHADataDoor_OshaScrapy"
ACCIDENTS_CSV = OSHADATA_DIR / "accidents_asof_022315.csv"
RID_CSV = OSHADATA_DIR / "RIDlookup.csv"
OUT_CSV = OSHADATA_DIR / "accidents_asof_022315_enriched.csv"


def load_csv(path: Path, **kwargs) -> pd.DataFrame:
    if not path.exists():
        print(f"ERROR: missing file {path}")
        sys.exit(2)
    return pd.read_csv(path, dtype=str, low_memory=False, **kwargs)


def main():
    print("Loading accidents CSV...", ACCIDENTS_CSV)
    df = load_csv(ACCIDENTS_CSV)

    print("Loading RID lookup...", RID_CSV)
    rid = load_csv(RID_CSV)

    # Normalize column names
    df.columns = [c.strip() for c in df.columns]
    rid.columns = [c.strip() for c in rid.columns]

    # Ensure report_id and RID are strings
    df['report_id'] = df.get('report_id', pd.Series(dtype=str)).astype(str).fillna('')
    rid['RID'] = rid['RID'].astype(str).fillna('')

    # Create normalized numeric-only forms (strip non-digits, leading zeros)
    df['report_id_digits'] = df['report_id'].str.replace(r"\D+", "", regex=True).str.lstrip('0')
    rid['RID_digits'] = rid['RID'].str.replace(r"\D+", "", regex=True).str.lstrip('0')

    # Build mapping RID -> state
    mapping = dict(zip(rid['RID'], rid['state']))
    mapping_digits = dict(zip(rid['RID_digits'], rid['state']))

    # Map state from report_id (exact)
    df['state_enriched'] = df['report_id'].map(mapping)

    # Re-run join using normalized digits where exact mapping missing
    missing_mask = df['state_enriched'].isna() | (df['state_enriched'] == '')
    before_missing = missing_mask.sum()
    # Try digits-based mapping
    df.loc[missing_mask, 'state_enriched'] = df.loc[missing_mask, 'report_id_digits'].map(mapping_digits)

    after_digits_missing = (df['state_enriched'].isna() | (df['state_enriched'] == '')).sum()

    # Try prefix heuristic (first 4 digits) for remaining
    still_missing_mask = df['state_enriched'].isna() | (df['state_enriched'] == '')
    if still_missing_mask.any():
        rid_digits_keys = [k for k in mapping_digits.keys() if k]
        prefix_map = {}
        for k in rid_digits_keys:
            prefix = k[:4]
            prefix_map.setdefault(prefix, []).append(k)

        def try_prefix_match(x):
            if not x or len(x) < 4:
                return None
            px = x[:4]
            candidates = prefix_map.get(px)
            if candidates and len(candidates) == 1:
                return mapping_digits.get(candidates[0])
            return None

        df.loc[still_missing_mask, 'state_enriched'] = df.loc[still_missing_mask, 'report_id_digits'].apply(try_prefix_match)

    after_prefix_missing = (df['state_enriched'].isna() | (df['state_enriched'] == '')).sum()

    # Fuzzy fallback using rapidfuzz (only if installed)
    still_missing_mask = df['state_enriched'].isna() | (df['state_enriched'] == '')
    fuzzy_matched = 0
    if HAVE_RAPIDFUZZ and still_missing_mask.any():
        # Prepare population as RID_digits that are non-empty
        population = [k for k in mapping_digits.keys() if k]
        for idx in df[still_missing_mask].index:
            query = df.at[idx, 'report_id_digits']
            if not query:
                continue
            match = rf_process.extractOne(query, population, scorer=rf_fuzz.ratio)
            if match and match[1] >= 90:
                matched_rid = match[0]
                df.at[idx, 'state_enriched'] = mapping_digits.get(matched_rid)
                fuzzy_matched += 1

    after_fuzzy_missing = (df['state_enriched'].isna() | (df['state_enriched'] == '')).sum()
    print(f"mapping stats: before_missing={before_missing}, after_digits={after_digits_missing}, after_prefix={after_prefix_missing}, fuzzy_matched={fuzzy_matched}, remaining_missing={after_fuzzy_missing}")

    # Parse event_date where possible
    if 'event_date' in df.columns:
        df['event_date_parsed'] = pd.to_datetime(df['event_date'], errors='coerce')
        df['event_year'] = df['event_date_parsed'].dt.year
        df['event_month'] = df['event_date_parsed'].dt.month
    else:
        df['event_date_parsed'] = pd.NaT
        df['event_year'] = None
        df['event_month'] = None

    # Fatality boolean (marker 'X' => True)
    if 'fatality' in df.columns:
        df['fatality_bool'] = df['fatality'].fillna('').astype(str).str.contains('X')
    else:
        df['fatality_bool'] = False

    # Basic dedupe hint: create a small 'match_key' combining report_id + state
    df['match_key'] = df['report_id'].fillna('') + '|' + df['state_enriched'].fillna('')

    # Write enriched CSV (use index=False)
    print(f"Writing enriched CSV to {OUT_CSV} (this may take a moment)")
    df.to_csv(OUT_CSV, index=False)

    total = len(df)
    fatal_count = int(df['fatality_bool'].sum()) if total else 0
    missing_state = int(df['state_enriched'].isna().sum()) if total else 0

    # write a small sample of previously-unmatched rows for inspection
    sample_unmatched = df[df['state_enriched'].isna()].head(200)
    if len(sample_unmatched):
        sample_path = OSHADATA_DIR / 'unmatched_sample.csv'
        sample_unmatched.to_csv(sample_path, index=False)
        print(f"Wrote sample of unmatched rows to {sample_path}")

    print("SMOKE SUMMARY")
    print(f" rows processed: {total}")
    print(f" fatality rows: {fatal_count}")
    print(f" rows missing state mapping: {missing_state}")
    print("enriched CSV written. smoke test complete.")


if __name__ == '__main__':
    main()
