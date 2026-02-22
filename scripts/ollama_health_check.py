#!/usr/bin/env python3
"""Health check for local Ollama server.

Usage examples:
  # quick run with defaults (tests 127.0.0.1 and host.docker.internal)
  python scripts/ollama_health_check.py

  # custom urls
  python scripts/ollama_health_check.py --urls http://127.0.0.1:11434 http://host.docker.internal:11434

The script tries GET /v1/models, GET /v1 and POST /v1/generate (with model/prompt).
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any, Tuple


def try_get(url: str, path: str = "/v1/models", timeout: int = 5) -> Tuple[bool, int | None, Any]:
    full = url.rstrip("/") + path
    req = urllib.request.Request(full, method="GET", headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            try:
                data = json.loads(body)
            except Exception:
                data = body
            return True, getattr(resp, "status", None), data
    except urllib.error.HTTPError as e:
        try:
            txt = e.read().decode("utf-8", errors="replace")
        except Exception:
            txt = str(e)
        return False, getattr(e, "code", None), txt
    except Exception as e:
        return False, None, str(e)


def try_post_generate(url: str, model: str = "phi3:mini", prompt: str = "health check", timeout: int = 10) -> Tuple[bool, int | None, Any]:
    full = url.rstrip("/") + "/v1/generate"
    payload = json.dumps({"model": model, "prompt": prompt}).encode("utf-8")
    req = urllib.request.Request(full, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            try:
                data = json.loads(body)
            except Exception:
                data = body
            return True, getattr(resp, "status", None), data
    except urllib.error.HTTPError as e:
        try:
            txt = e.read().decode("utf-8", errors="replace")
        except Exception:
            txt = str(e)
        return False, getattr(e, "code", None), txt
    except Exception as e:
        return False, None, str(e)


def check_url(url: str, model: str, verbose: bool = True) -> bool:
    ok_any = False
    if verbose:
        print(f"Testing {url}")

    checks = [ ("GET", "/v1/models"), ("GET", "/v1") ]
    for method, path in checks:
        ok, status, data = try_get(url, path=path)
        print(f"  {method} {path:12} -> ok={ok} status={status}")
        if ok:
            print(f"    response: {json.dumps(data) if isinstance(data, (dict, list)) else str(data)[:200]}")
            ok_any = True
            break

    if not ok_any:
        ok, status, data = try_post_generate(url, model=model)
        print(f"  POST /v1/generate -> ok={ok} status={status}")
        if ok:
            print(f"    response: {json.dumps(data) if isinstance(data, (dict, list)) else str(data)[:200]}")
            ok_any = True
        else:
            print(f"    error: {data}")

    return ok_any


def main() -> int:
    p = argparse.ArgumentParser(description="Ollama health-check (host + container addresses)")
    p.add_argument("--urls", nargs="*", default=["http://127.0.0.1:11434", "http://host.docker.internal:11434"], help="Base URLs to test")
    p.add_argument("--model", default="phi3:mini", help="Model name to use for generate test")
    p.add_argument("--no-verbose", dest="verbose", action="store_false", help="Reduce output")
    args = p.parse_args()

    any_ok = False
    for u in args.urls:
        try:
            ok = check_url(u, model=args.model, verbose=args.verbose)
        except Exception as e:
            print(f"Error testing {u}: {e}")
            ok = False
        any_ok = any_ok or ok

    if any_ok:
        print("\nHealth-check: SUCCESS (at least one endpoint responded)")
        return 0
    else:
        print("\nHealth-check: FAILURE (no endpoints responded successfully)")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
