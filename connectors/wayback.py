import os
import requests
from typing import List, Dict, Any


def query_wayback_cdx(url: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Query the Wayback CDX API for captures of the given URL.
    Returns a list of capture metadata dicts. If WAYBACK_BASE not set, use default public endpoint.
    """
    base = os.getenv("WAYBACK_BASE", "https://web.archive.org/cdx/search/cdx")
    params = {"url": url, "output": "json", "limit": limit}
    try:
        resp = requests.get(base, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        # First row is field names if using json output; convert to dicts
        if not data:
            return []
        headers = data[0]
        results = [dict(zip(headers, row)) for row in data[1:]]
        return results
    except Exception as e:
        return [{"error": str(e)}]
