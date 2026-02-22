#!/usr/bin/env python3
"""Enhanced fallback heuristics for prospects with no MX.

Features:
- Multi-page scraping of common contact pages and root
- Wayback Machine snapshot scraping
- security.txt inspection
- Optional WHOIS parsing if `whois` package is installed
- Persists discovered emails back to the DB as EmailCandidate rows

Usage:
  python tools/fallback_no_mx.py --db sqlite:///enrichment.db --limit 50
"""
import argparse
import json
import re
import time
import socket
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from db.models import get_session, EnrichedProspect, EmailCandidate

EMAIL_RE = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', re.I)
CONTACT_PATHS = ['/contact', '/contact-us', '/about', '/team', '/staff', '/employees', '/company/contact']


def fetch_url(url: str, timeout: int = 8) -> str:
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(req, timeout=timeout) as resp:
            return resp.read().decode(errors='ignore')
    except (HTTPError, URLError, socket.timeout, Exception):
        return ''


def scrape_emails(html: str) -> set:
    emails = set(m.group(0) for m in EMAIL_RE.finditer(html))
    for m in re.finditer(r'href=["\']mailto:([^"\']+)["\']', html, re.I):
        emails.add(m.group(1).split('?')[0])
    return emails


def wayback_urls(domain: str, limit: int = 5) -> list:
    try:
        q = f'https://web.archive.org/cdx/search/cdx?url={domain}/*&output=json&limit={limit}'
        body = fetch_url(q)
        if not body:
            return []
        arr = json.loads(body)
        urls = []
        for entry in arr[1:]:
            if len(entry) >= 3:
                urls.append(entry[2])
        return urls
    except Exception:
        return []


def try_whois(domain: str) -> set:
    emails = set()
    try:
        import whois
        w = whois.whois(domain)
        txt = str(w)
        for e in EMAIL_RE.findall(txt):
            emails.add(e)
    except Exception:
        pass
    return emails


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--db', required=True)
    p.add_argument('--limit', type=int, default=50)
    args = p.parse_args()
    sess = get_session(args.db)

    prospects = sess.query(EnrichedProspect).filter((EnrichedProspect.dns_mx == None) | (EnrichedProspect.dns_mx == [])).order_by(EnrichedProspect.id).limit(args.limit).all()
    print(f'Found {len(prospects)} prospects without MX (limit={args.limit})')

    results = []
    for p in prospects:
        domain = p.primary_email_domain or getattr(p, 'website', '') or ''
        if not domain:
            continue
        domain = domain.strip().lower()
        if domain.startswith('http'):
            from urllib.parse import urlparse
            parsed = urlparse(domain)
            domain = parsed.hostname or domain
        if not domain:
            continue

        found = set()
        # security.txt
        sec = fetch_url(f'https://{domain}/.well-known/security.txt') or fetch_url(f'https://{domain}/security.txt')
        if sec:
            found |= scrape_emails(sec)

        # common contact pages
        for path in CONTACT_PATHS:
            html = fetch_url(f'https://{domain}{path}')
            if html:
                found |= scrape_emails(html)
            time.sleep(0.4)

        # root
        root = fetch_url(f'https://{domain}/') or fetch_url(f'http://{domain}/')
        if root:
            found |= scrape_emails(root)

        # wayback
        snaps = wayback_urls(domain, limit=5)
        for s in snaps[:5]:
            html = fetch_url(s)
            if html:
                found |= scrape_emails(html)
            time.sleep(0.3)

        # whois (if available)
        found |= try_whois(domain)

        inserted = 0
        for e in sorted(found):
            # prefer domain-matching emails or role addresses
            if '@' in e and (e.split('@', 1)[1].lower() != domain) and domain not in e:
                continue
            exists = sess.query(EmailCandidate).filter(EmailCandidate.prospect_id == p.id, EmailCandidate.email == e).one_or_none()
            if exists:
                continue
            ec = EmailCandidate(prospect_id=p.id, email=e, pattern='fallback_scrape', score='0.5', status='fallback_found', source_signals={'found_by': 'fallback_no_mx'})
            sess.add(ec)
            inserted += 1
        if inserted:
            sess.commit()
            print(f'Prospect id={p.id} ({domain}) inserted {inserted} fallback candidates')
        results.append({'prospect_id': p.id, 'domain': domain, 'found': list(sorted(found)), 'inserted': inserted})

    out_path = 'outputs/fallback_no_mx.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print('Wrote', out_path)


if __name__ == '__main__':
    main()
