"""Simple AI client that prefers local mock when available, otherwise calls Azure OpenAI endpoints.

This lightweight client uses only the Python standard library so it works offline when
pointing at a local model mock. It expects environment variables defined in the repo `.env`.

Usage:
    from catalog_api.ai_client import ai_chat
    resp = ai_chat([{"role":"user","content":"Hello"}])
    print(resp)
"""
from __future__ import annotations

import json
import os
import urllib.request
import urllib.error
from typing import List, Dict


def _post_json(url: str, data: Dict, headers: Dict[str, str]) -> Dict:
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8")
            return {"error": True, "status": e.code, "body": body}
        except Exception:
            return {"error": True, "status": e.code, "body": None}
    except Exception as e:
        return {"error": True, "exception": str(e)}


def ai_chat(messages: List[Dict[str, str]], timeout: int = 30) -> str:
    """Send chat messages to the selected model and return the assistant text.

    messages: list of {role: str, content: str}
    """
    selection = os.getenv("MODEL_SELECTION", "GPT5_2")
    # Local mock takes precedence when enabled
    if os.getenv("LOCAL_MODEL_MOCK", "0") in ("1", "true", "True") or selection == "LOCAL_MOCK":
        url = os.getenv("LOCAL_MODEL_MOCK_URL", "http://localhost:5001")
        # Try several common mock endpoints and payload shapes
        text = "\n".join(m["content"] for m in messages if "content" in m)
        headers = {"Content-Type": "application/json"}

        # 1) /v1/generate with {prompt: str}
        resp = _post_json(f"{url}/v1/generate", {"prompt": text}, headers)
        if resp and not resp.get("error") and ("choices" in resp or "id" in resp):
            # flask mock returns choices -> text
            try:
                return resp.get("choices", [])[0].get("text")
            except Exception:
                return json.dumps(resp)

        # 2) /v1/infer with {input: str}
        resp = _post_json(f"{url}/v1/infer", {"input": text}, headers)
        if resp and not resp.get("error"):
            return resp.get("output") or resp.get("result") or json.dumps(resp)

        # 3) /v1/predict fallback
        resp = _post_json(f"{url}/v1/predict", {"prompt": text}, headers)
        if resp and not resp.get("error"):
            return resp.get("output") or resp.get("result") or json.dumps(resp)

        return str(resp)

    # GPT-5.2 (Azure 'responses' endpoint)
    if selection == "GPT5_2":
        endpoint = os.getenv("GPT5_2_AZURE_ENDPOINT")
        key = os.getenv("GPT5_2_AZURE_KEY")
        deployment = os.getenv("GPT5_2_DEPLOYMENT", "gpt-5.2-chat")
        api_version = os.getenv("GPT5_2_API_VERSION", "2025-04-01-preview")
        if not endpoint or not key:
            return "GPT5_2 endpoint or key not configured"
        # Construct payload for Azure Responses API
        payload = {
            "deployment": deployment,
            "input": {
                "messages": messages,
            },
            "max_tokens": 1024,
        }
        headers = {
            "Content-Type": "application/json",
            "api-key": key,
        }
        resp = _post_json(endpoint, payload, headers)
        # Azure Responses returns choices -> message
        try:
            if "output" in resp:
                # newer Responses format
                outputs = resp.get("output")
                if isinstance(outputs, list):
                    # join text parts
                    return "".join(o.get("content", "") if isinstance(o, dict) else str(o) for o in outputs)
            if "choices" in resp:
                choices = resp["choices"]
                if choices and isinstance(choices, list):
                    msg = choices[0].get("message") or choices[0].get("content")
                    if isinstance(msg, dict):
                        return msg.get("content", json.dumps(msg))
                    return str(msg)
        except Exception:
            pass
        return json.dumps(resp)

    # GPT-5 Mini fallback (Azure OpenAI style)
    if selection == "GPT5_MINI":
        # Use AZURE_AI_ENDPOINT and AZURE_AI_KEY to call /openai/deployments/{deployment}/chat/completions
        endpoint = os.getenv("AZURE_AI_ENDPOINT")
        key = os.getenv("AZURE_AI_KEY")
        deployment = os.getenv("GPT5_MINI_DEPLOYMENT", "gpt-5-mini")
        if not endpoint or not key:
            return "GPT5 Mini endpoint or key not configured"
        url = endpoint.rstrip("/") + f"/openai/deployments/{deployment}/chat/completions?api-version={os.getenv('GPT5_MINI_API_VERSION','2024-12-01-preview')}"
        payload = {"messages": messages, "max_tokens": 1024}
        headers = {"Content-Type": "application/json", "api-key": key}
        resp = _post_json(url, payload, headers)
        try:
            if "choices" in resp:
                return resp["choices"][0]["message"]["content"]
        except Exception:
            pass
        return json.dumps(resp)

    return "Model selection not supported"


if __name__ == "__main__":
    # quick local test when run directly
    print(ai_chat([{"role": "user", "content": "Hello from local test"}]))
