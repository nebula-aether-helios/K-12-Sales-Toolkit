from db.models import get_session, EnrichedProspect, EmailCandidate


def purge(db_url: str, limit: int = 10):
    session = get_session(db_url)
    prospects = session.query(EnrichedProspect).order_by(EnrichedProspect.id).limit(limit).all()
    total_deleted = 0
    for p in prospects:
        for e in list(p.emails):
            if e.status != 'validated_smtp':
                session.delete(e)
                total_deleted += 1
    session.commit()
    session.close()
    print(f"Deleted {total_deleted} non-validated candidates from first {len(prospects)} prospects")


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--db-url', required=True)
    p.add_argument('--limit', type=int, default=10)
    args = p.parse_args()
    purge(args.db_url, limit=args.limit)
