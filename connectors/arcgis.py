import os
import requests
from typing import Dict, Any


def query_arcgis_permits(business_name: str, city: str) -> Dict[str, Any]:
    """Query ArcGIS Sacramento permits. If ERIS_ARCGIS_GEOHUB is set, perform a request; otherwise return simulated data."""
    hub = os.getenv("ERIS_ARCGIS_GEOHUB")
    try:
        if hub:
            # A minimal example: user may provide an ArcGIS feature service/search endpoint
            params = {"q": business_name, "city": city, "f": "json"}
            resp = requests.get(hub, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            # Extract a small set of useful fields
            permits_found = len(data.get("features", []))
            return {
                "arcgis_permits_found": permits_found,
                "arcgis_raw": data,
            }
        else:
            # Simulated response for local runs
            return {
                "arcgis_permits_found": 0,
                "arcgis_raw": None,
            }
    except Exception as e:
        return {"arcgis_error": str(e)}
