#!/usr/bin/env python3
"""Check GEMINI_API_KEY from .env by doing a lightweight request.

This script:
- loads `GEMINI_API_KEY` from the project's `.env`
- performs a format sanity check
- calls Google Generative Language 'models' endpoint with `?key=` to validate the key

Install dependencies:
  pip install python-dotenv requests

Run:
  python scripts/check_gemini_key.py
"""
import os
import sys
import textwrap
from dotenv import load_dotenv
import requests


def short(s: str, length: int = 400) -> str:
    return s if len(s) <= length else s[:length] + "..."


def main() -> int:
    # Load .env from repo root (script run from project root)
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not found in environment or .env file.")
        return 2

    print("Found GEMINI_API_KEY (hidden). Performing basic checks...")

    # Basic format heuristics
    if api_key.startswith("AIza"):
        print("- Looks like a Google API key (starts with 'AIza').")
    elif api_key.startswith("sk-"):
        print("- Looks like an OpenAI-style secret key (starts with 'sk-').")
    else:
        print("- Key format unknown. Will still attempt a validation request.")

    # Attempt a lightweight GET to the Generative Language models list endpoint.
    # We use the `?key=` query parameter which some Google APIs accept for API keys.
    endpoint = f"https://generativelanguage.googleapis.com/v1beta2/models?key={api_key}"

    print(f"- Requesting models endpoint: {endpoint}")

    try:
        resp = requests.get(endpoint, timeout=10)
    except requests.RequestException as exc:
        print("Network error while attempting to validate the key:", str(exc))
        return 3

    code = resp.status_code
    print(f"- HTTP status: {code}")

    if code == 200:
        try:
            data = resp.json()
        except ValueError:
            print("- Received 200 but response is not valid JSON. Key may be partially valid.")
            return 0

        # Try to display model names (if available)
        models = data.get("models") or data.get("model") or data.get("availableModels")
        if isinstance(models, list):
            print(f"- Key appears valid. {len(models)} model(s) returned:")
            for m in models[:10]:
                # model could be a dict or a string
                if isinstance(m, dict):
                    name = m.get("name") or m.get("model") or str(m)
                else:
                    name = str(m)
                print("  -", short(name, 200))
        else:
            print("- Key appears valid (200). Response:")
            print(textwrap.indent(short(resp.text), "  "))

        return 0

    if code in (401, 403):
        print("- Unauthorized or forbidden. The API key is invalid or lacks permissions.")
        try:
            print(textwrap.indent(short(resp.text), "  "))
        except Exception:
            pass
        return 4

    # Other codes: print a short body to help debugging
    print("- Received unexpected status. Response body (truncated):")
    print(textwrap.indent(short(resp.text), "  "))
    return 5


if __name__ == "__main__":
    sys.exit(main())
