"""Worker process to consume enrichment tasks from RabbitMQ and execute adapters.

Usage: python scripts/worker.py --db outputs/enrichment.db
"""
import time
import argparse
import logging
import json
from typing import Dict

from src.queue import consume_tasks
from src.enrichment_models import EnrichmentDB, Contractor
from src.adapters import ADAPTER_REGISTRY


def process_task(db: EnrichmentDB, payload: Dict):
    contractor_id = payload.get("contractor_id")
    adapter_name = payload.get("adapter")
    adapter = ADAPTER_REGISTRY.get(adapter_name)
    if adapter is None:
        logging.error("Adapter %s not registered", adapter_name)
        return

    session = db.SessionLocal()
    try:
        contractor = session.query(Contractor).filter(Contractor.id == contractor_id).one_or_none()
        if contractor is None:
            logging.error("Contractor %s not found", contractor_id)
            return
        prospect = contractor.to_dict()
    finally:
        session.close()

    # retry/backoff
    retries = 3
    backoff = 1.0
    for attempt in range(1, retries + 1):
        try:
            fragment = adapter.enrich(prospect)
            db.upsert_enrichment_result(contractor_id, adapter_name, fragment, success=True, latency_ms=0, phase=getattr(adapter, "phase", 0))
            logging.info("Processed %s for %s", adapter_name, contractor_id)
            return
        except Exception:
            logging.exception("Adapter %s failed on attempt %d for %s", adapter_name, attempt, contractor_id)
            time.sleep(backoff)
            backoff *= 2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="outputs/enrichment.db")
    parser.add_argument("--local", action="store_true", help="Use in-process local queue instead of RabbitMQ")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    db = EnrichmentDB(args.db)
    db.create_all()

    def _cb(payload):
        if isinstance(payload, (bytes, str)):
            try:
                payload = json.loads(payload)
            except Exception:
                logging.error("Invalid payload: %s", payload)
                return
        process_task(db, payload)

    logging.info("Worker started, consuming tasks... local=%s", args.local)
    if args.local:
        from src.queue import get_local_queue
        q = get_local_queue()
        # use same consume loop but adapted for local queue
        while True:
            item = q.get()
            if item is None:
                logging.info("Worker received stop sentinel, exiting")
                break
            _cb(item)
    else:
        consume_tasks(_cb)


if __name__ == "__main__":
    main()
