#!/usr/bin/env python3
"""Show a live dashboard by reading outputs/ferengi_progress.json and regenerating ASCII landscape.
Does NOT start the controller; safe to run alongside an existing run.
"""
import time
import json
import argparse
from pathlib import Path


def render_mini_3d(a, b, c, width=36, height=8):
    mx = max(a, b, c, 1)
    cols = 3
    col_w = width // cols
    chars = [' ', '.', ':', '-', '=', '+', '*', '#', '%', '@']
    out_lines = ['' for _ in range(height)]
    for i, val in enumerate((a, b, c)):
        h = int((val / mx) * height)
        for row in range(height):
            level = height - row
            ch = chars[min(len(chars)-1, max(0, int((level/height)*(len(chars)-1))))]
            if level <= h:
                out_lines[row] += ch * col_w
            else:
                out_lines[row] += ' ' * col_w
    return '\n'.join(out_lines)


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
    parser.add_argument('--db', default='outputs/ferengi_enrichment.db')
    parser.add_argument('--interval', type=int, default=60, help='Seconds between refreshes')
    parser.add_argument('--grid', default='120x40', help='Grid size, e.g. 120x40')
    parser.add_argument('--metric', default=None, help='Metric to visualize')
    args = parser.parse_args()

    progress_path = Path('outputs') / 'ferengi_progress.json'
    db_path = args.db

    print(f"Starting live dashboard (no controller) — polling {progress_path} every {args.interval}s")
    try:
        while True:
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
                workers = sj.get('workers', 0)
                pct = (enriched / total * 100.0) if total else 0.0
                bar_len = 60
                filled = int(bar_len * pct / 100.0)
                bar = '[' + '#' * filled + '-' * (bar_len - filled) + ']' + f' {pct:.2f}%'
                print('FERENGI LIVE DASHBOARD (viewer only)')
                print(bar)
                print(f'Prospects: {enriched}/{total}  API calls: {api_calls}  Errors: {errors}  Workers: {workers}')
                print(render_mini_3d(workers, api_calls, errors, width=36, height=8))
            else:
                print('No progress snapshot yet; waiting...')

            # regenerate landscape for live view
            try:
                generate_landscape(db_path, args.metric, args.grid)
            except Exception as e:
                print('viewer: failed to regenerate landscape:', e)

            time.sleep(args.interval)
    except KeyboardInterrupt:
        print('\nExiting live dashboard.')


if __name__ == '__main__':
    main()
