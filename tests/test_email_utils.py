import re
import uuid
from enrichment import email_utils


def test_generate_email_candidates_basic():
    cands = email_utils.generate_email_candidates("Alice", "Smith", "example.com")
    assert any(re.match(r"alice\.smith@example\.com", e) for e in cands)
    assert any(e.endswith("@example.com") for e in cands)
    assert "info@example.com" in cands


def test_choose_best_candidates_scores():
    cands = ["alice.smith@example.com", "info@example.com", "a.smith@example.com"]
    best = email_utils.choose_best_candidates(cands, {"provider": "Google Workspace"}, ["example.com"]) 
    # should return up to 3 entries with score fields
    assert isinstance(best, list)
    assert all("email" in b and "score" in b for b in best)


def test_detect_catch_all_monkeypatch(monkeypatch):
    # monkeypatch smtp_probe to simulate catch-all acceptance
    def fake_smtp_probe(email, mx_hosts, timeout=10, helo_host="example.com"):
        return {"status": "valid", "details": "simulated"}

    monkeypatch.setattr(email_utils, "smtp_probe", fake_smtp_probe)
    # detect_catch_all should return True when smtp_probe returns valid for random address
    mx = [(10, "aspmx.l.google.com")]
    domain = f"example-{uuid.uuid4().hex[:6]}.com"
    assert email_utils.detect_catch_all(mx, domain) is True
