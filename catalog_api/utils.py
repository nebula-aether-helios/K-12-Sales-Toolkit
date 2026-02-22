import json
from typing import Any


def safe_json_dumps(obj: Any) -> str:
    try:
        return json.dumps(obj)
    except Exception:
        return json.dumps(str(obj))
