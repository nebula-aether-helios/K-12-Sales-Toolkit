import re
from typing import List, Dict, Tuple
import socket
import smtplib
import uuid
import time
from typing import Optional

COMMON_PATTERNS = [
    "{first}.{last}",
    "{first}{last}",
    "{f}{last}",
    "{first}{l}",
    "{first}",
    "{last}",
    "{first}_{last}",
    "{first}-{last}",
    "{first}.{l}",
    "{f}.{last}",
    "{last}{first}",
    "{l}{first}",
]


def normalize_token(s: str) -> str:
    s = s or ""
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9._-]", "", s)
    return s


def generate_email_candidates(first: str, last: str, domain: str, extra_locales: List[str] = None) -> List[str]:
    """Generate common email address local-parts for a name and return full addresses.

    returns up to len(COMMON_PATTERNS) candidates.
    """
    first_n = normalize_token(first or "")
    last_n = normalize_token(last or "")
    f = first_n[:1] if first_n else ""
    l = last_n[:1] if last_n else ""
    locals_ = []
    for p in COMMON_PATTERNS:
        local = p.format(first=first_n, last=last_n, f=f, l=l)
        local = re.sub(r"\.+", ".", local).strip('.')
        if local and local not in locals_:
            locals_.append(local)
    # role addresses
    for role in ["info", "office", "admin", "contact", "support", "hello"]:
        if role not in locals_:
            locals_.append(role)

    # normalize domain to a usable hostname
    try:
        from connectors.dns_helpers import normalize_domain
        domain_norm = normalize_domain(domain) if domain else ''
    except Exception:
        domain_norm = (domain or '').lower()

    emails = [f"{loc}@{domain_norm}" for loc in locals_ if domain_norm]
    return emails


def _check_github_username(username: str, timeout: int = 5) -> bool:
    """Check whether a GitHub profile exists for username (simple HEAD request).

    Uses urllib to avoid adding requests as a hard dependency.
    """
    if not username:
        return False
    try:
        from urllib.request import Request, urlopen
        req = Request(f"https://github.com/{username}", method='HEAD')
        resp = urlopen(req, timeout=timeout)
        return resp.status == 200
    except Exception:
        return False


def enumerate_usernames(first: str, last: str, max_checks: int = 12) -> List[str]:
    """Generate likely username variants and check GitHub for existence.

    Returns a list of discovered usernames (may be empty). This is a lightweight,
    rate-limited-friendly check suitable for small batches.
    """
    first_n = normalize_token(first or "")
    last_n = normalize_token(last or "")
    f = first_n[:1] if first_n else ""
    l = last_n[:1] if last_n else ""
    variants = [
        f + last_n,
        first_n + l,
        first_n + last_n,
        first_n + '.' + last_n,
        last_n + first_n,
        last_n + '.' + first_n,
        f + '.' + last_n,
        first_n,
        last_n,
    ]
    seen = set()
    found = []
    checks = 0
    for v in variants:
        if checks >= max_checks:
            break
        if not v or v in seen:
            continue
        seen.add(v)
        checks += 1
        if _check_github_username(v):
            found.append(v)
    return found


def hypothesize_from_usernames(usernames: List[str], domain: str, max_per_user: int = 3) -> List[str]:
    """Build email hypotheses from known usernames.

    For each discovered username, generate a few common email forms.
    """
    res = []
    try:
        from connectors.dns_helpers import normalize_domain
        domain_norm = normalize_domain(domain) if domain else ''
    except Exception:
        domain_norm = (domain or '').lower()
    if not domain_norm:
        return res
    for u in usernames:
        # direct username@domain
        res.append(f"{u}@{domain_norm}")
        # split username into parts around separators
        parts = re.split(r'[._-]', u)
        if len(parts) >= 2:
            res.append(f"{parts[0]}.{parts[-1]}@{domain_norm}")
            res.append(f"{parts[0]}{parts[-1]}@{domain_norm}")
        if len(res) >= max_per_user * len(usernames):
            break
    # ensure uniqueness
    seen = set()
    uniq = []
    for e in res:
        if e not in seen:
            seen.add(e)
            uniq.append(e)
    return uniq


def score_candidate(email: str, provider_signals: Dict[str, object] = None, spf_includes: List[str] = None, username_hits: List[str] = None, llm_score: float = None, llm_weight: float = 0.0) -> float:
    """Heuristic scoring with optional LLM combination.

    - person-like patterns get larger boosts
    - role addresses get a small boost
    - username hits increase score
    - optional llm_score will be combined using llm_weight
    """
    score = 0.0
    local = email.split("@")[0]
    # person-like patterns
    if re.match(r"^[a-z]+\.[a-z]+$", local):
        score += 0.8
    # contiguous letters (no dot) as fallback person-like
    if re.match(r"^[a-z]+[a-z]+$", local) and "." not in local:
        score += 0.5
    # role addresses get small boost
    if local in ("info", "admin", "support", "contact", "hello", "office"):
        score += 0.02
    # provider signal hints
    if provider_signals:
        prov = provider_signals.get("provider") if isinstance(provider_signals, dict) else None
        if prov and "google" in prov.lower():
            score += 0.05
    # boost when username hits are detected
    if username_hits:
        for uh in username_hits:
            if local == uh or local.replace('.', '') == uh.replace('.', ''):
                score += 0.35
    if spf_includes:
        score += 0.02 * len(spf_includes)
    heur_score = round(min(score, 1.0), 3)
    # combine with optional LLM score
    if llm_score is not None and llm_weight and 0.0 <= llm_weight <= 1.0:
        final = (1.0 - llm_weight) * heur_score + llm_weight * float(llm_score)
        return round(min(max(final, 0.0), 1.0), 3)
    return heur_score


def choose_best_candidates(candidates: List[str], provider_signals: Dict[str, object] = None, spf_includes: List[str] = None, username_hits: List[str] = None, llm_scores: dict = None, llm_weight: float = 0.0, top_n: int = 3) -> List[Dict[str, object]]:
    scored = []
    for c in candidates:
        heur = score_candidate(c, provider_signals, spf_includes, username_hits, llm_score=None, llm_weight=0.0)
        llm_s = None
        if llm_scores and c in llm_scores:
            try:
                llm_s = float(llm_scores.get(c))
            except Exception:
                llm_s = None
        final = score_candidate(c, provider_signals, spf_includes, username_hits, llm_score=llm_s, llm_weight=llm_weight)
        scored.append({"email": c, "score": final, "heur_score": heur, "llm_score": llm_s})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_n]


def apply_acceptance_rules(candidates: List[dict], prospect_signals: dict = None, thresholds: dict = None) -> List[dict]:
    """Apply post-processing acceptance rules and mark candidates with 'accepted' flag and possibly update status.

    thresholds example: {
        'mx_high_conf': 0.75,
        'purge_no_mx_below': 0.6,
    }
    """
    if thresholds is None:
        thresholds = {'mx_high_conf': 0.75, 'purge_no_mx_below': 0.6}
    signals = prospect_signals or {}
    has_mx = bool(signals.get('dns_mx'))
    catch_all = signals.get('catch_all', False)
    for c in candidates:
        c['accepted'] = False
        reasons = []
        score = float(c.get('score') or 0.0)
        status = c.get('status', '')
        # SMTP validated always accepted
        if status == 'validated_smtp':
            c['accepted'] = True
            reasons.append('validated_smtp')
            c['final_status'] = 'validated'
            continue
        # if MX present and score >= mx_high_conf -> accept
        if has_mx and score >= thresholds.get('mx_high_conf', 0.75) and not catch_all:
            c['accepted'] = True
            reasons.append('mx_and_score')
            c['final_status'] = 'high_confidence'
            continue
        # purge low-confidence no-MX candidates
        if (not has_mx) and score < thresholds.get('purge_no_mx_below', 0.6):
            c['accepted'] = False
            reasons.append('purge_no_mx_low_score')
            c['final_status'] = 'purged'
            continue
        # otherwise keep as not accepted but not purged
        c['final_status'] = status or 'unaccepted'
        c['reasons'] = reasons
    return candidates


def smtp_probe(email: str, mx_hosts: List[Tuple[int, str]], timeout: int = 15, helo_host: str = "example.com", max_attempts_per_host: int = 2) -> Dict[str, object]:
    """Attempt SMTP RCPT probe against MX hosts. Returns status dict.

    NOTE: This performs outbound TCP connections to port 25 and may be blocked.
    Returns: {status: 'valid'|'invalid'|'unknown', details: str}
    """
    if not mx_hosts:
        return {"status": "unknown", "details": "no_mx"}
    # import provider heuristics
    try:
        from connectors.dns_helpers import mx_provider_from_hostname
    except Exception:
        def mx_provider_from_hostname(h):
            return ''

    for pref, host in mx_hosts:
        # per-host retry/backoff
        attempts = 0
        while attempts < max_attempts_per_host:
            attempts += 1
            try:
                # resolve host to an address via socket to honor system resolver
                addr_info = socket.getaddrinfo(host, 25)
            except Exception:
                # cannot resolve this host, break out for this host
                break
            try:
                s = smtplib.SMTP(host=host, port=25, timeout=timeout)
                s.set_debuglevel(0)
                s.ehlo_or_helo_if_needed()
                # use null MAIL FROM per RFC for address verification
                try:
                    code, resp = s.mail("")
                except Exception:
                    # fallback to a no-reply sender
                    try:
                        s.mail("postmaster@%s" % helo_host)
                    except Exception:
                        pass
                try:
                    code, resp = s.rcpt(email)
                    # code 250 or 251 indicate acceptance
                    if isinstance(code, int) and 200 <= code < 300:
                        s.quit()
                        return {"status": "valid", "details": f"{host}:{code}", "code": code}
                    # 4xx temporary errors -> retryable
                    if isinstance(code, int) and 400 <= code < 500:
                        # sleep then retry if attempts remain
                        try:
                            s.quit()
                        except Exception:
                            pass
                        if attempts < max_attempts_per_host:
                            time.sleep(1 * attempts)
                            continue
                        else:
                            return {"status": "unknown", "details": f"{host}:{code}", "code": code}
                    # 5xx errors
                    if isinstance(code, int) and 500 <= code < 600:
                        provider = mx_provider_from_hostname(host)
                        # heuristic: treat some providers as definitive (Microsoft/Mimecast)
                        prov = (provider or '').lower()
                        # Extended list of providers that are authoritative on 5xx responses
                        definitive_providers = (
                            'microsoft 365', 'mimecast', 'microsoft', 'office365',
                            'google', 'gmail', 'yahoo', 'zoho', 'icloud', 'fastmail'
                        )
                        if any(p in prov for p in definitive_providers):
                            s.quit()
                            return {"status": "invalid", "details": f"{host}:{code}", "code": code}
                        # otherwise, if attempts remain, retry once with backoff
                        try:
                            s.quit()
                        except Exception:
                            pass
                        if attempts < max_attempts_per_host:
                            time.sleep(1 * attempts)
                            continue
                        else:
                            return {"status": "invalid", "details": f"{host}:{code}", "code": code}
                except smtplib.SMTPRecipientsRefused as e:
                    try:
                        s.quit()
                    except Exception:
                        pass
                    # attempt to parse SMTP code from exception if present
                    return {"status": "invalid", "details": str(e), "code": None}
                except Exception:
                    # unknown response, try next host
                    try:
                        s.quit()
                    except Exception:
                        pass
                    break
            except (socket.timeout, ConnectionRefusedError, OSError, smtplib.SMTPException):
                # try next host
                break
    return {"status": "unknown", "details": "all_mx_failed_or_grey", "code": None}


def detect_catch_all(mx_hosts: List[Tuple[int, str]], domain: str, timeout: int = 10) -> bool:
    """Detect catch-all by probing a random non-existent address and seeing if accepted."""
    if not mx_hosts or not domain:
        return False
    rand_local = f"noexist-{uuid.uuid4().hex[:10]}"
    test_addr = f"{rand_local}@{domain}"
    res = smtp_probe(test_addr, mx_hosts, timeout=timeout)
    return res.get('status') == 'valid'
