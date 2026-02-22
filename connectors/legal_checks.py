import random
from typing import Dict


def check_tax_lien(license_number: str) -> Dict:
    """Stub for tax lien lookup. Returns simulated result for now."""
    has_lien = random.random() < 0.03
    return {"tax_lien_found": 1 if has_lien else 0, "tax_lien_amount": (random.randint(100, 50000) if has_lien else 0)}


def check_sos_suspended(license_number: str) -> Dict:
    """Stub for Secretary of State suspended check."""
    suspended = random.random() < 0.01
    return {"sos_suspended": 1 if suspended else 0}


def check_hubzone(business_name: str, address_city: str) -> Dict:
    """Stub for HUBZone or similar high-value region check."""
    hubzone = random.random() < 0.02
    return {"hubzone_eligible": 1 if hubzone else 0}
