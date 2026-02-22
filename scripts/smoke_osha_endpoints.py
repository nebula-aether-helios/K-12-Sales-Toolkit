#!/usr/bin/env python3
"""Smoke-test for OSHA/DOL endpoints: DOL Fatalities API + EnforceData (enforcedata.dol.gov)

Fail-fast checks: validate env key and simple sample queries.
"""
import os
import sys
import logging
import argparse

import requests
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("smoke_osha")


def load_key():
    load_dotenv()
    return os.environ.get("US_DEPT_OF_LABOR_API")


def test_dol_fatalities(api_key: str) -> bool:
    url = "https://api.dol.gov/V1/Safety/Fatalities"
    headers = {"X-API-KEY": api_key}
    params = {"$filter": "contains(establishment_name,'Sacramento')", "$top": 1}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)
    except Exception as e:
        logger.error("DOL Fatalities request failed: %s", e)
        return False
    logger.info("DOL Fatalities HTTP %s", r.status_code)
    if r.status_code == 200:
        try:
            j = r.json()
            # success if we can parse JSON and see expected structure
            if isinstance(j, dict) and ("d" in j or "results" in j):
                logger.info("DOL Fatalities endpoint OK (parsed response)")
                return True
        except Exception:
            logger.error("DOL Fatalities returned non-JSON or unexpected payload")
            return False
    else:
        logger.error("DOL Fatalities returned status %s: %s", r.status_code, r.text[:200])
        return False


def test_enforcedata() -> bool:
    url = "https://enforcedata.dol.gov/api/osha_inspection"
    params = {"establishment_name": "Sacramento", "page": 1}
    try:
        r = requests.get(url, params=params, timeout=15)
    except Exception as e:
        logger.error("EnforceData request failed: %s", e)
        return False
    logger.info("EnforceData HTTP %s", r.status_code)
    if r.status_code == 200:
        try:
            j = r.json()
            if isinstance(j, dict) and ("results" in j or "data" in j):
                logger.info("EnforceData endpoint OK (parsed response)")
                return True
        except Exception:
            logger.error("EnforceData returned non-JSON or unexpected payload")
            return False
    else:
        logger.error("EnforceData returned status %s: %s", r.status_code, r.text[:200])
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dol-key", help="Override US_DEPT_OF_LABOR_API key via CLI")
    args = parser.parse_args()

    api_key = args.dol_key or load_key()
    if not api_key:
        logger.warning("No US_DEPT_OF_LABOR_API key found in environment; DOL Fatalities test will be skipped.")
    ok_dol = False
    if api_key:
        ok_dol = test_dol_fatalities(api_key)

    ok_enforce = test_enforcedata()

    if ok_dol or ok_enforce:
        logger.info("Smoke test: at least one OSHA enforcement source reachable.")
        sys.exit(0)
    else:
        logger.error("Smoke test failed: both DOL Fatalities and EnforceData appear unreachable or unauthorized.")
        sys.exit(2)


if __name__ == '__main__':
    main()
