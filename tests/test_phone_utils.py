from enrichment.phone_utils import parse_phone_number


def test_parse_phone_valid_us():
    # common US number
    res = parse_phone_number("+14155552671")
    assert res["valid"] is True
    assert res["normalized"] == "+14155552671"
    assert res["type"] in ("MOBILE", "FIXED_LINE", "MOBILE_OR_FIXED", "UNKNOWN")


def test_parse_phone_invalid():
    res = parse_phone_number("not-a-number")
    assert res["valid"] is False
    assert res["normalized"] is None
