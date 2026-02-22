"""Orchestrate a full local production run without Docker or RabbitMQ.

This script starts multiple worker processes that consume from an in-memory queue,
runs WorldsRunner to enqueue adapter tasks, waits for the queue to drain, then sends
stop sentinels to workers and exits.

Usage:
    python scripts/run_local_production.py --db outputs/enrichment.db --workers 4
"""
import argparse
import time
import logging
from multiprocessing import Process

from src.worlds_runner import WorldsRunner
from src.queue import get_local_queue
from scripts.worker import main as worker_main


def run_worker_process(db_path: str):
    # Worker needs CLI argument parsing; call worker.main via subprocess-like invocation
    import sys
    sys.argv = [sys.argv[0], '--db', db_path, '--local']
    try:
        worker_main()
    except SystemExit:
        return


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', default='outputs/enrichment.db')
    parser.add_argument('--workers', type=int, default=2)
    parser.add_argument('--start_phase', type=int, default=1)
    parser.add_argument('--end_phase', type=int, default=4)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    q = get_local_queue()

    # spawn workers
    procs = []
    for i in range(args.workers):
        p = Process(target=run_worker_process, args=(args.db,))
        p.start()
        procs.append(p)

    # run worlds runner which will enqueue tasks into local queue
    runner = WorldsRunner(db_path=args.db, batch_size=200)
    logging.info('Starting WorldsRunner phases %d..%d', args.start_phase, args.end_phase)
    runner.run_all(start_phase=args.start_phase, end_phase=args.end_phase, dry_run=False)

    # wait for queue to drain
    logging.info('Waiting for queue to drain...')
    while True:
        try:
            # Manager.Queue has qsize() on many platforms; fallback to timeout get
            if q.empty():
                break
        except Exception:
            # fallback: try to get with timeout to check emptiness
            try:
                item = q.get(timeout=1)
                if item is None:
                    # sentinel put accidentally; continue
                    continue
                # put back for workers
                q.put(item)
            except Exception:
                break
        time.sleep(0.5)

    logging.info('Queue drained; sending stop sentinels to workers')
    for _ in procs:
        q.put(None)

    # wait for workers to exit
    for p in procs:
        p.join(timeout=30)
        if p.is_alive():
            logging.warning('Worker %s did not exit in time; terminating', p.pid)
            p.terminate()

    logging.info('Local production run complete')


if __name__ == '__main__':
    main()
