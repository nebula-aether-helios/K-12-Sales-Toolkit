from db.models import get_session, EnrichedProspect


def delete_first_n(db_url: str, n: int = 10):
    session = get_session(db_url)
    ps = session.query(EnrichedProspect).order_by(EnrichedProspect.id).limit(n).all()
    count = 0
    for p in ps:
        session.delete(p)
        count += 1
    session.commit()
    session.close()
    print(f"Deleted {count} prospects")


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--db-url', required=True)
    p.add_argument('--n', type=int, default=10)
    args = p.parse_args()
    delete_first_n(args.db_url, args.n)
