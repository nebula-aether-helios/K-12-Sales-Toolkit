"""Generate a markdown file summarizing each EnrichedProspect row:
- company/business name (from primary_email_domain or source_row_id)
- owners name (best-effort from pattern or source_signals)
- personnel names (best-effort from emails local-parts)
- insurance/wc company (best-effort from source_signals or fallback)

Also include per-row analysis: counts of emails, validated_smtp, invalid, no_mx, phones.
"""
from db.models import get_session, EnrichedProspect
import json
import os
import csv

OUT = os.path.join(os.getcwd(), 'outputs', 'row_analysis.md')
CSV_PATH = os.path.join(os.getcwd(), 'outputs', 'sacramento_contractors_cslb_sac_osint.csv')

s = get_session('sqlite:///enrichment.db')
prospects = s.query(EnrichedProspect).order_by(EnrichedProspect.id).all()

# Load source CSV (if present) to enrich owner/insurance extraction without modifying DB schema
csv_rows = []
csv_header = []
if os.path.exists(CSV_PATH):
    try:
        with open(CSV_PATH, newline='', encoding='utf-8') as fh:
            reader = csv.DictReader(fh)
            csv_header = reader.fieldnames or []
            for r in reader:
                csv_rows.append(r)
    except Exception:
        csv_rows = []

lines = []
lines.append('# Row-level Contact & Probe Analysis\n')
lines.append('Generated from `enrichment.db` — per-row summary of company, owners, personnel, and insurance/WC hints.\n')
lines.append('|id|source_row|company|owners (best-effort)|personnel (best-effort)|insurance/wc (best-effort)|emails_count|validated_smtp|invalid_smtp|no_mx|phones_count|notes|')
lines.append('|--:|--|--|--|--|--|--:|--:|--:|--:|--:|--|')

for p in prospects:
    company = p.primary_email_domain or (getattr(p, 'source_row_id', '') or '')
    # owners: try CSV mapping first, then prospect.source_signals
    owners = ''
    personnel = []
    insurance = ''
    emails_count = len(p.emails or [])
    phones_count = len(p.phones or [])
    validated = 0
    invalid = 0
    no_mx = 0
    for c in p.emails:
        try:
            sig = c.source_signals or {}
            st = sig.get('smtp_details', {}) if isinstance(sig, dict) else {}
            status = st.get('status') if isinstance(st, dict) else None
        except Exception:
            status = None
        if status == 'valid':
            validated += 1
        elif status == 'invalid':
            invalid += 1
        elif status == 'unknown':
            no_mx += 1
        # personnel: extract name-like local parts
        local = c.email.split('@', 1)[0] if c.email and '@' in c.email else ''
        # heuristics: split on dot, underscore, hyphen
        parts = [p.strip() for p in local.replace('_', '.').replace('-', '.').split('.') if p.strip()]
        if len(parts) >= 2:
            personnel.append(' '.join([parts[0].capitalize(), parts[1].capitalize()]))
        elif parts:
            personnel.append(parts[0].capitalize())
    personnel = ', '.join(list(dict.fromkeys(personnel))[:6])

    # owners and insurance: try to find hints in prospect.source_row (if stored in dns or notes)
    # Try to enrich from original CSV: many imports store source row index in p.source_row_id
    if csv_rows and p.source_row_id:
        try:
            idx = int(p.source_row_id) - 1
            if 0 <= idx < len(csv_rows):
                row = csv_rows[idx]
                # CSV columns observed: 'business_name', 'contact_name', 'wc_insurance_company', 'wc_policy_number'
                owners = owners or (row.get('contact_name') or '').strip()
                insurance = insurance or (row.get('wc_insurance_company') or '').strip()
        except Exception:
            pass

    # Fallback: some prospects may have a source_row JSON attached in DB (rare)
    try:
        sr = getattr(p, 'source_row', None)
        if isinstance(sr, dict):
            owners = owners or sr.get('owner') or sr.get('owners') or ''
            insurance = insurance or sr.get('insurance') or sr.get('wc_insurance') or ''
    except Exception:
        pass

    # Fallback: attempt to look inside any email candidate source_signals for 'whois' or 'wayback' hints
    if not insurance:
        for c in p.emails:
            ss = c.source_signals or {}
            if isinstance(ss, dict):
                # look for fallback results
                fb = ss.get('fallback') or ss.get('wayback') or ss.get('whois')
                if isinstance(fb, dict):
                    ins = fb.get('insurance') or fb.get('wc')
                    if ins:
                        insurance = ins
                        break
    notes = ''
    lines.append(f'|{p.id}|{p.source_row_id or ""}|{company}|{owners}|{personnel}|{insurance}|{emails_count}|{validated}|{invalid}|{no_mx}|{phones_count}|{notes}|')

# Add per-provider summary (quick stats)
from db.models import ProviderMetric
rows = s.query(ProviderMetric).order_by(ProviderMetric.probes.desc()).all()
lines.append('\n\n## Provider Metrics Summary\n')
lines.append('|provider|probes|valid|invalid|codes_count|')
lines.append('|--|--:|--:|--:|--:|')
for r in rows:
    codes_count = len(r.codes or {})
    lines.append(f'|{r.provider}|{r.probes}|{r.valid}|{r.invalid}|{codes_count}|')

with open(OUT, 'w', encoding='utf-8') as fh:
    fh.write('\n'.join(lines))

print('Wrote', OUT)
