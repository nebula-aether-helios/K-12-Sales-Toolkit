"""Deep enrichment pipeline CLI entrypoint

Provides simple commands to run local enrichment flows:
- producer: enqueue tasks (uses workers.producer)
- consumer: run a single consumer (uses workers.consumer)
- quick: run a fast local batch (uses workers.quick_run)

Tuned defaults are chosen for a local machine: 8 workers for quick-run, DNS timeout 3s.
"""
from pathlib import Path
import argparse
import sys

# Tunable defaults
DEFAULT_DB_URL = "sqlite:///enrichment.db"
DEFAULT_RABBITMQ = "amqp://guest:guest@localhost:5672/"
DEFAULT_QUICK_WORKERS = 4
DEFAULT_QUICK_LIMIT = 500
DEFAULT_DNS_TIMEOUT = 3


def run_producer(args):
    from workers.producer import publish_tasks
    input_csv = args.input
    rabbit = args.rabbitmq or DEFAULT_RABBITMQ
    queue = args.queue or "enrich_tasks"
    print(f"Publishing tasks from {input_csv} to {rabbit} (queue={queue})")
    publish_tasks(input_csv, rabbit, queue)
    print("Producer finished.")


def run_consumer(args):
    from workers.consumer import consume
    rabbit = args.rabbitmq or DEFAULT_RABBITMQ
    db = args.db or DEFAULT_DB_URL
    enable_smtp = args.enable_smtp
    print(f"Starting consumer against {rabbit}; DB={db}; enable_smtp={enable_smtp}")
    # consumer.consume blocks and runs forever until interrupted
    consume(rabbit, args.queue or "enrich_tasks", db)


def run_quick(args):
    from workers.quick_run import run_quick
    input_csv = args.input
    db = args.db or DEFAULT_DB_URL
    limit = args.limit or DEFAULT_QUICK_LIMIT
    workers = args.workers or DEFAULT_QUICK_WORKERS
    enable_smtp = args.enable_smtp
    print(f"Running quick batch: {limit} rows, workers={workers}, smtp={enable_smtp}")
    ids = run_quick(input_csv, db, limit, workers, enable_smtp)
    print(f"Quick run completed: processed {len(ids)} rows")


def main():
    parser = argparse.ArgumentParser(description="Deep enrichment pipeline entrypoint")
    sub = parser.add_subparsers(dest="cmd")

    p_prod = sub.add_parser("producer")
    p_prod.add_argument("--input", required=True)
    # Accept both --rabbitmq and legacy/alternate --rabbitmq-url
    p_prod.add_argument("--rabbitmq", "--rabbitmq-url", dest="rabbitmq", required=False)
    p_prod.add_argument("--queue", required=False)

    p_cons = sub.add_parser("consumer")
    p_cons.add_argument("--rabbitmq", "--rabbitmq-url", dest="rabbitmq", required=False)
    # Accept both --db and --db-url for backward compatibility
    p_cons.add_argument("--db", "--db-url", dest="db", required=False)
    p_cons.add_argument("--queue", required=False)
    p_cons.add_argument("--enable-smtp", action="store_true")

    p_quick = sub.add_parser("quick")
    p_quick.add_argument("--input", required=True)
    # Accept both --db and --db-url
    p_quick.add_argument("--db", "--db-url", dest="db", required=False)
    p_quick.add_argument("--limit", type=int, required=False)
    p_quick.add_argument("--workers", type=int, required=False)
    p_quick.add_argument("--enable-smtp", action="store_true")

    if len(sys.argv) == 1:
        parser.print_help()
        return

    args = parser.parse_args()
    if args.cmd == "producer":
        run_producer(args)
    elif args.cmd == "consumer":
        run_consumer(args)
    elif args.cmd == "quick":
        run_quick(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
