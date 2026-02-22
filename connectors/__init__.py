"""Connectors package for ArcGIS, Wayback, DNS/MX, and ReconDon Craigslist crawler.
Each connector attempts to use real APIs if environment variables are set;
otherwise they provide a safe simulated response for local testing.
"""

"""Lightweight connectors package.

Avoid importing heavy external-API connectors (requests, etc.) at package
import time so scripts that only need DNS helpers can import this package
without triggering extra dependencies. Each connector should be imported
on-demand by consumers that need them.
"""

# Export only DNS helper by default to keep imports cheap.
try:
    from .dns_helpers import get_dns_records, parse_spf, mx_provider_from_hostname
    __all__ = ["get_dns_records", "parse_spf", "mx_provider_from_hostname"]
except Exception:
    __all__ = []

