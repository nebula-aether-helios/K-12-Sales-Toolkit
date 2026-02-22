"""Full DB Enrich CLI — presents ASCII intro, runs the full enrichment workflow
according to the plan file (manifest) and prints final metrics.

This script is the user-facing entrypoint for the enrichment workflow. It can be
packaged later into a binary (PyInstaller, etc.).
"""
import argparse
import time
import logging
from pathlib import Path

from src.utils.secrets import load_env_file
from src.worlds_runner import WorldsRunner, load_manifest_phases
from src.queue import get_local_queue
import threading
import sqlite3
import json
import datetime
import os


def run_worker_process(db_path: str):
    """Module-level worker entry so multiprocessing can spawn on Windows.

    It invokes the worker CLI (`scripts.worker`) in local-queue mode.
    """
    # import inside function to keep top-level imports minimal
    from scripts.worker import main as worker_main
    import sys
    sys.argv = [sys.argv[0], '--db', db_path, '--local']
    try:
        worker_main()
    except SystemExit:
        return


ASCII_LOGO = r'''
💰💰 ███████╗██╗   ██╗██╗     ██╗         ██████╗ ██████╗     ███████╗███╗   ██╗██████╗ ██╗ ██████╗██╗  ██╗
💰💰 ██╔════╝██║   ██║██║     ██║         ██╔══██╗██╔══██╗    ██╔════╝████╗  ██║██╔══██╗██║██╔════╝██║  ██║
💰💰 █████╗  ██║   ██║██║     ██║         ██║  ██║██████╔╝    █████╗  ██╔██╗ ██║██████╔╝██║██║     ███████║
💰💰 ██╔══╝  ██║   ██║██║     ██║         ██║  ██║██╔══██╗    ██╔══╝  ██║╚██╗██║██╔══██╗██║██║     ██╔══██║
💰💰 ██║     ╚██████╔╝███████╗███████╗    ██████╔╝██████╔╝    ███████╗██║ ╚████║██║  ██║██║╚██████╗██║  ██║
💰💰 ╚═╝      ╚═════╝ ╚══════╝╚══════╝    ╚═════╝ ╚═════╝     ╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝ ╚═════╝╚═╝  ╚═╝
                                                                                                              
💰 FULL DATABASE ENRICHMENT - COMPREHENSIVE RUN 💰
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', default='outputs/enrichment.db')
    parser.add_argument('--plan', default='catalog_api/sources/PLAN')
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--local-queue', action='store_true', default=True)
    args = parser.parse_args()

    print(ASCII_LOGO)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

    # safe load .env (without overwriting existing env)
    load_env_file()

    plan_path = Path(args.plan)
    phases = load_manifest_phases(plan_path) if plan_path.exists() else {}

    runner = WorldsRunner(db_path=args.db, batch_size=200)

    start = time.time()
    logging.info('Starting Full DB Enrich run; plan=%s workers=%d', args.plan, args.workers)

    # start local workers if requested
    procs = []
    if args.local_queue:
        # spawn worker processes using a module-level callable (pickle-safe on Windows)
        from multiprocessing import Process
        for _ in range(args.workers):
            p = Process(target=run_worker_process, args=(args.db,))
            p.start()
            procs.append(p)

    # Dashboard thread: periodically query the DB and re-render the banner + metrics
    stop_event = threading.Event()

    def dashboard_loop(db_path: str, procs_list, stop_evt: threading.Event, refresh: float = 1.0):
        """Simple terminal dashboard: clears the screen and prints banner + live metrics.

        Uses plain ANSI clear to remain dependency-free and Windows-friendly.
        """
        def clear_screen():
            # ANSI clear screen + move to top-left
            print('\033[2J\033[H', end='')

        def fetch_metrics(conn):
            cur = conn.cursor()
            metrics = {}
            try:
                cur.execute("SELECT COUNT(*) FROM contractors")
                metrics['contractors'] = cur.fetchone()[0]
            except Exception:
                metrics['contractors'] = 0
            try:
                cur.execute("SELECT COUNT(*) FROM enrichment_results")
                metrics['results'] = cur.fetchone()[0]
            except Exception:
                metrics['results'] = 0
            try:
                cur.execute("SELECT source, COUNT(*) as ct FROM enrichment_results GROUP BY source ORDER BY ct DESC")
                metrics['by_source'] = cur.fetchall()
            except Exception:
                metrics['by_source'] = []
            try:
                cur.execute("SELECT source, status, success_ct, error_ct, avg_ms, checked_at FROM source_health ORDER BY checked_at DESC")
                metrics['health'] = cur.fetchall()
            except Exception:
                metrics['health'] = []
            try:
                cur.execute("SELECT e.id, e.contractor_id, c.license_number, c.business_name, e.source, e.success, e.error, e.fetched_at FROM enrichment_results e JOIN contractors c ON e.contractor_id = c.id ORDER BY e.fetched_at DESC LIMIT 5")
                metrics['recent'] = cur.fetchall()
            except Exception:
                metrics['recent'] = []
            return metrics

        # Open a persistent sqlite connection for light-weight polling
        conn = None
        try:
            conn = sqlite3.connect(db_path, check_same_thread=False)
        except Exception:
            conn = None

        while not stop_evt.is_set():
            try:
                clear_screen()
                print(ASCII_LOGO)
                now = datetime.datetime.datetime.utcnow() if hasattr(datetime, 'datetime') else datetime.datetime.utcnow()
                print(f"Run started: {now.isoformat()}  (db={db_path})")

                # worker statuses
                print('\nWorkers:')
                for i, p in enumerate(procs_list):
                    status = 'alive' if p.is_alive() else 'stopped'
                    print(f"  worker[{i}] pid={getattr(p, 'pid', 'N/A')} status={status}")

                # queue size (best-effort)
                try:
                    q = get_local_queue()
                    qsize = None
                    try:
                        qsize = q.qsize()
                    except Exception:
                        qsize = 'N/A'
                    print(f"\nQueue size: {qsize}")
                except Exception:
                    print("\nQueue: not enabled")

                # DB metrics
                if conn:
                    metrics = fetch_metrics(conn)
                    print(f"\nContractors: {metrics.get('contractors', 0)}  |  Enrichment results: {metrics.get('results', 0)}")
                    print('\nBy source:')
                    for src, ct in metrics.get('by_source', []):
                        print(f"  {src}: {ct}")

                    print('\nSource health (most recent):')
                    for row in metrics.get('health', []):
                        src, status, suc, err, avg, checked = row
                        print(f"  {src}: status={status} success={suc} errors={err} avg_ms={avg} at={checked}")

                    print('\nRecent enrichment results (latest 5):')
                    for r in metrics.get('recent', []):
                        _id, contractor_id, license_num, biz, source, success, error, fetched_at = r
                        s = 'OK' if success else 'ERR'
                        print(f"  [{s}] id={_id} contractor={license_num or contractor_id} source={source} biz='{(biz or '')[:30]}' at={fetched_at} error={error or ''}")
                else:
                    print('\nDB not available yet')

                # flush and sleep
                try:
                    import sys
                    sys.stdout.flush()
                except Exception:
                    pass
                stop_evt.wait(refresh)
            except Exception:
                # protect dashboard from crashing
                import traceback
                traceback.print_exc()
                stop_evt.wait(refresh)
        if conn:
            try:
                conn.close()
            except Exception:
                pass

    # start dashboard thread
    dash_thread = threading.Thread(target=dashboard_loop, args=(args.db, procs, stop_event, 1.0), daemon=True)
    dash_thread.start()

    # run all phases using runner (this will enqueue tasks for long-running adapters)
    results = runner.run_all(start_phase=1, end_phase=4, dry_run=False)

    duration = time.time() - start
    logging.info('Full DB Enrich completed in %.2fs', duration)

    # stop dashboard
    stop_event.set()
    if 'dash_thread' in locals():
        dash_thread.join(timeout=5)

    # summary
    print('\n=== Run summary ===')
    for r in results:
        print(f"Phase {r['phase']}: processed={r.get('processed')} errors={r.get('errors')} duration_s={r.get('duration_s'):.2f}")

    # stop local workers
    if args.local_queue and procs:
        q = get_local_queue()
        for _ in procs:
            q.put(None)
        for p in procs:
            p.join(timeout=30)
            if p.is_alive():
                p.terminate()

    print('\nFull DB Enrich finished — results stored in', args.db)


if __name__ == '__main__':
    main()
