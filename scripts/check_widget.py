#!/usr/bin/env python3
"""
Telegram HTML Widget (Bot API 10.4) — Official Profile 1 Linter & Size Checker

Checks:
1. Raw UTF-8 size <= 32,768 bytes and no NUL (U+0000) characters.
2. Exact server-side zlib level 9 compressed size <= 4,096 bytes.
3. Widget Profile 1 compliance (detects forbidden HTML tags, stripped CSS properties,
   forbidden network/DOM APIs, and heavy-element opacity traps).

Usage:
  python check_widget.py <widget1.html> [widget2.html ...]
"""

import glob
import gzip
import os
import re
import sys
import zlib

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

MAX_RAW_BYTES = 32768
MAX_ZLIB_BYTES = 4096

FORBIDDEN_HTML_TAGS = [
    "input", "select", "option", "optgroup", "textarea", "form", "label",
    "fieldset", "legend", "datalist", "output", "progress", "meter",
    "dialog", "audio", "video", "source", "track", "iframe", "frame",
    "object", "embed", "portal", "template", "math", "ruby",
    "clipPath", "mask", "pattern", "marker", "foreignObject", "animate",
    "animateTransform", "animateMotion"
]

FORBIDDEN_CSS_PATTERNS = [
    (r"overflow(?:-[xy])?\s*:\s*(?:auto|scroll)\b", "overflow: auto/scroll is converted to hidden (nothing scrolls inside a widget)"),
    (r"position\s*:\s*sticky\b", "position: sticky is converted to relative"),
    (r"\b\d+(?:\.\d+)?(?:d?vh|svh|lvh|vb)\b", "height-relative units (vh/dvh/svh/vb) are stripped in Profile 1"),
    (r"@font-face\b", "@font-face is stripped in Profile 1 (use system-ui / generic families)"),
    (r"@import\b", "@import is stripped in Profile 1"),
    (r"@container\b", "@container queries are stripped in Profile 1"),
    (r":has\s*\(", ":has() selector is stripped in Profile 1"),
    (r"\b(?:margin|padding|inset)-(?:inline|block)", "CSS logical properties are stripped in Profile 1"),
    (r"\bclip-path\s*:", "clip-path is stripped in Profile 1"),
    (r"\btext-shadow\s*:", "text-shadow is stripped in Profile 1"),
    (r"-webkit-line-clamp\s*:", "-webkit-line-clamp is stripped in Profile 1"),
    (r"\b(?:oklch|oklab|lch|lab|hwb|color-mix)\s*\(", "modern color spaces (oklch/color-mix) are stripped in Profile 1"),
]

FORBIDDEN_JS_PATTERNS = [
    (r"\bfetch\s*\(", "fetch() throws NetworkDisabledError in QuickJS sandbox"),
    (r"\bXMLHttpRequest\b", "XMLHttpRequest throws NetworkDisabledError in QuickJS sandbox"),
    (r"\bWebSocket\b", "WebSocket throws NetworkDisabledError in QuickJS sandbox"),
    (r"\bEventSource\b", "EventSource throws NetworkDisabledError in QuickJS sandbox"),
    (r"\bnavigator\.clipboard\b", "navigator.clipboard is unavailable; use TelegramWidget.copyText(text)"),
    (r"\b(?:alert|confirm|prompt)\s*\(", "alert/confirm/prompt are disabled in QuickJS sandbox"),
    (r"\b(?:touchstart|touchmove|touchend)\b", "touch events are stripped on touch clients; use pointerdown/pointermove/pointerup"),
    (r"<img[^>]+src=['\"]https?://", "external <img src='https://...'> is never loaded; use inline <svg> or data: PNG/JPEG/WebP"),
    (r"<img[^>]+src=['\"]data:image/svg\+xml", "<img src='data:image/svg+xml'> is stripped in Profile 1; use inline <svg> instead"),
]


def check_file(filepath: str) -> bool:
    if not os.path.isfile(filepath):
        print(f"[ERROR] File not found: {filepath}")
        return False

    with open(filepath, "rb") as f:
        raw_bytes = f.read()

    errors = []
    warnings = []

    # 1. Check UTF-8 & NUL
    try:
        text = raw_bytes.decode("utf-8")
        if "\x00" in text:
            errors.append("Contains NUL character (U+0000) -> INPUT_MEDIA_WIDGET_HTML_INVALID")
    except UnicodeDecodeError as e:
        print(f"[FAIL] {filepath}: Invalid UTF-8 encoding ({e})")
        return False

    # 2. Check Raw & Zlib Level 9 sizes
    raw_len = len(raw_bytes)
    zlib_len = len(zlib.compress(raw_bytes, 9))
    gzip_len = len(gzip.compress(raw_bytes, compresslevel=9))

    if raw_len == 0 or raw_len > MAX_RAW_BYTES:
        errors.append(f"Raw UTF-8 size {raw_len} B exceeds limit of {MAX_RAW_BYTES} B")
    if zlib_len > MAX_ZLIB_BYTES:
        errors.append(f"Compressed zlib(9) size {zlib_len} B exceeds limit of {MAX_ZLIB_BYTES} B")
    elif zlib_len > 3900:
        warnings.append(f"Compressed zlib(9) size {zlib_len} B is close to 4096 B limit (< 200 B margin)")

    # 3. Check forbidden HTML tags
    for tag in FORBIDDEN_HTML_TAGS:
        pattern = rf"<{tag}(?:\s|>|/)"
        if re.search(pattern, text, re.IGNORECASE):
            errors.append(f"Forbidden HTML/SVG tag <{tag}> (silently removed by Widget Profile 1)")

    # 4. Check forbidden CSS patterns
    for pat, msg in FORBIDDEN_CSS_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            errors.append(f"Profile 1 CSS violation: {msg}")

    # 5. Check opacity usage (Heavy Elements trap: max 16 elements with opacity < 1)
    opacity_matches = re.findall(r"opacity\s*:\s*(0?\.\d+)", text, re.IGNORECASE)
    if opacity_matches:
        warnings.append(
            f"Found {len(opacity_matches)} CSS rule(s) with opacity < 1 ({', '.join(opacity_matches)}). "
            "Profile 1 stops the widget if >16 elements on screen have opacity < 1 or blurred box-shadow. "
            "Prefer var(--tg-theme-hint-color) or rgba() instead of opacity."
        )

    # 6. Check forbidden JS & asset patterns
    for pat, msg in FORBIDDEN_JS_PATTERNS:
        if re.search(pat, text):
            errors.append(f"Profile 1 JS/Asset violation: {msg}")

    status = "PASS" if not errors else "FAIL"
    name = os.path.basename(filepath)
    print(f"[{status}] {name:26s} | Raw: {raw_len:5d}/{MAX_RAW_BYTES} B | Zlib9: {zlib_len:4d}/{MAX_ZLIB_BYTES} B (Gzip9: {gzip_len:4d} B)")

    for err in errors:
        print(f"   ❌ ERROR:   {err}")
    for warn in warnings:
        print(f"   ⚠️ WARNING: {warn}")

    return len(errors) == 0


def main():
    args = sys.argv[1:]
    if not args:
        args = sorted(glob.glob("widget_*.html") + glob.glob("boilerplate.html"))
    if not args:
        print("Usage: python check_widget.py <widget.html> [...]")
        sys.exit(1)

    all_passed = True
    for path in args:
        if not check_file(path):
            all_passed = False

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
