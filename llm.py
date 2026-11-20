"""Optional full-AI backend for Red Octopus AI (Google Gemini).

This module is used ONLY when the user puts their OWN Gemini API key
in the .env file (GEMINI_API_KEY). No key is hardcoded anywhere and
no shared key is ever used. If there is no key, or the request fails,
ask_gemini() returns None and the caller falls back to the local
offline brain — the bot keeps working either way.

Uses only the Python standard library (urllib) — no extra dependency.
"""

import json
import os
import urllib.error
import urllib.request

GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    + GEMINI_MODEL
    + ":generateContent"
)


def _load_soul():
    """Read SOUL.md (the bot's personality) if it exists."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SOUL.md")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def _load_dotenv():
    """Read KEY=VALUE lines from .env next to this file (no dependency)."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except OSError:
        pass


def get_api_key():
    """Return the user's own Gemini key, or None if not configured."""
    _load_dotenv()
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key or key == "your_own_key_here":
        return None
    return key


def has_key():
    return get_api_key() is not None


def ask_gemini(prompt, memory):
    """Ask Gemini with the user's memory as context.

    Returns the model's reply text, or None on any failure
    (no key, no network, bad key, quota, timeout, bad response).
    """
    key = get_api_key()
    if not key:
        return None

    lang = memory.get_lang()
    name = memory.get_name() or "unknown"
    facts = memory.data.get("facts", {})
    facts_text = "; ".join("%s: %s" % (k, v) for k, v in facts.items()) or "none yet"
    lang_name = "Burmese (Myanmar language)" if lang == "mm" else "English"

    system = (
        "You are Octo, a friendly red octopus AI assistant living in a terminal. "
        "You are helpful, warm and a little playful. "
        "The user's name is %s. Always reply in %s. "
        "Things you remember about the user: %s. "
        "Keep answers short and useful unless the user asks for detail."
        % (name, lang_name, facts_text)
    )
    soul = _load_soul()
    if soul:
        system += "\n\nYour personality (from SOUL.md):\n" + soul

    contents = []
    for turn in memory.recent_history(10):
        role = "user" if turn["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": turn["text"]}]})
    contents.append({"role": "user", "parts": [{"text": prompt}]})

    body = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": contents,
    }

    req = urllib.request.Request(
        GEMINI_URL + "?key=" + key,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return text.strip()
    except Exception:
        return None
