"""Clear probe_locks table entries.

Usage:
    python tools/clear_probe_locks.py --db sqlite:///enrichment.db [--name replock]
"""
import argparse
from db.models import get_session, ProbeLock


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--db', required=True)
    p.add_argument('--name', required=False)
    args = p.parse_args()
    sess = get_session(args.db)
    q = sess.query(ProbeLock)
    if args.name:
        q = q.filter(ProbeLock.name == args.name)
    deleted = 0
    for r in q.all():
        sess.delete(r)
        deleted += 1
    sess.commit()
    print(f"Deleted {deleted} lock rows.")

if __name__ == '__main__':
    main()
