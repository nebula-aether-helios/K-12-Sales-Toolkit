#!/usr/bin/env python3
"""
Simple Google Places enrichment pipeline (Text Search -> Find Place -> Details)

Fail-fast smoke test: verify API key and a sample Text Search before processing CSV rows.

Usage:
  python scripts/google_places_enrich.py \
    --input outputs/sacramento_contractors_cslb_sac.csv \
    --output outputs/sacramento_contractors_cslb_sac_enriched.csv \
    --batch 50

"""
import os
import time
import argparse
import logging
from typing import Optional, Dict, Any

import requests
import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm

logger = logging.getLogger("gp_enrich")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

PLACES_TEXTSEARCH = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACES_FINDPLACE = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
PLACES_DETAILS = "https://maps.googleapis.com/maps/api/place/details/json"


def load_api_key() -> Optional[str]:
    load_dotenv()
    return os.environ.get("GOOGLE_PLACES_API_KEY")


def smoke_test_key(api_key: str, timeout: int = 10) -> bool:
    """Perform a quick Text Search to validate the API key and connectivity (fail-fast)."""
    params = {"query": "Sacramento City Hall", "key": api_key}
    try:
        r = requests.get(PLACES_TEXTSEARCH, params=params, timeout=timeout)
    except Exception as e:
        logger.error("Smoke test request failed: %s", e)
        return False
    if r.status_code != 200:
        logger.error("Smoke test HTTP error: %s", r.status_code)
        return False
    j = r.json()
    status = j.get("status")
    if status not in ("OK", "ZERO_RESULTS"):
        logger.error("Smoke test Places API status: %s, response: %s", status, j.get("error_message"))
        return False
    logger.info("Smoke test passed (status=%s)", status)
    return True


def find_place(query: str, api_key: str) -> Optional[str]:
    params = {
        "input": query,
        "inputtype": "textquery",
        "fields": "place_id,name,formatted_address",
        "key": api_key,
    }
    r = requests.get(PLACES_FINDPLACE, params=params, timeout=10)
    if r.status_code != 200:
        logger.debug("FindPlace HTTP %s for query=%s", r.status_code, query)
        return None
    j = r.json()
    if j.get("status") != "OK":
        return None
    candidates = j.get("candidates", [])
    if not candidates:
        return None
    return candidates[0].get("place_id")


def get_place_details(place_id: str, api_key: str) -> Dict[str, Any]:
    fields = ",".join([
        "name",
        "formatted_address",
        "formatted_phone_number",
        "website",
        "rating",
        "user_ratings_total",
        "reviews",
    ])
    params = {"place_id": place_id, "fields": fields, "key": api_key}
    r = requests.get(PLACES_DETAILS, params=params, timeout=10)
    if r.status_code != 200:
        return {}
    j = r.json()
    if j.get("status") != "OK":
        return {}
    result = j.get("result", {})
    return result


def build_query_from_row(row: pd.Series) -> str:
    # Try common column names, fallback to concatenating all string values
    parts = []
    for col in ("business_name", "name", "company", "organization"):
        if col in row and pd.notna(row[col]):
            parts.append(str(row[col]))
            break
    for col in ("address", "street", "address1", "addr"):
        if col in row and pd.notna(row[col]):
            parts.append(str(row[col]))
            break
    for col in ("city", "town"):
        if col in row and pd.notna(row[col]):
            parts.append(str(row[col]))
            break
    for col in ("state", "region"):
        if col in row and pd.notna(row[col]):
            parts.append(str(row[col]))
            break
    if not parts:
        # fallback: use first three non-null string columns
        for v in row.astype(str).values.tolist()[:3]:
            if v and v.lower() != "nan":
                parts.append(v)
    return ", ".join(parts)


def enrich_dataframe(df: pd.DataFrame, api_key: str, batch_size: int = 50) -> pd.DataFrame:
    out_rows = []
    for idx in tqdm(df.index, desc="Rows"):
        row = df.loc[idx]
        query = build_query_from_row(row)
        if not query:
            out = {"place_id": None, "gp_name": None}
            out_rows.append({**row.to_dict(), **out})
            continue
        place_id = find_place(query, api_key)
        if not place_id:
            out = {"place_id": None}
            out_rows.append({**row.to_dict(), **out})
            continue
        details = get_place_details(place_id, api_key)
        # extract top-level useful fields
        enriched = {
            "place_id": place_id,
            "gp_name": details.get("name"),
            "gp_address": details.get("formatted_address"),
            "gp_phone": details.get("formatted_phone_number"),
            "gp_website": details.get("website"),
            "gp_rating": details.get("rating"),
            "gp_user_ratings_total": details.get("user_ratings_total"),
            "gp_reviews": details.get("reviews"),
        }
        out_rows.append({**row.to_dict(), **enriched})
        # polite pause to reduce burst quota risk
        time.sleep(0.1)
    return pd.DataFrame(out_rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=False, default="outputs/sacramento_contractors_cslb_sac.csv")
    parser.add_argument("--output", required=False, default="outputs/sacramento_contractors_cslb_sac_enriched.csv")
    parser.add_argument("--batch", type=int, default=50)
    args = parser.parse_args()

    api_key = load_api_key()
    if not api_key:
        logger.error("No GOOGLE_PLACES_API_KEY found in environment. Populate .env or set env var and retry.")
        raise SystemExit(1)

    logger.info("Running smoke test for API key and connectivity...")
    if not smoke_test_key(api_key):
        logger.error("Smoke test failed. Aborting to fail fast.")
        raise SystemExit(1)

    logger.info("Reading input CSV: %s", args.input)
    df = pd.read_csv(args.input, dtype=str)
    if df.empty:
        logger.error("Input CSV is empty: %s", args.input)
        raise SystemExit(1)

    logger.info("Starting enrichment of %d rows (single-worker).", len(df))
    enriched = enrich_dataframe(df, api_key, batch_size=args.batch)

    logger.info("Writing enriched output to %s", args.output)
    enriched.to_csv(args.output, index=False)
    logger.info("Done. Enriched rows: %d", len(enriched))


if __name__ == "__main__":
    main()
