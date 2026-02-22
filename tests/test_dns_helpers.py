import dns.resolver
import types
import pytest

from connectors import dns_helpers


class FakeA:
    def __init__(self, text):
        self._text = text

    def to_text(self):
        return self._text


class FakeAAAA(FakeA):
    pass


class FakeMX:
    def __init__(self, pref, exchange):
        self.preference = pref
        self.exchange = exchange


class FakeTXT:
    def __init__(self, b):
        # emulate dnspython r.strings bytes list
        self.strings = [b for b in b]


class FakeNS:
    def __init__(self, target):
        self.target = target


def resolve_stub(self, domain, rtype):
    # simple stub that returns fake answers depending on rtype
    if rtype == "A":
        return [FakeA("1.2.3.4")]
    if rtype == "AAAA":
        return [FakeAAAA("2607:5300:0:123::1")]
    if rtype == "MX":
        return [FakeMX(10, "aspmx.l.google.com."), FakeMX(20, "alt1.aspmx.l.google.com.")]
    if rtype == "TXT":
        return [FakeTXT([b"v=spf1 include:example.com -all"])]
    if rtype == "NS":
        return [FakeNS("ns1.example.com."), FakeNS("ns2.example.com.")]
    raise dns.resolver.NoAnswer


def test_get_dns_records_monkeypatch(monkeypatch):
    # monkeypatch the Resolver.resolve method
    monkeypatch.setattr(dns.resolver.Resolver, "resolve", resolve_stub)
    res = dns_helpers.get_dns_records("example.com", timeout=1)
    assert res["a"] == ["1.2.3.4"]
    assert res["aaaa"] == ["2607:5300:0:123::1"]
    assert isinstance(res["mx"], list) and len(res["mx"]) >= 1
    assert res["txt"] and "v=spf1" in res["txt"][0]
    assert res["ns"] and "ns1.example.com" in res["ns"][0]


def test_parse_spf():
    txts = ["v=spf1 include:example.com -all"]
    parsed = dns_helpers.parse_spf(txts)
    assert parsed["has_spf"] is True
    assert "example.com" in parsed["includes"]


def test_mx_provider_from_hostname():
    assert dns_helpers.mx_provider_from_hostname("aspmx.l.google.com") == "Google Workspace"
    assert dns_helpers.mx_provider_from_hostname("mail.protection.outlook.com") == "Microsoft 365"
    assert dns_helpers.mx_provider_from_hostname("mx.secureserver.net") == "GoDaddy"
