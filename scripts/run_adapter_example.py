"""Run an example adapter against a contractor and write result to enrichment DB."""
from pathlib import Path
import json

from src.adapters import get_adapter, list_adapters
from src.enrichment_models import EnrichmentDB


def main():
    repo_root = Path(__file__).resolve().parents[1]
    target = repo_root / "outputs" / "enrichment_migration_preview.db"
    db = EnrichmentDB(str(target))
    db.create_all()

    # ensure a contractor exists
    cid = db.upsert_contractor("SAMPLE-0001", business_name="Demo Contractor", address_city="Sacramento")
    print("Using contractor id", cid)

    print("Available adapters:", list_adapters())
    adapter = get_adapter("google_places")
    prospect = {"license_number": "SAMPLE-0001", "business_name": "Demo Contractor"}
    result = adapter.enrich(prospect)
    rid = db.upsert_enrichment_result(cid, adapter.name, result, success=True, latency_ms=42, phase=adapter.phase)
    print("Wrote enrichment result id", rid)


if __name__ == "__main__":
    main()
