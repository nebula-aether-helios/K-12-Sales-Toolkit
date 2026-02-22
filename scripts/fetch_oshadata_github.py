#!/usr/bin/env python3
"""Fetch OSHADataDoor dataset files from GitHub and save locally under outputs/oshadata.

Uses existing `catalog_api.fetchers.github_fetcher` to list repos and contents.
"""
import os
import sys
import logging
from pathlib import Path

# Ensure repository root is on sys.path so `catalog_api` package is importable when
# running this script directly.
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import requests
from catalog_api.fetchers import github_fetcher

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("fetch_oshadata")


ORG_URL = "https://github.com/OSHADataDoor"
OUT_DIR = Path("outputs/oshadata")


def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def download_file(url: str, dest: Path) -> bool:
    try:
        r = requests.get(url, timeout=30)
        if r.status_code != 200:
            logger.error("Failed to download %s: HTTP %s", url, r.status_code)
            return False
        dest.write_bytes(r.content)
        return True
    except Exception as e:
        logger.error("Error downloading %s: %s", url, e)
        return False


def main():
    ensure_dir(OUT_DIR)
    repos = github_fetcher.list_org_repos(ORG_URL)
    if not repos:
        logger.error("No repos found for %s", ORG_URL)
        sys.exit(2)
    logger.info("Found %d repos", len(repos))
    downloaded = 0
    for full_name in repos:
        logger.info("Checking repo: %s", full_name)
        entries = github_fetcher.list_repo_files(full_name, path="data")
        if not entries:
            logger.info(" No data/ directory or no entries in %s", full_name)
            continue
        repo_dir = OUT_DIR / full_name.replace('/', '_')
        ensure_dir(repo_dir)
        for e in entries:
            # e can be directory or file; we only download files with download_url
            name = e.get('name')
            download_url = e.get('download_url') or github_fetcher.raw_url_from_content_entry(e)
            if not download_url:
                logger.info("  Skipping (no download_url): %s", name)
                continue
            dest = repo_dir / name
            if dest.exists():
                logger.info("  Already exists: %s", dest)
                continue
            logger.info("  Downloading %s -> %s", download_url, dest)
            if download_file(download_url, dest):
                downloaded += 1

    logger.info("Done. Total files downloaded: %d", downloaded)


if __name__ == '__main__':
    main()
