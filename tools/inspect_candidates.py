from db.models import get_session, EnrichedProspect


def main(db_url: str, limit: int = 10):
    session = get_session(db_url)
    prospects = session.query(EnrichedProspect).order_by(EnrichedProspect.id).limit(limit).all()
    for p in prospects:
        print(f"Prospect id={p.id} source_row={p.source_row_id} domain={p.primary_email_domain} dns_mx={bool(p.dns_mx)}")
        for e in p.emails:
            print(f"  - {e.email} status={e.status} score={e.score} signals={e.source_signals}")
    session.close()


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--db-url', required=True)
    p.add_argument('--limit', type=int, default=10)
    args = p.parse_args()
    main(args.db_url, args.limit)
