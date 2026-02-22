"""CLI to run Mario Worlds phased enrichment runner."""
import argparse
from pathlib import Path
from src.worlds_runner import WorldsRunner


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="./outputs/enrichment.db")
    parser.add_argument("--phase", type=int, help="Run single phase (1-4)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    db_path = args.db
    runner = WorldsRunner(db_path, batch_size=100)
    if args.phase:
        res = runner.run_phase(args.phase, dry_run=args.dry_run)
        print(res)
    else:
        res = runner.run_all(dry_run=args.dry_run)
        for r in res:
            print(r)


if __name__ == "__main__":
    main()
