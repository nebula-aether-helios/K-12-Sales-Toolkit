#!/usr/bin/env python3
"""Contractor -> OSHA accidents semantic matching using sentence-transformers embeddings.

This script loads the Sacramento CSLB contractors CSV and the enriched OSHA
accidents CSV and computes sentence-transformer embeddings for contractor
name+address and accident descriptions. It finds the nearest accident per
contractor within the same state using cosine similarity and writes a preview
CSV with the best matches.

Defaults to a 100-row preview for fast testing.
"""
from pathlib import Path
import sys
import argparse
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CONTRACTOR_CSV = ROOT / "outputs" / "sacramento_contractors_cslb_sac.csv"
ACCIDENTS_ENRICHED_CSV = ROOT / "outputs" / "oshadata" / "OSHADataDoor_OshaScrapy" / "accidents_asof_022315_enriched.csv"
OUT_PREVIEW = ROOT / "outputs" / "sacramento_contractors_cslb_sac_enriched_preview_bert.csv"


def load_csv(path: Path, **kwargs) -> pd.DataFrame:
    if not path.exists():
        print(f"ERROR: missing file {path}")
        sys.exit(2)
    return pd.read_csv(path, dtype=str, low_memory=False, **kwargs)


def normalize_text(s: str) -> str:
    if pd.isna(s):
        return ""
    return " ".join(str(s).split())


def embed_texts(model, texts, batch_size=64):
    # model.encode returns numpy arrays
    return model.encode(texts, batch_size=batch_size, show_progress_bar=False, convert_to_numpy=True, normalize_embeddings=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", type=int, default=100, help="number of contractor rows to preview")
    parser.add_argument("--threshold", type=float, default=0.60, help="cosine similarity threshold for matches (0-1)")
    args = parser.parse_args()

    print("Loading contractor seed...", CONTRACTOR_CSV)
    contractors = load_csv(CONTRACTOR_CSV)
    print("Loading enriched accidents...", ACCIDENTS_ENRICHED_CSV)
    accidents = load_csv(ACCIDENTS_ENRICHED_CSV)

    # Prepare text fields
    contractors['match_text'] = (contractors.get('business_name','').fillna('') + ' ' + contractors.get('address_street','').fillna('') + ' ' + contractors.get('address_city','').fillna('') + ' ' + contractors.get('address_state','').fillna('')).apply(normalize_text)

    accidents['match_text'] = (accidents.get('event_desc','').fillna('') + ' ' + accidents.get('event_keyword','').fillna('') + ' ' + accidents.get('abstract_text','').fillna('')).apply(normalize_text)

    # Load model lazily
    try:
        from sentence_transformers import SentenceTransformer
    except Exception as e:
        print("ERROR: sentence-transformers not installed. Install with: pip install sentence-transformers")
        raise

    print("Loading embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Limit accidents by state per contractor during nearest-neighbor search;
    # precompute embeddings for accidents grouped by state to speed repeated queries.
    print("Computing accident embeddings (this may take a moment)...")
    accidents['state_enriched'] = accidents.get('state_enriched', accidents.get('state_flag', '')).fillna('')

    # Build embeddings for all accidents once
    accident_texts = accidents['match_text'].fillna('').tolist()
    accident_embeddings = embed_texts(model, accident_texts)

    # index mapping
    accidents_idx = accidents.reset_index(drop=True)

    # Preview contractors
    preview_df = contractors.head(args.preview).copy()
    preview_df['matched_report_id'] = ''
    preview_df['matched_similarity'] = 0.0
    preview_df['matched_event_date'] = ''
    preview_df['matched_event_desc'] = ''

    # compute embeddings for preview contractors
    contractor_texts = preview_df['match_text'].fillna('').tolist()
    print(f"Computing embeddings for {len(contractor_texts)} contractors...")
    contractor_embeddings = embed_texts(model, contractor_texts)

    # Normalize accidents' state to upper for matching
    accidents_idx['state_enriched'] = accidents_idx.get('state_enriched','').fillna('').str.upper()

    # For each contractor, restrict to accidents in same state when available
    for i, row in preview_df.iterrows():
        state = (row.get('address_state') or '').strip().upper()
        c_emb = contractor_embeddings[i]
        # select candidate indices
        if state:
            candidates_mask = accidents_idx['state_enriched'] == state
            if not candidates_mask.any():
                candidates_mask = accidents_idx['state_enriched'] == ''
        else:
            candidates_mask = accidents_idx['state_enriched'] == ''

        cand_idxs = np.where(candidates_mask.values)[0]
        if len(cand_idxs) == 0:
            # fallback: use all accidents
            cand_idxs = np.arange(len(accident_embeddings))

        # compute cosine similarities (embeddings normalized)
        cand_embs = accident_embeddings[cand_idxs]
        sims = np.dot(cand_embs, c_emb)
        best_idx = np.argmax(sims)
        best_sim = float(sims[best_idx]) if len(sims) else 0.0
        if best_sim >= args.threshold:
            chosen = accidents_idx.iloc[cand_idxs[best_idx]]
            preview_df.at[i, 'matched_report_id'] = chosen.get('report_id','')
            preview_df.at[i, 'matched_similarity'] = best_sim
            preview_df.at[i, 'matched_event_date'] = chosen.get('event_date','')
            preview_df.at[i, 'matched_event_desc'] = chosen.get('event_desc','')

    # Write preview
    OUT_PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    preview_df.to_csv(OUT_PREVIEW, index=False)
    print(f"Wrote preview with {len(preview_df)} rows to {OUT_PREVIEW}")


if __name__ == '__main__':
    main()
