from typing import Dict

# Import phonenumbers lazily and handle absence gracefully so quick runs can
# proceed without the library installed.
try:
    import phonenumbers
    from phonenumbers import carrier as _pn_carrier
    PHONE_LIB_AVAILABLE = True
except Exception:
    PHONE_LIB_AVAILABLE = False


def parse_phone_number(raw: str, default_region: str = "US") -> Dict[str, object]:
    """Parse phone number and return normalized details.

    If the `phonenumbers` library is not available, return a conservative
    fallback indicating no valid parse.
    """
    out = {"raw": raw, "normalized": None, "valid": False, "type": "UNKNOWN", "carrier": None}
    if not raw:
        return out
    if not PHONE_LIB_AVAILABLE:
        return out
    try:
        parsed = phonenumbers.parse(raw, default_region)
        out["normalized"] = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        out["valid"] = phonenumbers.is_valid_number(parsed)
        num_type = phonenumbers.number_type(parsed)
        type_map = {
            phonenumbers.PhoneNumberType.MOBILE: "MOBILE",
            phonenumbers.PhoneNumberType.FIXED_LINE: "FIXED_LINE",
            phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "MOBILE_OR_FIXED",
            phonenumbers.PhoneNumberType.VOIP: "VOIP",
            phonenumbers.PhoneNumberType.PAGER: "PAGER",
            phonenumbers.PhoneNumberType.UNKNOWN: "UNKNOWN",
        }
        out["type"] = type_map.get(num_type, "UNKNOWN")
        try:
            out["carrier"] = _pn_carrier.name_for_number(parsed, "en")
        except Exception:
            out["carrier"] = None
    except Exception:
        pass
    return out
