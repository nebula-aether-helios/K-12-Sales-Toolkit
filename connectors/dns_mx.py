import dns.resolver
import socket
from typing import List, Dict


def lookup_mx(domain: str, timeout: int = 5) -> Dict:
    """Lookup MX records and basic footprint for a domain."""
    try:
        answers = dns.resolver.resolve(domain, 'MX', lifetime=timeout)
        mxs = []
        for r in answers:
            mxs.append(str(r.exchange).rstrip('.'))
        # also try A lookup for footprint
        try:
            a = socket.gethostbyname(domain)
        except Exception:
            a = None
        return {"mx_records": mxs, "a_record": a}
    except Exception as e:
        return {"error": str(e)}
