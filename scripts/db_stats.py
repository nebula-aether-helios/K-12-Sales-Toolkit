import sqlite3
from pathlib import Path

DB = Path('outputs/ferengi_enrichment.db')

def main():
    if not DB.exists():
        print('Database not found:', DB)
        return
    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()
    total = cur.execute('SELECT COUNT(*) FROM contractors').fetchone()[0]
    completed = cur.execute("SELECT COUNT(*) FROM contractors WHERE enrich_status='completed'").fetchone()[0]
    errors = cur.execute("SELECT COUNT(*) FROM contractors WHERE error_message IS NOT NULL AND TRIM(error_message)!=''").fetchone()[0]
    pending = total - completed
    print(f'Total: {total}')
    print(f'Completed: {completed}')
    print(f'Pending: {pending}')
    print(f'Errors: {errors}')
    conn.close()

if __name__ == '__main__':
    main()
