import os
import requests
from typing import Dict, Any


def crawl_craigslist_by_license(license_number: str) -> Dict[str, Any]:
    """Simple ReconDon-style Craigslist crawler stub. This is a safe stub that attempts to use Wayback CDX if available.
    In production, replace with the full ReconDon crawler implementation.
    """
    wayback = os.getenv("WAYBACK_BASE", "https://web.archive.org/cdx/search/cdx")
    # Use Wayback to search for craigslist.org URLs containing the license number
    query = f"https://sacramento.craigslist.org/*{license_number}*"
    params = {"url": query, "output": "json", "limit": 20}
    try:
        resp = requests.get(wayback, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        headers = data[0] if data else []
        captures = [dict(zip(headers, row)) for row in data[1:]] if data and len(data) > 1 else []
        found = len(captures) > 0
        return {
            "cl_wayback_matches": found,
            "cl_wayback_count": len(captures),
            "cl_wayback_captures": captures[:5],
        }
    except Exception as e:
        return {"error": str(e)}
