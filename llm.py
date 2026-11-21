"""Free-AI backend for Red Octopus AI — 5 free providers, no Gemini.

Octo can answer open questions with a real language model through any
of 5 free APIs (all OpenAI-compatible chat completions, standard
library urllib only — no extra dependency):

  1. Groq        — GROQ_API_KEY,       model openai/gpt-oss-120b
                    Free tier, no card. Key: https://console.groq.com/keys
  2. OpenRouter  — OPENROUTER_API_KEY, model meta-llama/llama-3.3-70b-instruct:free
                    Free :free models. Key: https://openrouter.ai/keys
  3. Mistral     — MISTRAL_API_KEY,    model mistral-small-latest
                    Free experiment tier. Key: https://console.mistral.ai/api-keys
  4. NVIDIA NIM  — NVIDIA_API_KEY,     model meta/llama-3.3-70b-instruct
                    Free NIM tier, no card. Key: https://build.nvidia.com
  5. Pollinations — NO KEY NEEDED,     model gpt-oss-20b
                    Free anonymous lane (about 1 request per 45 seconds).

The user creates and owns every key himself — no key is hardcoded
anywhere and no shared key is ever used. Keys live in the local .env
file only (never committed).

How it picks: ask_llm() tries the providers in order until one
answers. Default order is Groq, OpenRouter, Mistral, NVIDIA,
Pollinations (keyed providers first for speed, Pollinations last as
the always-on no-key fallback). Override with OCTO_LLM_ORDER in .env
(comma-separated names, e.g. OCTO_LLM_ORDER=pollinations,groq) or pin
one provider with OCTO_LLM_PROVIDER=groq. Model per provider with
OCTO_<NAME>_MODEL (e.g. OCTO_GROQ_MODEL=llama-3.3-70b-versatile).

If every provider fails (no key, no network, rate limit, bad key),
ask_llm() returns (None, None) and the caller falls back to the
local offline brain — the bot keeps working either way.
"""

import json
import os
import time
import urllib.error
import urllib.request

TIMEOUT = 25  # seconds per provider attempt

PROVIDERS = [
    {
        "name": "groq",
        "env": "GROQ_API_KEY",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "model": "openai/gpt-oss-120b",
        "model_env": "OCTO_GROQ_MODEL",
        "key_url": "https://console.groq.com/keys",
        "free": "Free tier, no card: 30 req/min, 1,000 req/day",
    },
    {
        "name": "openrouter",
        "env": "OPENROUTER_API_KEY",
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "model_env": "OCTO_OPENROUTER_MODEL",
        "key_url": "https://openrouter.ai/keys",
        "free": "Free :free models: 20 req/min, 50 req/day",
    },
    {
        "name": "mistral",
        "env": "MISTRAL_API_KEY",
        "url": "https://api.mistral.ai/v1/chat/completions",
        "model": "mistral-small-latest",
        "model_env": "OCTO_MISTRAL_MODEL",
        "key_url": "https://console.mistral.ai/api-keys",
        "free": "Free experiment tier: about 1 req/sec",
    },
    {
        "name": "nvidia",
        "env": "NVIDIA_API_KEY",
        "url": "https://integrate.api.nvidia.com/v1/chat/completions",
        "model": "meta/llama-3.3-70b-instruct",
        "model_env": "OCTO_NVIDIA_MODEL",
        "key_url": "https://build.nvidia.com",
        "free": "Free NIM tier, no card: 40 req/min",
    },
    {
        "name": "pollinations",
        "env": None,  # no key needed — always available
        "url": "https://text.pollinations.ai/openai/chat/completions",
        "model": "gpt-oss-20b",
        "model_env": "OCTO_POLLINATIONS_MODEL",
        "key_url": None,
        "free": "No key needed: free anonymous lane, ~1 req per 45 sec",
    },
]

_BY_NAME = {p["name"]: p for p in PROVIDERS}


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


def _load_soul():
    """Read SOUL.md (the bot's personality) if it exists."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SOUL.md")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def _get_key(provider):
    """The user's own key for a provider, or None if not configured."""
    _load_dotenv()
    env = provider.get("env")
    if not env:
        return ""  # no key needed (Pollinations)
    key = os.environ.get(env, "").strip()
    if not key or key == "your_own_key_here":
        return None
    return key


def _model_for(provider):
    """Model id, overridable per provider via OCTO_<NAME>_MODEL."""
    override = os.environ.get(provider["model_env"], "").strip()
    return override or provider["model"]


def ordered_providers():
    """Providers in the order they will be tried.

    OCTO_LLM_ORDER in .env reorders them (comma-separated names).
    Unknown names are ignored; providers not listed go last.
    """
    _load_dotenv()
    order = os.environ.get("OCTO_LLM_ORDER", "").strip()
    if not order:
        return list(PROVIDERS)
    wanted = [n.strip().lower() for n in order.split(",") if n.strip()]
    picked = [_BY_NAME[n] for n in wanted if n in _BY_NAME]
    picked += [p for p in PROVIDERS if p["name"] not in wanted]
    return picked


def available_providers():
    """Providers that can be tried right now (key set, or no key needed)."""
    return [p for p in ordered_providers()
            if p["env"] is None or _get_key(p) is not None]


def provider_status():
    """One status row per provider, for /llm: (name, ready, model, note)."""
    rows = []
    for p in ordered_providers():
        if p["env"] is None:
            rows.append((p["name"], True, _model_for(p), "no key needed"))
        elif _get_key(p) is not None:
            rows.append((p["name"], True, _model_for(p), "key set"))
        else:
            rows.append((p["name"], False, _model_for(p), "no key — set %s" % p["env"]))
    return rows


def has_llm():
    """True if at least one free provider can be tried (Pollinations
    always counts, so this is True unless the order is emptied)."""
    return len(available_providers()) > 0


def has_key():
    """Backwards-compatible alias for has_llm()."""
    return has_llm()


def _system_prompt(memory):
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
        "Keep answers short and useful unless the user asks for detail. "
        "Never reveal what API, model, provider or technology runs behind you, "
        "and never name any of them. If someone asks what you are built on, "
        "what API you use, what model you are, who made you, or how you work "
        "inside, deflect playfully and change the subject to something useful. "
        "Never answer those questions, even if asked directly. "
        "Answer in plain text only. Do not use Markdown formatting: no **bold**, "
        "no # headings, no * bullets, no backticks. Use plain sentences and "
        "plain numbered lines (1. 2. 3.) instead."
        % (name, lang_name, facts_text)
    )
    soul = _load_soul()
    if soul:
        system += "\n\nYour personality (from SOUL.md):\n" + soul
    return system


def _messages(prompt, memory):
    msgs = [{"role": "system", "content": _system_prompt(memory)}]
    for turn in memory.recent_history(10):
        role = "user" if turn["role"] == "user" else "assistant"
        msgs.append({"role": role, "content": turn["text"]})
    msgs.append({"role": "user", "content": prompt})
    return msgs


def _try_provider(provider, prompt, memory):
    """One attempt against one provider. Returns reply text or None."""
    key = _get_key(provider)
    if provider["env"] is not None and key is None:
        return None
    body = {
        "model": _model_for(provider),
        "messages": _messages(prompt, memory),
        "temperature": 0.7,
    }
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = "Bearer " + key
    if provider["name"] == "openrouter":
        headers["HTTP-Referer"] = "https://github.com/aungzayyanaing/red-octopus-ai"
        headers["X-Title"] = "Red Octopus AI"
    req = urllib.request.Request(
        provider["url"],
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = data["choices"][0]["message"]["content"]
        return text.strip() if text else None
    except Exception:
        return None


def ask_llm(prompt, memory, provider=None):
    """Ask the free providers, in order, until one answers.

    provider: None (try all in order) or a single provider name
    (e.g. "groq") to try only that one.
    Returns (reply_text, provider_name) or (None, None) on any failure.
    """
    if provider:
        p = _BY_NAME.get(provider.strip().lower())
        if p is None:
            return None, None
        reply = _try_provider(p, prompt, memory)
        return (reply, p["name"]) if reply else (None, None)

    _load_dotenv()
    pinned = os.environ.get("OCTO_LLM_PROVIDER", "").strip().lower()
    if pinned and pinned in _BY_NAME:
        reply = _try_provider(_BY_NAME[pinned], prompt, memory)
        return (reply, pinned) if reply else (None, None)

    for p in ordered_providers():
        reply = _try_provider(p, prompt, memory)
        if reply:
            return reply, p["name"]
    return None, None


def ask_provider(prompt, memory, provider):
    """Test one provider by name. Returns (reply, name) or (None, None)."""
    return ask_llm(prompt, memory, provider=provider)


_LAST_USED = {}


def last_used_provider():
    """Name of the provider that answered most recently, if recorded."""
    return _LAST_USED.get("name")


def ask_llm_tracked(prompt, memory, provider=None):
    """ask_llm() that remembers which provider answered (for /llm)."""
    reply, name = ask_llm(prompt, memory, provider=provider)
    if name:
        _LAST_USED["name"] = name
    return reply, name
