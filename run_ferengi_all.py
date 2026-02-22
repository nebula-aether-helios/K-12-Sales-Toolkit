#!/usr/bin/env python3
"""Wrapper: one-command to rule them all for Ferengi enrichment

Behavior:
- Reads secrets from OS env or .env (python-dotenv) if present
- Validates required env vars (placeholders listed in .env.template)
- Optionally seeds DB, runs controller, and generates ASCII landscapes
- Does NOT write secrets to logs or files
"""
import os
import sys
import argparse
import subprocess
from pathlib import Path
from dotenv import load_dotenv
import time

# load local .env if present
env_path = Path('.') / '.env'
env_int = Path('.') / 'env.int'
# If an env.int file exists (provided by user), and no .env is present, import it into .env
if env_int.exists() and not env_path.exists():
    try:
        print('Found env.int - importing into .env')
        lines = env_int.read_text(encoding='utf-8', errors='ignore').splitlines()
        out_lines = []
        for l in lines:
            l = l.strip()
            if not l or l.startswith('#'):
                continue
            # accept KEY=VALUE or export KEY=VALUE
            if l.startswith('export '):
                l = l[len('export '):]
            out_lines.append(l)
        if out_lines:
            env_path.write_text('\n'.join(out_lines) + '\n', encoding='utf-8')
            print('.env created from env.int (safely)')
    except Exception as e:
        print('Failed to import env.int:', e)

if env_path.exists():
    load_dotenv(dotenv_path=env_path)

REQUIRED_SECRETS = [
    'FERENGI_DB',
    # add other keys only if you plan to use distributed or API calls
]


def check_required(required):
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        print("Missing required environment variables:", ", ".join(missing))
        sys.exit(2)


def run_controller(db, max_iterations, smoke, extra_args):
    cmd = [sys.executable, 'ferengi_enrichment_controller.py', '--db', db]
    if max_iterations:
        cmd += ['--max-iterations', str(max_iterations)]
    # controller does not accept a --smoke flag; emulate a smoke run by limiting iterations
    if smoke:
        cmd += ['--max-iterations', '1']
    if extra_args:
        cmd += extra_args
    print('Running controller:', ' '.join(cmd))
    res = subprocess.run(cmd)
    return res.returncode


def run_controller_async(db, max_iterations, smoke, extra_args):
    cmd = [sys.executable, 'ferengi_enrichment_controller.py', '--db', db]
    if max_iterations:
        cmd += ['--max-iterations', str(max_iterations)]
    if smoke:
        cmd += ['--max-iterations', '1']
    if extra_args:
        cmd += extra_args
    print('Starting controller (background):', ' '.join(cmd))
    p = subprocess.Popen(cmd)
    return p


def generate_landscape(db, metric, grid):
    try:
        from visualizations.ascii_landscape import render_from_db
        grid_size = None
        if grid:
            parts = grid.lower().split('x')
            if len(parts) == 2:
                grid_size = (int(parts[0]), int(parts[1]))
        render_from_db(db, metric_fields=[metric] if metric else [], grid_size=grid_size)
    except Exception as e:
        print('Failed to generate landscape:', e)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', default=os.environ.get('FERENGI_DB', 'outputs/ferengi_enrichment.db'))
    parser.add_argument('--max-iterations', type=int, default=None)
    parser.add_argument('--smoke', action='store_true', help='Run a quick smoke pass')
    parser.add_argument('--seed', action='store_true', help='Seed DB if missing using existing scripts')
    parser.add_argument('--metric', default=None, help='Metric field to visualize (e.g., profit_score)')
    parser.add_argument('--grid', default=None, help='Grid size, e.g. 80x24')
    parser.add_argument('--monitor', action='store_true', help='Tail logs and periodically regenerate ASCII landscape')
    parser.add_argument('--monitor-interval', type=int, default=5, help='Seconds between landscape refreshes when monitoring')
    parser.add_argument('--monitor-grid', default='120x40', help='Grid size used by monitor (e.g. 120x40)')
    parser.add_argument('--live', action='store_true', help='Run controller in background and show live progress bar from progress file')
    parser.add_argument('--live-interval', type=int, default=2, help='Seconds between live dashboard refreshes')
    parser.add_argument('extra', nargs=argparse.REMAINDER)
    args = parser.parse_args()

    db_path = Path(args.db)
    # check required envs minimally
    check_required(REQUIRED_SECRETS)

    if args.seed and not db_path.exists():
        print('Seeding DB...')
        # try to call create_sample_ferengi_db.py if present
        seed_script = Path('create_sample_ferengi_db.py')
        if seed_script.exists():
            subprocess.run([sys.executable, str(seed_script)])
        else:
            print('No seeder script found; please run import_contractors_csv.py manually')

    # ensure outputs exists
    Path('outputs').mkdir(parents=True, exist_ok=True)

    code = run_controller(str(db_path), args.max_iterations, args.smoke, args.extra)

    # generate ascii landscape snapshot (normal run)
    try:
        generate_landscape(str(db_path), args.metric, args.grid)
    except Exception:
        pass

    # monitoring mode: tail log and regenerate landscape periodically
    if args.monitor:
        log_path = Path('outputs') / 'ferengi_enrichment.log'
        print(f"Entering monitor mode: tailing {log_path} and refreshing landscape every {args.monitor_interval}s")
        # spawn controller as background process if not already running (we used run_controller)
        # If controller already finished (code returned), still allow one refresh
        # Tail the log file
        try:
            # open log and seek to end
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as fh:
                fh.seek(0, 2)
                start_time = time.time()
                # if controller still running, wait and poll file; otherwise do one pass
                while True:
                    line = fh.readline()
                    while line:
                        print(line.rstrip())
                        line = fh.readline()
                    # regenerate landscape
                    try:
                        grid = args.monitor_grid
                        generate_landscape(str(db_path), args.metric, grid)
                    except Exception as e:
                        print('monitor: failed to regenerate landscape:', e)
                    # break if controller finished
                    if code is not None:
                        # we executed run_controller via subprocess.run so controller already finished
                        break
                    time.sleep(args.monitor_interval)
        except FileNotFoundError:
            print('monitor: log file not found:', log_path)

    if args.live:
        # run controller in background and display live dashboard based on progress JSON
        proc = run_controller_async(str(db_path), args.max_iterations, args.smoke, args.extra)
        progress_path = Path('outputs') / 'ferengi_progress.json'
        try:
            while True:
                # read progress
                if progress_path.exists():
                    try:
                        sj = json.loads(progress_path.read_text(encoding='utf-8'))
                    except Exception:
                        sj = None
                else:
                    sj = None

                # clear screen
                print('\x1b[2J\x1b[H', end='')
                if sj:
                    total = sj.get('total_prospects', 0)
                    enriched = sj.get('enriched_count', 0)
                    api_calls = sj.get('api_calls', 0)
                    errors = sj.get('errors', 0)
                    workers = sj.get('workers', args.monitor_grid)
                    pct = (enriched / total * 100.0) if total else 0.0
                    bar_len = 60
                    filled = int(bar_len * pct / 100.0)
                    bar = '[' + '#' * filled + '-' * (bar_len - filled) + ']' + f' {pct:.2f}%'
                    print('FERENGI LIVE DASHBOARD')
                    print(bar)
                    print(f'Prospects: {enriched}/{total}  API calls: {api_calls}  Errors: {errors}  Workers: {workers}')
                    # mini 3D ASCII bars for workers / api_calls / errors
                    def render_mini_3d(a, b, c, width=36, height=8):
                        # scale values relative to max among them
                        mx = max(a, b, c, 1)
                        cols = 3
                        col_w = width // cols
                        chars = [' ', '.', ':', '-', '=', '+', '*', '#', '%', '@']
                        out_lines = ['' for _ in range(height)]
                        for i, val in enumerate((a, b, c)):
                            h = int((val / mx) * height)
                            for row in range(height):
                                # from top (height-1) to 0
                                level = height - row
                                ch = chars[min(len(chars)-1, max(0, int((level/height)*(len(chars)-1))))]
                                if level <= h:
                                    out_lines[row] += ch * col_w
                                else:
                                    out_lines[row] += ' ' * col_w
                        return '\n'.join(out_lines)

                    print(render_mini_3d(workers, api_calls, errors, width=36, height=8))
                else:
                    print('No progress snapshot yet; waiting...')

                # regenerate landscape for live view
                try:
                    generate_landscape(str(db_path), args.metric, args.monitor_grid)
                except Exception as e:
                    print('live: failed to regenerate landscape:', e)

                # break if process ended and final snapshot indicates final
                if proc.poll() is not None:
                    # process ended; show final snapshot then exit
                    if progress_path.exists():
                        try:
                            sj = json.loads(progress_path.read_text(encoding='utf-8'))
                            if sj.get('final'):
                                print('\nController finished and final snapshot present. Exiting live dashboard.')
                                break
                        except Exception:
                            pass
                    print('\nController finished; exiting live dashboard.')
                    break

                time.sleep(args.live_interval)
        finally:
            try:
                if proc.poll() is None:
                    proc.terminate()
            except Exception:
                pass

    sys.exit(code)


if __name__ == '__main__':
    main()
