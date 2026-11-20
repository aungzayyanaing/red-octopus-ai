#!/usr/bin/env python3
"""Render REAL screenshots of Red Octopus AI.

Runs octo.py scripted (OCTO_PLAIN=1, piped stdin), captures the
actual stdout, and draws it into terminal-style PNG images
(dark background, monospace, colours approximated from the ANSI
colours the app really uses).

Scenarios:
  01-startup.png  banner + octopus + greeting
  02-chat.png     a real conversation (teach + recall + todos + joke)
  03-help.png     the /help output

Usage:  python3 make_screenshots.py
Output: docs/screenshots/*.png
"""

import os
import re
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont, features

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(ROOT, "docs", "screenshots")

MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
MYANMAR = "/usr/share/fonts/truetype/noto/NotoSansMyanmar-Regular.ttf"
MYANMAR_BOLD = "/usr/share/fonts/truetype/noto/NotoSansMyanmar-Bold.ttf"

FONT_SIZE = 17
LINE_H = 25
PAD_X = 24
PAD_Y = 22
BG = (13, 17, 23)
FG = (229, 231, 235)
RED = (255, 85, 85)
GOLD = (251, 191, 36)
CYAN = (0, 208, 255)
DIM = (156, 163, 175)

MY_RE = re.compile(r"[\u1000-\u109F]")

SCENARIOS = {
    "01-startup.png": "/exit\n",
    "02-chat.png": (
        "/name Aung\n"
        "မင်္ဂလာပါ\n"
        "/teach what is the capital of Myanmar? | Naypyidaw\n"
        "what is the capital of Myanmar?\n"
        "/todo buy a book\n"
        "/todos\n"
        "/joke\n"
        "/exit\n"
    ),
    "03-help.png": "/help\n/exit\n",
}


def segments(line):
    """Split a line into (text, is_myanmar) runs."""
    out = []
    buf = ""
    cur = None
    for ch in line:
        is_mm = bool(MY_RE.match(ch))
        if cur is None:
            cur = is_mm
            buf = ch
        elif is_mm == cur:
            buf += ch
        else:
            out.append((buf, cur))
            buf = ch
            cur = is_mm
    if buf:
        out.append((buf, cur))
    return out


def get_fonts(bold=False):
    return (
        ImageFont.truetype(MYANMAR_BOLD if bold else MYANMAR, FONT_SIZE),
        ImageFont.truetype(MONO_BOLD if bold else MONO, FONT_SIZE),
    )


def line_width(draw, line, bold=False):
    mm_font, mono_font = get_fonts(bold)
    w = 0
    for text, is_mm in segments(line):
        w += draw.textlength(text, font=mm_font if is_mm else mono_font)
    return w


def draw_line(draw, x, y, line, color, bold=False):
    mm_font, mono_font = get_fonts(bold)
    for text, is_mm in segments(line):
        font = mm_font if is_mm else mono_font
        draw.text((x, y), text, font=font, fill=color)
        x += draw.textlength(text, font=font)


def colorize(line, in_banner_art):
    """Return (color, bold) approximating the app's real ANSI colours."""
    if in_banner_art:
        return RED, False
    if line.startswith("Octo > "):
        return FG, False
    if line.startswith("You > "):
        return FG, False
    if line.startswith("==="):
        return GOLD, False
    if "OCTO" in line and "Red Octopus" in line:
        return RED, True
    if line.startswith("Type /help"):
        return DIM, False
    if line.startswith("  Your terminal") or "Offline brain mode" in line or "Full AI mode" in line:
        return CYAN, False
    return FG, False


def render(text, out_path):
    lines = text.rstrip("\n").split("\n")
    # everything before the first ==== line is the octopus art
    banner_idx = next((i for i, ln in enumerate(lines) if ln.startswith("===")), len(lines))

    probe = Image.new("RGB", (10, 10))
    probe_draw = ImageDraw.Draw(probe)
    width = max(line_width(probe_draw, ln) for ln in lines) + PAD_X * 2
    height = len(lines) * LINE_H + PAD_Y * 2

    img = Image.new("RGB", (int(width), height), BG)
    draw = ImageDraw.Draw(img)
    y = PAD_Y
    for i, ln in enumerate(lines):
        color, bold = colorize(ln, i < banner_idx)
        # colour the "Octo > " / "You > " prefixes like the app does
        for prefix, pcolor in (("Octo > ", RED), ("You > ", GOLD)):
            if ln.startswith(prefix):
                draw_line(draw, PAD_X, y, prefix, pcolor, bold=False)
                rest = ln[len(prefix):]
                mm_font, mono_font = get_fonts(bold)
                x = PAD_X + draw.textlength(prefix, font=mono_font)
                for text, is_mm in segments(rest):
                    font = mm_font if is_mm else mono_font
                    draw.text((x, y), text, font=font, fill=color)
                    x += draw.textlength(text, font=font)
                break
        else:
            draw_line(draw, PAD_X, y, ln, color, bold)
        y += LINE_H
    img.save(out_path)
    return out_path, img.size


def run_scenario(stdin_text):
    env = dict(os.environ)
    env["OCTO_PLAIN"] = "1"
    proc = subprocess.run(
        [sys.executable, os.path.join(ROOT, "octo.py")],
        input=stdin_text,
        capture_output=True,
        text=True,
        cwd=ROOT,
        env=env,
        timeout=60,
    )
    return proc.stdout


def main():
    print("raqm (Myanmar shaping) available:", features.check("raqm"))
    os.makedirs(OUT_DIR, exist_ok=True)
    for name, stdin_text in SCENARIOS.items():
        out_path = os.path.join(OUT_DIR, name)
        text = run_scenario(stdin_text)
        path, size = render(text, out_path)
        print("wrote %s  (%dx%d, %d lines)" % (path, size[0], size[1], len(text.splitlines())))


if __name__ == "__main__":
    main()
