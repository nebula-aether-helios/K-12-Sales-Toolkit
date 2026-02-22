"""Create probe lock table if missing by invoking metadata.create_all.

Usage:
    python tools/add_probe_lock_table.py --db sqlite:///enrichment.db
"""
import argparse
from db import models


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--db', required=True)
    args = p.parse_args()
    models.create_tables(args.db)
    print('Ensured probe_locks table exists (create_all executed).')


if __name__ == '__main__':
    main()
