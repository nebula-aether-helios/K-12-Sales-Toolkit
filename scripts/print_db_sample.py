import sqlite3, json, sys
p = 'outputs/ferengi_enrichment.db'
try:
    conn = sqlite3.connect(p)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    # list tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cur.fetchall()]
    print(json.dumps({'db_path': p, 'tables': tables}, indent=2))
    # count contractors
    if 'contractors' in tables:
        cur.execute('SELECT COUNT(*) as cnt FROM contractors')
        print('contractors_count:', cur.fetchone()['cnt'])
        cur.execute("SELECT * FROM contractors LIMIT 5")
        rows = [dict(r) for r in cur.fetchall()]
        # truncate long fields
        for r in rows:
            for k,v in r.items():
                if isinstance(v, str) and len(v) > 200:
                    r[k] = v[:200] + '...'
        print(json.dumps({'sample_rows': rows}, indent=2))
    else:
        print('No contractors table found')
    conn.close()
except Exception as e:
    print('ERROR', str(e))
    sys.exit(2)
