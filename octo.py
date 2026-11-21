#!/usr/bin/env python3
"""Octo — Red Octopus AI.

A JARVIS-style terminal chatbot. Runs in Windows PowerShell and in
macOS/Linux terminals with Python 3.10+.

    python octo.py                    start the chat
    python octo.py "your question"    one-shot answer and exit

The octopus answers with its offline brain by default. If you put your
OWN free API key in .env (Groq, OpenRouter, Mistral or NVIDIA — or use
Pollinations, which needs no key at all), open questions are answered
by a real AI instead — like a full AI. No key is ever bundled.

Memory lives on your own computer (memory.json + MEMORY.md) and
survives restarts. See README.md for the full guide.
"""

import os
import re
import sys
import time
from types import SimpleNamespace

# Windows: enable ANSI colour support in the console.
if os.name == "nt":
    os.system("")

import brain
import commands
import llm
from memory import Memory

# ----------------------------------------------------------------------
# colours (ANSI)
# ----------------------------------------------------------------------
RED = "\033[91m"
CYAN = "\033[96m"
GOLD = "\033[93m"
GREEN = "\033[92m"
DIM = "\033[90m"
BOLD = "\033[1m"
BANNER_RED = "\033[1;38;5;196m"
RESET = "\033[0m"

PLAIN = os.environ.get("OCTO_PLAIN") == "1"  # used by make_screenshots.py
INTERACTIVE = sys.stdin.isatty() and not PLAIN


def color(text, code):
    if PLAIN:
        return text
    return code + text + RESET


# ----------------------------------------------------------------------
# markdown rendering — the terminal cannot render Markdown, so raw
# **bold** markers used to show up on screen. Convert them to ANSI
# (bold / cyan) or strip them, so an answer never shows raw **.
# ----------------------------------------------------------------------
_MD_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_MD_CODE_RE = re.compile(r"`([^`]+)`")
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_MD_ITALIC_RE = re.compile(r"(?<!\w)[*_]([^*_]+)[*_](?!\w)")


def render_markdown(text):
    """Render a Markdown reply as plain terminal text.

    **bold** -> ANSI bold, `code` -> cyan, [text](url) -> text (url),
    # headings -> bold text, * bullets -> - bullets, ``` fences are
    dropped. Any stray ** left over is removed, never shown.
    """
    lines = []
    in_fence = False
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            lines.append(line)
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            line = m.group(2)
            stripped = line
        if re.match(r"^\*\s+", stripped):
            line = "- " + stripped[2:]
        line = _MD_LINK_RE.sub(
            lambda mm: "%s (%s)" % (mm.group(1), mm.group(2)), line)
        line = _MD_BOLD_RE.sub(
            lambda mm: color(mm.group(1), BOLD), line)
        line = _MD_CODE_RE.sub(
            lambda mm: color(mm.group(1), CYAN), line)
        line = _MD_ITALIC_RE.sub(lambda mm: mm.group(1), line)
        line = line.replace("**", "").replace("__", "")
        lines.append(line)
    return "\n".join(lines).strip("\n")


# ----------------------------------------------------------------------
# big block-letter name banner — OCTO in chunky red block letters,
# the way CLAUDE CODE shows its name on startup.
# ----------------------------------------------------------------------
NAME_BANNER = [
    r" ██████   ██████  ████████  ██████ ",
    r"██    ██ ██    ██    ██    ██    ██",
    r"██    ██ ██          ██    ██    ██",
    r"██    ██ ██          ██    ██    ██",
    r"██    ██ ██          ██    ██    ██",
    r"██    ██ ██    ██    ██    ██    ██",
    r" ██████   ██████     ██     ██████ ",
]


def show_name_banner():
    """Print the big OCTO block-letter banner."""
    for line in NAME_BANNER:
        print(color("       " + line, BANNER_RED))
    print(color("              RED OCTOPUS AI", RED))


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# tiny red pixel character — 3 frames (eyes blink, feet shift).
# A small blocky sprite: red body, two black eyes (gaps), stubby legs,
# standing on a ground line. Same character as the web demo.
# ----------------------------------------------------------------------
MINI_A = [  # eyes open
    r'  ███████  ',
    r' █████████ ',
    r' ██ ███ ██ ',
    r' █████████ ',
    r' █████████ ',
    r'  ██   ██  ',
    r'___________',
]

MINI_B = [  # eyes blink (closed)
    r'  ███████  ',
    r' █████████ ',
    r' █████████ ',
    r' █████████ ',
    r' █████████ ',
    r'  ██   ██  ',
    r'___________',
]

MINI_C = [  # eyes open, feet shifted right
    r'  ███████  ',
    r' █████████ ',
    r' ██ ███ ██ ',
    r' █████████ ',
    r' █████████ ',
    r'   ██   ██ ',
    r'___________',
]

MINI_FRAMES = [MINI_A, MINI_B, MINI_C]


def show_mini(animated=True):
    """Print the tiny red character. Animated when interactive."""
    if not animated or not INTERACTIVE:
        for line in MINI_A:
            print(color(line, RED))
        return
    frames = (MINI_A, MINI_B, MINI_C, MINI_A)
    for i, frame in enumerate(frames):
        for line in frame:
            print(color(line, RED))
        time.sleep(0.35)
        if i < len(frames) - 1:
            # move the cursor back up so the next frame draws over this one
            sys.stdout.write("\033[%dA" % len(frame))
            sys.stdout.flush()
    # final frame stays on screen


def type_out(text, delay=0.012):
    """Print text with a typing effect (instant when not interactive)."""
    if not INTERACTIVE:
        print(text)
        return
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def thinking():
    """A short 'thinking' animation while the brain works."""
    if not INTERACTIVE:
        return
    for dots in ("", ".", "..", "..."):
        sys.stdout.write("\r" + color("Octo is thinking" + dots, DIM) + "   ")
        sys.stdout.flush()
        time.sleep(0.18)
    sys.stdout.write("\r" + " " * 30 + "\r")
    sys.stdout.flush()


def clear_screen():
    if PLAIN:
        print("--- screen cleared ---")
        return
    os.system("cls" if os.name == "nt" else "clear")


def banner(full_ai):
    if full_ai:
        ready = [p["name"] for p in llm.available_providers()]
        mode = "Full AI mode — free providers ready: %s" % ", ".join(ready)
    else:
        mode = "Offline brain mode — add a free API key in .env for full AI (/llm to see providers)"
    print(color("=" * 52, GOLD))
    print(color("  OCTO  —  Red Octopus AI", "\033[1;91m"))
    print(color("  Your terminal AI assistant. Type /help to begin.", CYAN))
    print(color("  " + mode, DIM))
    print(color("=" * 52, GOLD))


def greet(memory):
    name = memory.get_name()
    if name:
        return "Hello, %s! I am Octo. What can I do for you?" % name
    return ("Hello! I am Octo, your red octopus AI assistant. "
            "Just type to chat. Tell me your name with /name <name>.")


def one_shot(question):
    """Answer a single question and exit (one-shot mode).

    Usage:  python octo.py "what time is it?"
    The answer is printed on its own, so it works in scripts and pipes.
    """
    memory = Memory()
    reply = None
    if llm.has_llm():
        reply, _used = llm.ask_llm_tracked(question, memory)
    if reply is None:
        reply = brain.respond(question, memory)
    memory.add_turn("user", question)
    memory.add_turn("octo", reply)
    print(render_markdown(reply))


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] in ("-h", "--help"):
            print('Usage:')
            print('  python octo.py                start the chat')
            print('  python octo.py "question"     one-shot answer and exit')
            print('  python octo.py --help         show this help')
            return
        one_shot(" ".join(sys.argv[1:]))
        return

    memory = Memory()
    full_ai = llm.has_llm()
    ctx = SimpleNamespace(memory=memory, lang=memory.get_lang())

    if INTERACTIVE:
        clear_screen()
    show_name_banner()
    show_mini(animated=True)
    banner(full_ai)
    print()
    type_out(color("Octo > ", RED) + greet(memory))
    print(color("Type /help for commands, /exit to quit.", DIM))
    print()

    while True:
        try:
            prompt = "You > " if PLAIN else color("You > ", GOLD)
            try:
                user_text = input(prompt)
            except EOFError:
                print()
                print(color("Octo > ", RED) +
                      "Goodbye! I will be right here when you come back.")
                break
            if not sys.stdin.isatty():
                # Piped input is not echoed by the terminal; echo it so a
                # captured transcript reads like a real session.
                sys.stdout.write(user_text + "\n")
            user_text = user_text.strip()
            if not user_text:
                continue

            memory.add_turn("user", user_text)

            if user_text.startswith("/"):
                reply, should_exit = commands.dispatch(user_text, ctx)
                if reply == "__CLEAR__":
                    clear_screen()
                    continue
                type_out(color("Octo > ", RED) + reply)
                memory.add_turn("octo", reply)
                if should_exit:
                    break
                continue

            thinking()
            reply = None
            if full_ai:
                reply, _used = llm.ask_llm_tracked(user_text, memory)
            if reply is None:
                reply = brain.respond(user_text, memory)
            type_out(color("Octo > ", RED) + render_markdown(reply))
            memory.add_turn("octo", reply)

        except KeyboardInterrupt:
            print()
            print(color("Octo > ", RED) + "Goodbye! I will be right here when you come back.")
            break


if __name__ == "__main__":
    main()
