"""Simple GitHub helpers to list org repos and repo contents and return raw file URLs.
"""
from typing import List, Dict, Any
import httpx
from urllib.parse import urlparse


def _owner_repo_from_url(url: str):
    # expect https://github.com/{owner} or https://github.com/{owner}/{repo}
    p = urlparse(url)
    parts = [p for p in p.path.split('/') if p]
    if len(parts) == 0:
        return None, None
    owner = parts[0]
    repo = parts[1] if len(parts) > 1 else None
    return owner, repo


def list_org_repos(org_url: str) -> List[str]:
    owner, repo = _owner_repo_from_url(org_url)
    if not owner:
        return []
    api = f"https://api.github.com/orgs/{owner}/repos"
    try:
        r = httpx.get(api, timeout=20.0)
        if r.status_code != 200:
            return []
        j = r.json()
        return [item.get('full_name') for item in j if item.get('full_name')]
    except Exception:
        return []


def list_repo_files(full_name: str, path: str = '') -> List[Dict[str, Any]]:
    """Return content entries for a repo path via GitHub contents API. full_name is owner/repo."""
    api = f"https://api.github.com/repos/{full_name}/contents/{path.lstrip('/')}"
    try:
        r = httpx.get(api, timeout=20.0)
        if r.status_code != 200:
            return []
        return r.json()
    except Exception:
        return []


def raw_url_from_content_entry(entry: Dict[str, Any]) -> str:
    # content entry has 'download_url' for files
    return entry.get('download_url')
