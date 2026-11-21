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
RESET = "\033[0m"

PLAIN = os.environ.get("OCTO_PLAIN") == "1"  # used by make_screenshots.py
INTERACTIVE = sys.stdin.isatty() and not PLAIN


def color(text, code):
    if PLAIN:
        return text
    return code + text + RESET


# ----------------------------------------------------------------------
# animated red octopus — 3 frames (tentacles wave, eyes blink)
# ----------------------------------------------------------------------
FRAME_A = [  # eyes open, tentacles centered
    r'        .--""""--.        ',
    r'       /          \\       ',
    r'      |  \\O    O/  |      ',
    r'      |            |      ',
    r'      |   ______   |      ',
    r'       \\          /       ',
    r'        |        |        ',
    r'     __/          \\__     ',
    r'    ||    ||  ||    ||    ',
    r'    ||    ||  ||    ||    ',
    r'   /||    ||  ||    ||\\   ',
    r'   | |    ||  ||    | |   ',
    r'   | |    ||  ||    | |   ',
    r'    \\|    ||  ||    |/    ',
    r'     |    ||  ||    |     ',
    r'    _|    ||  ||    |_    ',
    r'   /      ||  ||      \\   ',
]

FRAME_B = [  # eyes blink, tentacles sway left
    r'        .--""""--.        ',
    r'       /          \\       ',
    r'      |  \\-    -/  |      ',
    r'      |            |      ',
    r'      |   ______   |      ',
    r'       \\          /       ',
    r'        |        |        ',
    r'     __/          \\__     ',
    r'     ||    ||  ||    ||    ',
    r'     ||    ||  ||    ||    ',
    r'    /||    ||  ||    ||\\   ',
    r'    | |    ||  ||    | |   ',
    r'    | |    ||  ||    | |   ',
    r'     \\|    ||  ||    |/    ',
    r'      |    ||  ||    |     ',
    r'     _|    ||  ||    |_    ',
    r'    /      ||  ||      \\   ',
]

FRAME_C = [  # eyes open, tentacles sway right
    r'        .--""""--.        ',
    r'       /          \\       ',
    r'      |  \\O    O/  |      ',
    r'      |            |      ',
    r'      |   ______   |      ',
    r'       \\          /       ',
    r'        |        |        ',
    r'     __/          \\__     ',
    r'   ||    ||  ||    ||     ',
    r'   ||    ||  ||    ||     ',
    r'  /||    ||  ||    ||\\    ',
    r'  | |    ||  ||    | |    ',
    r'  | |    ||  ||    | |    ',
    r'   \\|    ||  ||    |/     ',
    r'    |    ||  ||    |      ',
    r'   _|    ||  ||    |_     ',
    r'  /      ||  ||      \\    ',
]

FRAMES = [FRAME_A, FRAME_B, FRAME_C]


def show_octopus(animated=True):
    """Print the red octopus. Animated when interactive."""
    if not animated or not INTERACTIVE:
        for line in FRAME_A:
            print(color(line, RED))
        return
    frames = (FRAME_A, FRAME_B, FRAME_C, FRAME_A)
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
    lang = memory.get_lang()
    if lang == "mm":
        if name:
            return "မင်္ဂလာပါ၊ %s။ ကျွန်တော် Octo ပါ။ ဘာကူညီပေးရမလဲ။" % name
        return ("မင်္ဂလာပါ။ ကျွန်တော် Octo ပါ။ အနီရောင် ရေဘဝဲ AI လက်ထောက်။ "
                "စကားပြောချင်ရင် ရိုက်ထည့်လိုက်ပါ။ /name <နာမည်> နဲ့ နာမည်ပြောပေးလို့လည်း ရပါတယ်။")
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
    print(reply)


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
    show_octopus(animated=True)
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
                print(color("Octo > ", RED) + ("ပြန်လာခဲ့ပါ။ ကျွန်တော် ဒီမှာပဲ စောင့်နေမယ်။"
                      if ctx.lang == "mm" else
                      "Goodbye! I will be right here when you come back."))
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
            type_out(color("Octo > ", RED) + reply)
            memory.add_turn("octo", reply)

        except KeyboardInterrupt:
            print()
            print(color("Octo > ", RED) + "Goodbye! I will be right here when you come back.")
            break


if __name__ == "__main__":
    main()
