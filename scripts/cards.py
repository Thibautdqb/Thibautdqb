"""Draw the generated images of the profile README (SVG, dark and light) from live data.

    GITHUB_TOKEN=$(gh auth token) python scripts/cards.py

Run daily by .github/workflows/cards.yml. Standard library only; every number comes from the GitHub or
PyPI API. Draws: the project cards (elessar, volatility-engine), the elessar badges and the ridgeline divider.
"""

from __future__ import annotations

import html
import json
import math
import os
import random
import re
import urllib.error
import urllib.request
from pathlib import Path

USER = "Thibautdqb"
OUT = Path(__file__).resolve().parent.parent / "assets" / "generated"
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
SANS = "Inter, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

# the palette of the T-Rex banner: night, emerald to cyan
THEMES = {
    "dark": {"panel": "#0d1117", "line": "#222a36", "ink": "#f0f3f6", "text": "#c9d1d9", "muted": "#8b949e",
             "acc0": "#34d399", "acc1": "#22d3ee",
             "badge": "#161b22", "badge_text": "#c9d1d9", "badge_value": "#0d1117"},
    "light": {"panel": "#ffffff", "line": "#d0d7de", "ink": "#1f2328", "text": "#30363d", "muted": "#59636e",
              "acc0": "#059669", "acc1": "#0891b2",
              "badge": "#eaeef2", "badge_text": "#30363d", "badge_value": "#ffffff"},
}


def get(url: str, graphql: dict | None = None) -> dict | list | None:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-cards"}
    if TOKEN and "api.github.com" in url:
        headers["Authorization"] = f"Bearer {TOKEN}"
    data = json.dumps(graphql).encode() if graphql is not None else None
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=headers), timeout=30) as r:
            return json.load(r)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None


def esc(s: object) -> str:
    return html.escape(str(s), quote=True)


def gradient(t: dict) -> str:
    return (f'<defs><linearGradient id="acc" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{t["acc0"]}"/>'
            f'<stop offset="1" stop-color="{t["acc1"]}"/></linearGradient>'
            '<filter id="glow" x="-200%" y="-200%" width="500%" height="500%"><feGaussianBlur stdDeviation="2.5" result="b"/>'
            '<feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>')


def card(t: dict, label: str, name: str, tagline: str, prompt: str, code: str, right: str, status: str,
         live: bool, dot_after: bool = False) -> str:
    """One project: label and status, name and tagline, a command line, a short line of facts."""
    w, h = 820, 176
    dot = (f'<circle cx="{w - 34}" cy="36" r="4" fill="{t["acc0"] if live else t["muted"]}">'
           + ('<animate attributeName="opacity" values="1;0.3;1" dur="2.6s" repeatCount="indefinite"/>' if live else "")
           + "</circle>")
    # width of the name in a bold sans at 40px: narrow letters take about half the room of the others
    name_w = 26 + sum(10.5 if ch in "iljtfr-.' " else 22 for ch in name) + (10 if dot_after else 0) + 24
    neon = f'<tspan fill="{t["acc0"]}" filter="url(#glow)">.</tspan>' if dot_after else ""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{esc(name)}: {esc(tagline)}">
  {gradient(t)}
  <rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="14" fill="{t['panel']}" stroke="{t['line']}"/>
  <rect x="28" y="0.5" width="56" height="2" rx="1" fill="url(#acc)"/>
  <text x="28" y="40" fill="{t['muted']}" font-family="{MONO}" font-size="11" letter-spacing="2">{esc(label.upper())}</text>
  {dot}
  <text x="{w - 48}" y="40" fill="{t['muted']}" font-family="{MONO}" font-size="11" letter-spacing="1.5" text-anchor="end">{esc(status)}</text>
  <text x="26" y="92" fill="{t['ink']}" font-family="{SANS}" font-size="40" font-weight="700" letter-spacing="-1.2">{esc(name)}{neon}</text>
  <text x="{name_w}" y="91" fill="url(#acc)" font-family="{SANS}" font-size="17" font-weight="600">{esc(tagline)}</text>
  <rect x="28" y="116" width="{int((len(prompt) + len(code) + 1) * 8.45 + 46)}" height="36" rx="8" fill="none" stroke="{t['line']}"/>
  <text x="42" y="139" font-family="{MONO}" font-size="14"><tspan fill="{t['acc0']}">{esc(prompt)}</tspan><tspan fill="{t['ink']}"> {esc(code)}</tspan><tspan fill="{t['acc0']}"> ▍<animate attributeName="opacity" values="1;0;1" dur="1.1s" repeatCount="indefinite"/></tspan></text>
  <text x="{w - 28}" y="139" fill="{t['muted']}" font-family="{MONO}" font-size="12" text-anchor="end">{esc(right)}</text>
</svg>
"""


def elessar(t: dict) -> str:
    info = (get("https://pypi.org/pypi/elessar/json") or {}).get("info") or {}
    stars = (get(f"https://api.github.com/repos/{USER}/elessar") or {}).get("stargazers_count", 0)
    version = f"v{info['version']} · " if info.get("version") else ""
    return card(t, "Open source · live on PyPI", "elessar", "automated EDA and data quality for pandas",
                "$", "pip install elessar", "python 3.10+ · linux · macos · windows", f"{version}★ {stars}", True,
                dot_after=True)


def volatility(t: dict) -> str:
    repo = get(f"https://api.github.com/repos/{USER}/volatility-engine") or {}
    return card(t, "Research", "volatility-engine", "5-minute volatility forecasts",
                "$", "git clone github.com/Thibautdqb/volatility-engine", "BTC · ETH · Deribit",
                f"★ {repo.get('stargazers_count', 0)} · updated {(repo.get('pushed_at') or '')[:10]}", True)


def badge(t: dict, label: str, value: str, color: str) -> str:
    lw, vw = int(len(label) * 6.6 + 16), int(len(value) * 6.6 + 16)
    w = lw + vw
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} 22" width="{w}" height="22" role="img" '
            f'aria-label="{esc(label)}: {esc(value)}"><rect width="{w}" height="22" rx="5" fill="{t["badge"]}"/>'
            f'<rect x="{lw}" width="{vw}" height="22" rx="5" fill="{color}"/><rect x="{lw}" width="6" height="22" fill="{color}"/>'
            f'<text x="{lw / 2}" y="15" fill="{t["badge_text"]}" font-family="{MONO}" font-size="11" text-anchor="middle">{esc(label)}</text>'
            f'<text x="{lw + vw / 2}" y="15" fill="{t["badge_value"]}" font-family="{MONO}" font-size="11" font-weight="700" '
            f'text-anchor="middle">{esc(value)}</text></svg>\n')


def badges(t: dict) -> dict[str, str]:
    info = (get("https://pypi.org/pypi/elessar/json") or {}).get("info") or {}
    versions = sorted({c.rsplit("::", 1)[-1].strip() for c in info.get("classifiers", [])
                       if re.fullmatch(r"Programming Language :: Python :: 3\.\d+", c)}, key=lambda v: int(v.split(".")[1]))
    runs = (get(f"https://api.github.com/repos/{USER}/elessar/actions/workflows/ci.yml/runs?branch=main&status=completed&per_page=1")
            or {}).get("workflow_runs") or []
    passing = bool(runs) and runs[0].get("conclusion") == "success"
    return {"badge-pypi": badge(t, "pypi", f"v{info.get('version', '?')}", t["acc0"]),
            "badge-python": badge(t, "python", f"{versions[0]} – {versions[-1]}" if versions else "3", t["acc1"]),
            "badge-tests": badge(t, "tests", "passing" if passing else "failing", t["acc0"] if passing else "#f85149")}


def ridges(seed: int, phase: float, n: int, w: float, top: float, step: float) -> list[str]:
    """Gentle ridgelines across the width, flat at both ends."""
    rng = random.Random(seed)
    out = []
    for i in range(n):
        bumps = [(rng.uniform(0.15 * w, 0.85 * w), rng.uniform(30, 90), rng.uniform(0.2, 1.0)) for _ in range(3)]
        pts = []
        for k in range(120):
            x = w * k / 119
            edge = min(1.0, x / 120) * min(1.0, (w - x) / 120)
            y = sum(a * math.exp(-((x - c - 20 * math.sin(phase + i)) ** 2) / (2 * s * s)) for c, s, a in bumps)
            pts.append(f"{x:.0f},{top + i * step - 22 * edge * y - edge * math.sin(x / 11 + i + phase):.1f}")
        out.append("M" + " L".join(pts))
    return out


def divider(t: dict) -> str:
    w = 1200
    a, b = ridges(11, 0.0, 4, w, 30, 6), ridges(11, 1.6, 4, w, 30, 6)
    ys = [float(v) for p in a + b for v in re.findall(r",(-?[\d.]+)", p)]
    top, h = min(ys) - 6, max(ys) - min(ys) + 12  # the frame follows both shapes of the animation, plus the stroke
    fade = (f'<defs><linearGradient id="fade" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{t["acc0"]}" stop-opacity="0"/>'
            f'<stop offset="0.25" stop-color="{t["acc0"]}"/><stop offset="0.75" stop-color="{t["acc1"]}"/>'
            f'<stop offset="1" stop-color="{t["acc1"]}" stop-opacity="0"/></linearGradient></defs>')
    lines = "".join(f'<path d="{p}" fill="none" stroke="url(#fade)" stroke-opacity="{0.3 + 0.2 * i:.2f}" stroke-width="1.2">'
                    f'<animate attributeName="d" values="{p};{q};{p}" dur="{16 + i}s" repeatCount="indefinite"/></path>'
                    for i, (p, q) in enumerate(zip(a, b)))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 {top:.1f} {w} {h:.1f}" width="{w}" height="{h:.0f}" '
            f'role="img" aria-label="">{fade}{lines}</svg>\n')


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.svg"):
        old.unlink()
    for theme, t in THEMES.items():
        suffix = "" if theme == "dark" else "-light"
        for name, draw in (("elessar", elessar), ("volatility-engine", volatility), ("divider", divider)):
            (OUT / f"{name}{suffix}.svg").write_text(draw(t), encoding="utf-8")
        for name, svg in badges(t).items():
            (OUT / f"{name}{suffix}.svg").write_text(svg, encoding="utf-8")
    print("wrote", sorted(p.name for p in OUT.glob("*.svg")))


if __name__ == "__main__":
    main()
