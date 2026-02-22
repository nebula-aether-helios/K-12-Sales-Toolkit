import socket
from typing import Dict, List, Tuple

# Try to import dnspython; if not available, provide safe fallbacks so the
# rest of the enrichment pipeline can run without failing imports.
try:
    import dns.resolver
    import dns.exception
    DNS_AVAILABLE = True
except Exception:
    DNS_AVAILABLE = False


def get_dns_records(domain: str, timeout: int = 8) -> Dict[str, object]:
    """Return DNS footprint for domain: A, AAAA, MX, TXT, NS.

    If dnspython is not installed, returns empty structures so callers can
    still proceed (DNS signals will be missing).
    """
    result = {"a": [], "aaaa": [], "mx": [], "txt": [], "ns": []}
    if not domain:
        return result
    if not DNS_AVAILABLE:
        # no dnspython available; return empty results
        return result

    resolver = dns.resolver.Resolver()
    resolver.timeout = timeout
    resolver.lifetime = timeout
    try:
        answers = resolver.resolve(domain, "A")
        for r in answers:
            result["a"].append(r.to_text())
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.Timeout):
        pass

    try:
        answers = resolver.resolve(domain, "AAAA")
        for r in answers:
            result["aaaa"].append(r.to_text())
    except Exception:
        pass

    try:
        answers = resolver.resolve(domain, "MX")
        for r in answers:
            result["mx"].append((int(r.preference), str(r.exchange).rstrip('.')))
        result["mx"].sort(key=lambda x: x[0])
    except Exception:
        pass

    try:
        answers = resolver.resolve(domain, "TXT")
        for r in answers:
            txt = b"".join(r.strings).decode(errors="ignore") if hasattr(r, 'strings') else r.to_text()
            result["txt"].append(txt)
    except Exception:
        pass

    try:
        answers = resolver.resolve(domain, "NS")
        for r in answers:
            result["ns"].append(str(r.target).rstrip('.'))
    except Exception:
        pass

    return result


def parse_spf(txt_records: List[str]) -> Dict[str, object]:
    """Detect SPF present and collect include: domains.

    Lightweight parser: looks for 'v=spf1' and 'include:' tokens.
    """
    has_spf = False
    includes: List[str] = []
    for t in txt_records or []:
        low = t.lower()
        if "v=spf1" in low:
            has_spf = True
            parts = low.split()
            for p in parts:
                if p.startswith("include:"):
                    includes.append(p.split(":", 1)[1])
    return {"has_spf": has_spf, "includes": includes}


def mx_provider_from_hostname(hostname: str) -> str:
    """Infer common provider labels from MX hostname heuristics."""
    if not hostname:
        return ""
    h = hostname.lower()
    if "google.com" in h or "googlemail.com" in h or "googlehosted" in h:
        return "Google Workspace"
    if "mail.protection.outlook" in h or "outlook.com" in h or "office365" in h or "outlook" in h:
        return "Microsoft 365"
    if "zoho" in h:
        return "Zoho"
    if "sendgrid" in h:
        return "SendGrid"
    if "messagingengine" in h or "fastmail" in h:
        return "FastMail"
    if "amazonses" in h or "amazonaws.com" in h or h.endswith("amazonses.com"):
        return "Amazon SES"
    if "mailgun" in h:
        return "Mailgun"
    if "godaddy" in h or "secureserver" in h:
        return "GoDaddy"
    parts = h.split('.')
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return hostname


def is_valid_hostname(hostname: str) -> bool:
    """Basic hostname validation.

    Rules:
    - must be a non-empty string
    - allowed chars: a-zA-Z0-9.-
    - must contain at least one dot
    - labels must not start or end with '-' and must be 1-63 chars
    - overall length <= 255
    """
    if not hostname or not isinstance(hostname, str):
        return False
    hn = hostname.strip().rstrip('.')
    if len(hn) == 0 or len(hn) > 255:
        return False
    if '.' not in hn:
        return False
    import re
    if not re.match(r'^[A-Za-z0-9.-]+$', hn):
        return False
    parts = hn.split('.')
    for label in parts:
        if len(label) == 0 or len(label) > 63:
            return False
        if label.startswith('-') or label.endswith('-'):
            return False
    return True


def normalize_domain(raw: str) -> str:
    """Normalize a raw domain or website string to a usable hostname.

    - strips scheme and path
    - lowercases
    - if an email-like string is provided, returns domain part
    - if no TLD present, appends .com (best-effort)
    """
    if not raw:
        return ""
    from urllib.parse import urlparse

    s = str(raw).strip()
    # if looks like an email, extract domain
    if "@" in s and not s.startswith("http"):
        try:
            return s.split("@", 1)[1].lower()
        except Exception:
            pass

    # parse URL to extract hostname
    parsed = urlparse(s)
    host = parsed.hostname or s
    # remove port
    if ":" in host:
        host = host.split(":")[0]
    host = host.strip().lower()
    # if there are spaces, replace with hyphen
    host = host.replace(' ', '-')
    # if missing a dot (no TLD), append .com
    if '.' not in host:
        host = host + '.com'
    return host
