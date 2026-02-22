import argparse
import sys
from pathlib import Path
from typing import Optional

# lazy import to avoid heavy dependencies at module import time


def _print_manifest_sources(manifest_slug: str, sample: int = 5):
    """Print inferred source rows for a manifest's CSV without ingesting."""
    from json import loads

    sources_dir = Path(__file__).resolve().parent / 'sources'
    manifest_path = sources_dir / f"{manifest_slug}.json"
    if not manifest_path.exists():
        # try by api_slug inside
        for p in sources_dir.glob('*.json'):
            try:
                j = loads(p.read_text(encoding='utf-8'))
                if j.get('api_slug') == manifest_slug:
                    manifest_path = p
                    break
            except Exception:
                continue
    if not manifest_path.exists():
        print(f"Manifest for '{manifest_slug}' not found", file=sys.stderr)
        return 2
    manifest = loads(manifest_path.read_text(encoding='utf-8'))
    csv_rel = manifest.get('source_csv')
    if not csv_rel:
        print("Manifest does not reference a CSV (no 'source_csv' field)")
        return 3

    repo_root = Path(__file__).resolve().parent.parent
    csv_path = (repo_root / csv_rel).resolve()
    if not csv_path.exists():
        print(f"CSV not found at {csv_path}", file=sys.stderr)
        return 4

    print(f"Sampling up to {sample} rows from: {csv_path}")
    count = 0
    from . import ingest
    for source, sid in ingest.seed_from_csv(str(csv_path)):
        print(f"{source}: {sid}")
        count += 1
        if count >= sample:
            break
    if count == 0:
        print("No rows inferred from CSV")
    return 0


def _run_manifest_ingest(manifest_slug: str, dry_run: bool = False):
    if dry_run:
        return _print_manifest_sources(manifest_slug, sample=10)
    from . import ingest
    ok = ingest.ingest_sources_from_manifest_slug(manifest_slug)
    if ok:
        print(f"Ingestion scheduled/completed for manifest: {manifest_slug}")
        return 0
    print(f"Manifest processed but nothing ingested for: {manifest_slug}")
    return 0


def main(argv: Optional[list] = None):
    p = argparse.ArgumentParser(prog='catalog-cli', description='Catalog API local CLI tools')
    sub = p.add_subparsers(dest='cmd')

    en = sub.add_parser('enumerate-manifest', help='Enumerate and optionally ingest a manifest by slug')
    en.add_argument('--slug', required=True, help='Manifest slug or api_slug')
    en.add_argument('--dry-run', action='store_true', help='Do not write to DB; just sample CSV rows')

    sa = sub.add_parser('sample-csv', help='Sample a CSV directly')
    sa.add_argument('--csv', required=True, help='Path to CSV file (relative to repo root or absolute)')
    sa.add_argument('--n', type=int, default=5, help='Number of sample rows')

    args = p.parse_args(argv)
    if args.cmd == 'enumerate-manifest':
        return _run_manifest_ingest(args.slug, dry_run=args.dry_run)
    if args.cmd == 'sample-csv':
        repo_root = Path(__file__).resolve().parent.parent
        csv_path = Path(args.csv)
        if not csv_path.is_absolute():
            csv_path = (repo_root / csv_path).resolve()
        if not csv_path.exists():
            print(f"CSV not found: {csv_path}", file=sys.stderr)
            return 2
        print(f"Sampling up to {args.n} rows from: {csv_path}")
        count = 0
        from . import ingest
        for source, sid in ingest.seed_from_csv(str(csv_path)):
            print(f"{source}: {sid}")
            count += 1
            if count >= args.n:
                break
        if count == 0:
            print("No rows inferred from CSV")
        return 0

    p.print_help()
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
