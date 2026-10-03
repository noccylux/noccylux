#!/usr/bin/env python3
"""Render the synthwave banner and GitHub stat cards used by the profile README.

    python scripts/render_profile.py            # fetch stats with $GITHUB_TOKEN and render everything
    python scripts/render_profile.py --sample   # render with sample numbers, no network

Text is converted to outlines, so the SVGs look identical on every OS and
need no external service at view time. Requires `fonttools`.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import random
import urllib.request
from html import escape
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
FONTS = Path(__file__).resolve().parent / "fonts"

# ---- profile content ---------------------------------------------------------
LOGIN = "noccylux"
NAME = "BOYANG HAN"
TAGLINE = "QUANTITATIVE RESEARCH · MACHINE LEARNING"
PROMPT = "building tools for alpha research"
# Notebook outputs and markup inflate byte counts without saying much about the code.
EXCLUDED_LANGUAGES = {"Jupyter Notebook", "HTML", "CSS", "TeX", "Makefile", "CMake", "Batchfile"}

# ---- synthwave '84 inspired palette -----------------------------------------
INK = "#f4eefa"
MUTED = "#a59bc0"
PINK = "#f92aad"
CYAN = "#36f9f6"
YELLOW = "#fede5d"
ORANGE = "#ff8b39"
PURPLE = "#b98cff"
GREEN = "#72f1b8"
LANG_COLORS = [PINK, CYAN, YELLOW, ORANGE, PURPLE, GREEN]
OTHER_COLOR = "#6b5f86"


# ---- text as outlines --------------------------------------------------------
class Font:
    """Draws text as <use> references to glyph outlines collected in <defs>."""

    def __init__(self, filename: str, key: str):
        self.tt = TTFont(FONTS / filename)
        self.glyph_set = self.tt.getGlyphSet()
        self.cmap = self.tt.getBestCmap()
        self.hmtx = self.tt["hmtx"]
        self.upm = self.tt["head"].unitsPerEm
        self.cap_height = self.tt["OS/2"].sCapHeight
        self.key = key
        self.used: dict[str, str] = {}

    def reset(self) -> None:
        self.used = {}

    def _glyphs(self, text: str) -> list[str]:
        return [self.cmap.get(ord(c), ".notdef") for c in text]

    def width(self, text: str, size: float, tracking: float = 0.0) -> float:
        names = self._glyphs(text)
        units = sum(self.hmtx[n][0] for n in names) + tracking * self.upm * max(len(names) - 1, 0)
        return units * size / self.upm

    def text(self, text: str, x: float, y: float, size: float, fill: str,
             anchor: str = "start", tracking: float = 0.0, attrs: str = "") -> str:
        width = self.width(text, size, tracking)
        x -= {"start": 0, "middle": width / 2, "end": width}[anchor]
        scale = size / self.upm
        uses, cursor = [], 0.0
        for name in self._glyphs(text):
            if name not in self.used:
                pen = SVGPathPen(self.glyph_set)
                self.glyph_set[name].draw(pen)
                self.used[name] = pen.getCommands()
            if self.used[name]:
                uses.append(f'<use xlink:href="#{self.key}-{name}" x="{cursor:g}"/>')
            cursor += self.hmtx[name][0] + tracking * self.upm
        return (f'<g transform="translate({x:.2f} {y:.2f}) scale({scale:.5f} {-scale:.5f})" '
                f'fill="{fill}"{attrs}>{"".join(uses)}</g>')

    def defs(self) -> str:
        return "".join(f'<path id="{self.key}-{n}" d="{d}"/>' for n, d in self.used.items() if d)


DISPLAY = Font("Orbitron-Bold.ttf", "d")
MONO = Font("JetBrainsMono-Regular.ttf", "m")
ALL_FONTS = (DISPLAY, MONO)


def svg_document(width: int, height: int, title: str, defs: str, body: str) -> str:
    glyphs = "".join(f.defs() for f in ALL_FONTS)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">'
            f'<title>{escape(title)}</title><defs>{glyphs}{defs}</defs>{body}</svg>\n')


def start_document() -> None:
    for f in ALL_FONTS:
        f.reset()


# ---- banner ------------------------------------------------------------------
def render_banner() -> str:
    start_document()
    W, H = 1280, 320
    horizon = 228
    sun_x, sun_r = 1010, 118

    rng = random.Random(7)
    stars = []
    for _ in range(46):
        sx, sy = rng.uniform(16, W - 16), rng.uniform(12, horizon - 30)
        if (sx - sun_x) ** 2 + (sy - horizon) ** 2 < (sun_r + 30) ** 2:
            continue
        stars.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="{rng.choice((0.7, 1, 1, 1.4)):g}" '
                     f'fill="{INK}" opacity="{rng.uniform(0.25, 0.75):.2f}"/>')

    # Sun stripes widen toward the horizon.
    stripes = []
    y, gap = horizon - 58, 2.5
    while y < horizon:
        stripes.append(f'<rect x="{sun_x - sun_r - 2}" y="{y:.1f}" width="{2 * sun_r + 4}" height="{gap:.1f}" fill="#000"/>')
        y += gap + 10
        gap += 1.6

    # Perspective floor grid converging on the sun.
    grid = []
    depth = H - horizon
    for i in range(1, 9):
        gy = horizon + depth * (i / 8) ** 1.8
        grid.append(f'<line x1="0" y1="{gy:.1f}" x2="{W}" y2="{gy:.1f}"/>')
    for i in range(-16, 17):
        grid.append(f'<line x1="{sun_x + i * 14}" y1="{horizon}" x2="{sun_x + i * 150}" y2="{H}"/>')

    ridge = [(0, horizon), (0, 216), (50, 210), (110, 220), (170, 212), (240, 222), (300, 216), (380, horizon)]
    ridge2 = [(W - 170, horizon), (W - 120, 214), (W - 70, 220), (W - 30, 206), (W, 212), (W, horizon)]
    poly = lambda pts: " ".join(f"{a},{b}" for a, b in pts)

    defs = f"""
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#0b0420"/><stop offset="0.6" stop-color="#1c0b3a"/><stop offset="1" stop-color="#3b1158"/>
</linearGradient>
<linearGradient id="floor" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#1a0733"/><stop offset="1" stop-color="#0b0420"/>
</linearGradient>
<linearGradient id="sun" gradientUnits="userSpaceOnUse" x1="0" y1="{horizon - sun_r}" x2="0" y2="{horizon}">
  <stop offset="0" stop-color="{YELLOW}"/><stop offset="0.45" stop-color="{ORANGE}"/><stop offset="1" stop-color="{PINK}"/>
</linearGradient>
<linearGradient id="gridfade" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#fff" stop-opacity="0.15"/><stop offset="1" stop-color="#fff" stop-opacity="1"/>
</linearGradient>
<linearGradient id="name" gradientUnits="userSpaceOnUse" x1="0" y1="{DISPLAY.cap_height}" x2="0" y2="0">
  <stop offset="0" stop-color="#ffffff"/><stop offset="0.55" stop-color="#ffd6f1"/><stop offset="1" stop-color="{PINK}"/>
</linearGradient>
<mask id="sunmask"><rect x="0" y="0" width="{W}" height="{H}" fill="#fff"/>{"".join(stripes)}</mask>
<mask id="gridmask"><rect x="0" y="{horizon}" width="{W}" height="{depth}" fill="url(#gridfade)"/></mask>
<clipPath id="frame"><rect width="{W}" height="{H}" rx="16"/></clipPath>
<clipPath id="above"><rect width="{W}" height="{horizon}"/></clipPath>
<filter id="glow" x="-20%" y="-50%" width="140%" height="200%">
  <feGaussianBlur stdDeviation="5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter>
<filter id="haze" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="26"/></filter>
"""

    cursor_x = 76 + MONO.width("> " + PROMPT, 17) + 6
    body = f"""
<g clip-path="url(#frame)">
  <rect width="{W}" height="{H}" fill="url(#sky)"/>
  {"".join(stars)}
  <g clip-path="url(#above)">
    <circle cx="{sun_x}" cy="{horizon}" r="{sun_r + 8}" fill="{PINK}" opacity="0.45" filter="url(#haze)"/>
    <circle cx="{sun_x}" cy="{horizon}" r="{sun_r}" fill="url(#sun)" mask="url(#sunmask)"/>
  </g>
  <polygon points="{poly(ridge)}" fill="#14062a" stroke="{PURPLE}" stroke-opacity="0.35" stroke-width="1.2"/>
  <polygon points="{poly(ridge2)}" fill="#14062a" stroke="{PURPLE}" stroke-opacity="0.35" stroke-width="1.2"/>
  <rect y="{horizon}" width="{W}" height="{depth}" fill="url(#floor)"/>
  <g mask="url(#gridmask)" stroke="{PINK}" stroke-width="1.2" stroke-opacity="0.6">{"".join(grid)}</g>
  <line x1="0" y1="{horizon}" x2="{W}" y2="{horizon}" stroke="{PINK}" stroke-width="2" filter="url(#glow)"/>

  {DISPLAY.text(NAME, 72, 116, 60, "url(#name)", tracking=0.06, attrs=' filter="url(#glow)"')}
  {MONO.text(TAGLINE, 76, 156, 19, CYAN, tracking=0.08)}
  {MONO.text(">", 76, 188, 17, PINK)}
  {MONO.text(PROMPT, 76 + MONO.width("> ", 17), 188, 17, MUTED)}
  <rect x="{cursor_x:.1f}" y="174" width="9" height="17" fill="{CYAN}">
    <animate attributeName="opacity" values="1;0;1" keyTimes="0;0.5;1" dur="1.2s" calcMode="discrete" repeatCount="indefinite"/>
  </rect>
</g>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="16" fill="none" stroke="{PURPLE}" stroke-opacity="0.35"/>
"""
    return svg_document(W, H, f"{NAME.title()} — {TAGLINE.title()}", defs, body)


# ---- stat cards --------------------------------------------------------------
CARD_W, CARD_H = 480, 230


def card_frame(title: str, note: str) -> tuple[str, str]:
    defs = f"""
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#1b1330"/><stop offset="1" stop-color="#2a1745"/>
</linearGradient>
<linearGradient id="edge" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="{PINK}" stop-opacity="0.55"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0.35"/>
</linearGradient>
<linearGradient id="rule" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="{PINK}"/><stop offset="0.6" stop-color="{PINK}" stop-opacity="0.15"/><stop offset="1" stop-color="{PINK}" stop-opacity="0"/>
</linearGradient>
"""
    body = (f'<rect x="0.5" y="0.5" width="{CARD_W - 1}" height="{CARD_H - 1}" rx="10" fill="url(#bg)" stroke="url(#edge)"/>'
            + DISPLAY.text(title, 24, 38, 14, INK, tracking=0.12)
            + MONO.text(note, CARD_W - 24, 38, 11, MUTED, anchor="end")
            + f'<rect x="24" y="50" width="{CARD_W - 48}" height="1.2" fill="url(#rule)"/>')
    return defs, body


def compact(n: int) -> str:
    if n >= 10_000:
        return f"{n / 1000:.1f}k".replace(".0k", "k")
    return f"{n:,}"


def render_stats(stats: dict) -> str:
    start_document()
    defs, body = card_frame("GITHUB ACTIVITY", "last 12 months")
    tiles = [
        (compact(stats["contributions"]), "CONTRIBUTIONS", PINK),
        (compact(stats["commits"]), "COMMITS", CYAN),
        (compact(stats["active_days"]), "ACTIVE DAYS", YELLOW),
        (f'{stats["longest_streak"]}d', "LONGEST STREAK", ORANGE),
        (compact(stats["repositories"]), "REPOSITORIES", PURPLE),
        (str(stats["since"]), "ON GITHUB SINCE", GREEN),
    ]
    col_w = (CARD_W - 48) / 3
    for i, (value, label, color) in enumerate(tiles):
        x = 24 + (i % 3) * col_w
        y = 92 + (i // 3) * 54
        body += DISPLAY.text(value, x, y, 22, color)
        body += MONO.text(label, x, y + 17, 10, MUTED, tracking=0.06)

    weeks = stats["weekly"][-52:]
    if weeks:
        top, base = 180, 210
        peak = max(max(weeks), 1)
        step = (CARD_W - 48) / len(weeks)
        bars = []
        for i, count in enumerate(weeks):
            h = 2 + (base - top - 2) * count / peak if count else 1
            bars.append(f'<rect x="{24 + i * step:.2f}" y="{base - h:.2f}" width="{step * 0.62:.2f}" height="{h:.2f}" rx="1"/>')
        defs += f"""
<linearGradient id="bars" gradientUnits="userSpaceOnUse" x1="0" y1="{top}" x2="0" y2="{base}">
  <stop offset="0" stop-color="{CYAN}"/><stop offset="1" stop-color="{PINK}"/>
</linearGradient>"""
        body += f'<g fill="url(#bars)" opacity="0.85">{"".join(bars)}</g>'
        body += f'<line x1="24" y1="{base + 0.5}" x2="{CARD_W - 24}" y2="{base + 0.5}" stroke="{PINK}" stroke-opacity="0.35"/>'
    return svg_document(CARD_W, CARD_H, "GitHub activity over the last 12 months", defs, body)


def render_languages(languages: dict[str, int]) -> str:
    start_document()
    defs, body = card_frame("TOP LANGUAGES", "by code size")
    ranked = sorted(((n, b) for n, b in languages.items() if n not in EXCLUDED_LANGUAGES and b > 0),
                    key=lambda item: item[1], reverse=True)
    total = sum(b for _, b in ranked) or 1
    shown = ranked[:6] if len(ranked) <= 6 else ranked[:5]
    rest = total - sum(b for _, b in shown)
    entries = [(n, b, LANG_COLORS[i]) for i, (n, b) in enumerate(shown)]
    if rest > 0:
        entries.append(("Other", rest, OTHER_COLOR))

    bar_x, bar_w, bar_y = 24, CARD_W - 48, 74
    defs += f'<clipPath id="bar"><rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="10" rx="5"/></clipPath>'
    segments, x = [], float(bar_x)
    for _, b, color in entries:
        w = bar_w * b / total
        segments.append(f'<rect x="{x:.2f}" y="{bar_y}" width="{w + 0.5:.2f}" height="10" fill="{color}"/>')
        x += w
    body += f'<g clip-path="url(#bar)"><rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="10" fill="#3a2d55"/>{"".join(segments)}</g>'

    col_w = bar_w / 2
    for i, (name, b, color) in enumerate(entries):
        cx = bar_x + (i % 2) * col_w
        cy = 126 + (i // 2) * 36
        body += f'<circle cx="{cx + 5}" cy="{cy - 4.5}" r="5" fill="{color}"/>'
        body += MONO.text(name, cx + 18, cy, 13, INK)
        body += MONO.text(f"{100 * b / total:.1f}%", cx + col_w - 22, cy, 12, MUTED, anchor="end")
    if not entries:
        body += MONO.text("no language data yet", CARD_W / 2, 140, 12, MUTED, anchor="middle")
    return svg_document(CARD_W, CARD_H, "Most used languages by code size", defs, body)


# ---- data --------------------------------------------------------------------
QUERY = """
query($login: String!, $after: String) {
  user(login: $login) {
    createdAt
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      contributionCalendar { totalContributions weeks { contributionDays { contributionCount } } }
    }
    repositories(first: 100, after: $after, ownerAffiliations: OWNER, isFork: false) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes { languages(first: 20) { edges { size node { name } } } }
    }
  }
}
"""


def graphql(token: str, variables: dict) -> dict:
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json",
                 "User-Agent": f"{LOGIN}-profile-cards"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return payload["data"]["user"]


def fetch_stats(token: str) -> tuple[dict, dict[str, int]]:
    languages: dict[str, int] = {}
    after, user = None, None
    while True:
        page = graphql(token, {"login": LOGIN, "after": after})
        user = user or page
        for repo in page["repositories"]["nodes"]:
            for edge in repo["languages"]["edges"]:
                name = edge["node"]["name"]
                languages[name] = languages.get(name, 0) + edge["size"]
        info = page["repositories"]["pageInfo"]
        if not info["hasNextPage"]:
            break
        after = info["endCursor"]

    collection = user["contributionsCollection"]
    calendar = collection["contributionCalendar"]
    days = [d["contributionCount"] for w in calendar["weeks"] for d in w["contributionDays"]]
    longest = run = 0
    for count in days:
        run = run + 1 if count else 0
        longest = max(longest, run)
    stats = {
        "contributions": calendar["totalContributions"],
        "commits": collection["totalCommitContributions"],
        "active_days": sum(1 for c in days if c),
        "longest_streak": longest,
        "repositories": user["repositories"]["totalCount"],
        "since": dt.datetime.fromisoformat(user["createdAt"].replace("Z", "+00:00")).year,
        "weekly": [sum(d["contributionCount"] for d in w["contributionDays"]) for w in calendar["weeks"]],
    }
    return stats, languages


def sample_stats() -> tuple[dict, dict[str, int]]:
    rng = random.Random(3)
    weekly = [max(0, int(rng.gauss(14, 9))) for _ in range(52)]
    stats = {"contributions": sum(weekly), "commits": int(sum(weekly) * 0.8), "active_days": 186,
             "longest_streak": 23, "repositories": 30, "since": 2018, "weekly": weekly}
    languages = {"Python": 2_400_000, "C++": 380_000, "Cuda": 120_000, "Jupyter Notebook": 9_000_000,
                 "JavaScript": 90_000, "Shell": 40_000, "C": 30_000, "TypeScript": 20_000}
    return stats, languages


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sample", action="store_true", help="render with sample numbers instead of fetching")
    parser.add_argument("--out", type=Path, default=ASSETS, help="output directory (default: assets/)")
    args = parser.parse_args()

    if args.sample:
        stats, languages = sample_stats()
    else:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            parser.error("GITHUB_TOKEN is not set (use --sample to render without network)")
        stats, languages = fetch_stats(token)

    args.out.mkdir(parents=True, exist_ok=True)
    outputs = {"banner.svg": render_banner(), "stats.svg": render_stats(stats),
               "languages.svg": render_languages(languages)}
    for filename, svg in outputs.items():
        (args.out / filename).write_text(svg, encoding="utf-8")
        print(f"wrote {args.out / filename} ({len(svg) / 1024:.1f} KiB)")


if __name__ == "__main__":
    main()
