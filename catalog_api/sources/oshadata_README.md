OSHA DataDoor manifests

This folder contains manifests describing locally-downloaded OSHA DataDoor datasets.

Files:
- `oshadata_accidents.json`: Incident-level accidents dataset (from `outputs/oshadata/OSHADataDoor_OshaScrapy/accidents_asof_022315.csv`).
- `oshadata_ridlookup.json`: Mapping file from `RID` to `state`.
- `oshadata_state_employment.json`: State-level employment snapshot CSV.

How to run the quick enrichment smoke-test:

1. Install dependencies (recommended in a virtualenv):

```bash
python -m pip install -r requirements.txt
```

2. Run the lightweight OSHA enrichment smoke-test (reads local CSVs and writes an enriched CSV):

```bash
python scripts/osha_local_enrich.py
```

Outputs:
- `outputs/oshadata/OSHADataDoor_OshaScrapy/accidents_asof_022315_enriched.csv` — enriched accidents dataset
- `outputs/oshadata/OSHADataDoor_OshaScrapy/unmatched_sample.csv` — up to 200 unmatched rows for inspection

Notes:
- The script will attempt exact RID joins, numeric normalization, prefix heuristics, and will use `rapidfuzz` for fuzzy RID matching if installed.
- If you want contractor-level fuzzy joins (name/address) you can pass contractor CSV into an enhanced script; I can add that next.
