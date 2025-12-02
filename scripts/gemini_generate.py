#!/usr/bin/env python3
"""Generate text from Gemini (Generative Language) using python.

This script tries to use the `google-genai` library if installed. If not,
it falls back to the REST endpoint for a simple POST request.

Usage:
  python scripts/gemini_generate.py --prompt "Explain AI in a few words"

Install dependencies (optional, recommended):
  pip install google-genai python-dotenv requests
"""
import os
import sys
import argparse
import textwrap
from dotenv import load_dotenv


def try_genai_library(model: str, prompt: str, api_key: str):
    try:
        from google import genai
    except Exception:
        return None, "google-genai library not available"

    # Try a couple of common client patterns
    try:
        # Pattern: client = genai.Client(); client.models.generate_content(...)
        client = None
        if hasattr(genai, "Client"):
            client = genai.Client()

        if client is not None and hasattr(client, "models") and hasattr(client.models, "generate_content"):
            resp = client.models.generate_content(model=model, contents=prompt)
            # Response shapes vary; try to extract text
            try:
                return getattr(resp, "text", None) or getattr(resp, "response", resp), None
            except Exception:
                return resp, None

        # Pattern: genai.Text.generate(...)
        if hasattr(genai, "Text") and hasattr(genai.Text, "generate"):
            resp = genai.Text.generate(model=model, prompt=prompt)
            return resp, None

        return None, "google-genai installed but API surface not recognized"
    except Exception as exc:
        return None, f"google-genai call failed: {exc}"


def fallback_rest(model: str, prompt: str, api_key: str):
    import requests

    # POST to the generativelanguage REST endpoint. This is a lightweight fallback.
    url = f"https://generativelanguage.googleapis.com/v1beta2/models/{model}:generateText?key={api_key}"
    payload = {"input": prompt}

    resp = requests.post(url, json=payload, timeout=20)
    try:
        return resp.json(), None
    except Exception:
        return resp.text, None


def main():
    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="gemini-2.5-flash", help="Model name (e.g. gemini-2.5-flash)")
    parser.add_argument("--prompt", required=True, help="Prompt / input text to generate from")
    args = parser.parse_args()

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not found in environment or .env. Set it and retry.")
        return 2

    model = args.model
    prompt = args.prompt

    print(f"Using model: {model}")

    result, err = try_genai_library(model=model, prompt=prompt, api_key=api_key)
    if err is None and result is not None:
        print("--- Result (google-genai library) ---")
        print(textwrap.shorten(str(result), 4000))
        return 0

    print(f"google-genai not used: {err}. Falling back to REST endpoint...")

    try:
        rest_res, rest_err = fallback_rest(model=model, prompt=prompt, api_key=api_key)
        print("--- Result (REST fallback) ---")
        print(textwrap.shorten(str(rest_res), 4000))
        return 0
    except Exception as exc:
        print("REST request failed:", exc)
        return 3


if __name__ == "__main__":
    sys.exit(main())
