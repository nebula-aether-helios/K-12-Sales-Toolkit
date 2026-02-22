import pytest
from connectors.dns_helpers import is_valid_hostname
from tools.upscale_reprobe import normalize_phone


def test_is_valid_hostname():
    assert is_valid_hostname('example.com')
    assert is_valid_hostname('sub.domain.example.co.uk')
    assert not is_valid_hostname('localhost')
    assert not is_valid_hostname('bad_host!name')
    assert not is_valid_hostname('')


def test_normalize_phone():
    assert normalize_phone('(555) 123-4567') == '+15551234567'
    assert normalize_phone('1-800-555-1212') == '+18005551212'
    assert normalize_phone('+44 20 7946 0958') == '+442079460958'
    assert normalize_phone('12345') is None
