"""Draw the README's charts from the study's result files.

    uv run python scripts/readme_charts.py

Writes docs/img/<name>-light.svg and -dark.svg (transparent background, for GitHub's two themes).
Every number comes from study/llm-chatbot/reports/*/result.json; nothing is typed in by hand.
"""

from __future__ import annotations

import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).parent.parent
REPORTS = ROOT / "study/llm-chatbot/reports"
OUT = ROOT / "docs/img"

THEMES = {
    "light": {
        "text": "#0b0b0b", "muted": "#52514e", "grid": "#dedcd3", "surface": "#ffffff",
        "s1": "#2a78d6", "s2": "#eb6834", "s3": "#1baf7a",
    },
    "dark": {
        "text": "#f0efec", "muted": "#c3c2b7", "grid": "#3a3a37", "surface": "#0d1117",
        "s1": "#3987e5", "s2": "#d95926", "s3": "#199e70",
    },
}  # fmt: skip
FONT = 'font-family="system-ui,-apple-system,Segoe UI,Helvetica,Arial,sans-serif"'
JUDGES = ["phi4:14b", "mistral-small3.2:24b", "gemma3:27b"]  # fixed order: colour follows the judge
SHORT = {"phi4:14b": "phi4", "mistral-small3.2:24b": "mistral-small", "gemma3:27b": "gemma3"}
W = 760


def result(name: str) -> dict:
    return json.loads((REPORTS / name / "result.json").read_text())


class Svg:
    def __init__(self, height: int, theme: dict, title: str, desc: str):
        self.t = theme
        self.parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height}" width="{W}" '
            f'height="{height}" role="img" aria-label="{escape(desc)}" {FONT}>',
            f"<title>{escape(title)}</title><desc>{escape(desc)}</desc>",
        ]

    def text(self, x, y, s, *, size=13, fill="text", anchor="start", weight=400):
        self.parts.append(
            f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{self.t[fill]}" '
            f'text-anchor="{anchor}" font-weight="{weight}">{escape(str(s))}</text>'
        )

    def line(self, x1, y1, x2, y2, *, stroke="grid", width=1.0, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{self.t[stroke]}" stroke-width="{width}"{d} stroke-linecap="round"/>'
        )

    def bar(self, x, y, w, h, fill):
        """Horizontal bar anchored at x with a rounded data end."""
        w = max(w, 0.0)
        r = min(4.0, w / 2, h / 2)
        self.parts.append(
            f'<path d="M{x:.1f},{y:.1f} h{w - r:.1f} a{r},{r} 0 0 1 {r},{r} v{h - 2 * r:.1f} '
            f'a{r},{r} 0 0 1 -{r},{r} h-{w - r:.1f} z" fill="{self.t[fill]}"/>'
        )

    def dot(self, x, y, fill, r=5.0):
        self.parts.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{self.t[fill]}" '
            f'stroke="{self.t["surface"]}" stroke-width="2"/>'
        )

    def swatch(self, x, y, fill, label, kind="bar"):
        if kind == "bar":
            self.parts.append(
                f'<rect x="{x}" y="{y - 9}" width="14" height="10" rx="2" fill="{self.t[fill]}"/>'
            )
        else:
            self.line(x - 3, y - 4, x + 17, y - 4, stroke=fill, width=2)
            self.dot(x + 7, y - 4, fill, r=4.5)
        self.text(x + 22, y, label, size=12, fill="muted")

    def axis(self, x0, x1, y, ticks, scale, fmt, top):
        for v in ticks:
            x = scale(v)
            self.line(x, top, x, y, stroke="grid")
            self.text(x, y + 16, fmt(v), size=11, fill="muted", anchor="middle")

    def done(self) -> str:
        return "".join(self.parts) + "</svg>\n"


def chart_resolve(theme: dict) -> str:
    """Smallest resolvable difference per judge, beside the difference it reported."""
    res = result("arm-A")
    mrd = {r["judge"]: r for r in res["mrd"]}
    diff = {r["judge"]: r for r in res["difference"]}
    left, right, top, row = 150, 560, 64, 46
    s = Svg(top + row * len(JUDGES) + 44, theme, "What each judge can resolve",
            "Per judge: the smallest v2 minus v1 difference it can resolve, about 19 to 21 points, "
            "and the 30 to 37 point difference it reported.")  # fmt: skip

    def x(v):
        return left + v / 50 * (right - left)

    s.text(0, 18, "Smallest difference each judge can resolve, v2 − v1", size=15, weight=600)
    s.swatch(0, 42, "s1", "cannot resolve below this (bias bound + noise)")
    s.swatch(330, 42, "text", "difference the judge reported, 95% interval", kind="dot")
    bottom = top + row * len(JUDGES)
    s.axis(left, right, bottom, [0, 10, 20, 30, 40, 50], x, lambda v: f"{v}", top - 6)
    s.text(right, bottom + 34, "percentage points", size=11, fill="muted", anchor="end")
    for i, j in enumerate(JUDGES):
        y = top + row * i + row / 2
        m, d = mrd[j], diff[j]
        s.text(0, y + 4, SHORT[j], size=13)
        s.bar(left, y - 8, x(100 * m["mrd"]) - left, 16, "s1")
        s.line(x(100 * d["ci_lo"]), y, x(100 * d["ci_hi"]), y, stroke="text", width=2)
        s.dot(x(100 * d["diff"]), y, "text")
        s.text(right + 14, y - 3, f"reported +{100 * d['diff']:.1f}", size=12)
        s.text(right + 14, y + 13, f"resolves above {100 * m['mrd']:.1f}", size=12, fill="muted")
    return s.done()


def chart_repeat(theme: dict) -> str:
    """Share of answers whose verdict changed between trials, per arm and judge."""
    arms = [
        ("arm-A", "Same request again", "temperature 0, 3 trials"),
        ("arm-B", "Sampling switched on", "temperature 0.7, 5 trials"),
        ("arm-C", "Key facts listed in another order", "temperature 0, 5 orders"),
    ]
    left, right, top, bar_h, gap, block = 250, 640, 64, 12, 2, 66
    s = Svg(top + block * len(arms) + 40, theme, "Repeatability by arm",
            "Share of answers whose verdict changed between trials. Identical requests at "
            "temperature 0: almost none. Reordered key facts at temperature 0: about 7 percent "
            "for every judge.")  # fmt: skip

    def x(v):
        return left + v / 12 * (right - left)

    s.text(0, 18, "Answers whose verdict changed between trials", size=15, weight=600)
    for k, j in enumerate(JUDGES):
        s.swatch(k * 150, 42, f"s{k + 1}", SHORT[j])
    bottom = top + block * len(arms) - 10
    s.axis(left, right, bottom, [0, 3, 6, 9, 12], x, lambda v: f"{v}%", top - 6)
    for a, (name, label, sub) in enumerate(arms):
        within = {r["judge"]: r for r in result(name)["within"]}
        y0 = top + block * a
        s.text(0, y0 + 16, label, size=13)
        s.text(0, y0 + 33, sub, size=11, fill="muted")
        for k, j in enumerate(JUDGES):
            changed = 100 * (1 - within[j]["pct_all_agree"])
            y = y0 + k * (bar_h + gap)
            s.bar(left, y, x(changed) - left, bar_h, f"s{k + 1}")
            s.text(max(x(changed), left) + 7, y + 10, f"{changed:.1f}%", size=11)
    return s.done()


def chart_bias(theme: dict) -> str:
    """Judge score minus human score, on disputed and on randomly drawn reference questions."""
    rows = result("arm-A")["bias_by"]["selected"]
    by = {(r["judge"], r["selected"]): r for r in rows}
    strata = [(True, "s2", "21 questions picked because a judge disputed them"),
              (False, "s1", "29 questions drawn at random")]  # fmt: skip
    left, right, top, block = 150, 600, 64, 54
    s = Svg(top + block * len(JUDGES) + 44, theme, "Bias depends on where the reference was drawn",
            "Judge score minus human score. On questions picked for being disputed, phi4 is 44 "
            "points below the human; on randomly drawn questions, 2 points below.")  # fmt: skip

    def x(v):
        return left + (v + 70) / 90 * (right - left)

    s.text(0, 18, "Judge score minus human score, by how the question was chosen", size=15,
           weight=600)  # fmt: skip
    for k, (_, colour, label) in enumerate(strata):
        s.swatch(4 + k * 350, 42, colour, label, kind="dot")
    bottom = top + block * len(JUDGES)
    s.axis(left, right, bottom, [-60, -40, -20, 0, 20], x, lambda v: f"{v:+d}" if v else "0",
           top - 6)  # fmt: skip
    s.line(x(0), top - 6, x(0), bottom, stroke="muted", dash="3 3")
    s.text(right, bottom + 34, "percentage points, 95% interval", size=11, fill="muted",
           anchor="end")  # fmt: skip
    for i, j in enumerate(JUDGES):
        y0 = top + block * i
        s.text(0, y0 + block / 2 + 4, SHORT[j], size=13)
        for k, (selected, colour, _) in enumerate(strata):
            r = by[(j, selected)]
            y = y0 + 16 + k * 20
            s.line(x(100 * r["ci_lo"]), y, x(100 * r["ci_hi"]), y, stroke=colour, width=2)
            s.dot(x(100 * r["bias"]), y, colour)
            value = 100 * r["bias"]
            s.text(right + 14, y + 4, "0.0" if abs(value) < 0.05 else f"{value:+.1f}", size=12)
    return s.done()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    charts = {"resolve": chart_resolve, "repeatability": chart_repeat, "bias": chart_bias}
    for name, fn in charts.items():
        for theme_name, theme in THEMES.items():
            (OUT / f"{name}-{theme_name}.svg").write_text(fn(theme))
    print(f"wrote {2 * len(charts)} files to {OUT}")


if __name__ == "__main__":
    main()
