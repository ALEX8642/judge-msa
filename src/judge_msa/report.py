"""Run every analysis on a verdict table and render the result as JSON, markdown and HTML."""

from __future__ import annotations

import html
from dataclasses import fields, is_dataclass
from typing import Any

import pandas as pd

from judge_msa.agreement import between_judges, vs_reference, within_judge
from judge_msa.bias import bias_table, difference_by_judge, differential_bias
from judge_msa.bootstrap import DEFAULT_N_BOOT
from judge_msa.components import components
from judge_msa.mrd import mrd
from judge_msa.table import NO_SYSTEM, PART, NotEstimable


def _plain(x: Any) -> Any:
    """Make a result JSON-serialisable."""
    if isinstance(x, NotEstimable):
        return {"not_estimable": x.reason}
    if is_dataclass(x):
        return {f.name: _plain(getattr(x, f.name)) for f in fields(x)}
    if isinstance(x, pd.DataFrame):
        return [_plain(r) for r in x.to_dict("records")]
    if isinstance(x, dict):
        return {str(k): _plain(v) for k, v in x.items()}
    if isinstance(x, list | tuple):
        return [_plain(v) for v in x]
    if hasattr(x, "item") and not isinstance(x, str):
        return x.item()
    return x


def analyze(
    df: pd.DataFrame,
    *,
    positive: str | None = None,
    compare: tuple[str, str] | None = None,
    by: tuple[str, ...] = (),
    n_boot: int = DEFAULT_N_BOOT,
    seed: int = 0,
) -> dict:
    """Everything the report shows, as one JSON-serialisable dict."""
    boot = {"n_boot": n_boot, "seed": seed}
    systems = sorted(df["system"].unique())
    judges = sorted(df["judge"].unique())
    values = sorted(df["verdict"].unique())
    parts = df.drop_duplicates(PART)
    has_ref = bool(parts["reference"].notna().any())
    weighted = "weight" in df.columns and df["weight"].nunique() > 1
    notes: list[str] = []
    if df.attrs.get("dropped"):
        n = df.attrs["dropped"]
        notes.append(
            f"{n} row{' had' if n == 1 else 's had'} no verdict and "
            f"{'was' if n == 1 else 'were'} left out."
        )
    if positive is not None and positive not in values:
        raise ValueError(f"positive verdict {positive!r} does not occur; values are {values}")
    if compare is None and len(systems) == 2:
        compare = (systems[1], systems[0])
        notes.append(f"No comparison was named, so {compare[0]} is compared with {compare[1]}.")
    if compare and not set(compare) <= set(systems):
        raise ValueError(f"--compare names {compare}, but the systems are {systems}")

    result: dict[str, Any] = {
        "meta": {
            "rows": len(df),
            "parts": len(parts),
            "items": int(df["item"].nunique()),
            "systems": systems,
            "judges": judges,
            "verdict_values": values,
            "positive": positive,
            "compare": list(compare) if compare else None,
            "reference_parts": int(parts["reference"].notna().sum()),
            "weighted": bool(weighted),
            "dropped": int(df.attrs.get("dropped", 0)),
            "n_boot": n_boot,
            "seed": seed,
        },
        "within": within_judge(df),
        "between": between_judges(df),
    }
    if positive is None:
        ne = NotEstimable("pass --positive to name the verdict that counts as a pass")
        for key in ("vs_reference", "bias", "differential_bias", "difference", "components", "mrd"):
            result[key] = ne
        notes.append(
            "No positive verdict was named, so bias, variance components and the minimum "
            "resolvable difference were not computed."
        )
    else:
        multi = len(systems) > 1
        result["vs_reference"] = vs_reference(df, positive, by="system" if multi else None)
        result["bias"] = bias_table(df, positive, **boot)
        result["bias_by"] = {b: bias_table(df, positive, by=b, **boot) for b in by}
        result["components"] = components(df, positive)
        result["grr_share"] = result["components"].attrs["grr_share"]
        if compare:
            a, b = compare
            result["differential_bias"] = differential_bias(df, positive, a, b, **boot)
            diff = difference_by_judge(df, positive, a, b, **boot)
            result["difference"] = diff
            result["difference_spread"] = diff.attrs["spread"]
            result["mrd"] = [mrd(df, positive, j, a, b, **boot) for j in judges]
        else:
            ne = NotEstimable("needs two systems to compare (--compare A B)")
            result["differential_bias"] = result["difference"] = result["mrd"] = ne
            if systems != [NO_SYSTEM]:
                notes.append("No pair of systems was compared; name one with --compare.")
    if not has_ref:
        notes.append(
            "There is no reference, so nothing here says whether any judge is right: "
            "judges that agree may share the same bias."
        )
    elif weighted:
        notes.append("Reference statistics use the sampling weights in the weight column.")
    if has_ref:
        notes.append(
            "Bias is measured against the reference as given. Errors in the reference shift every "
            "judge's bias, and the reference's own repeatability is not measured here unless it "
            "was entered as a judge with repeated trials."
        )
    result["notes"] = notes
    return _plain(result)


# ---------------------------------------------------------------------------------------------
# Rendering. Both formats are produced from one list of blocks.
# ---------------------------------------------------------------------------------------------


def _is_ne(x: Any) -> bool:
    return isinstance(x, dict) and "not_estimable" in x


def _fmt(x: Any, pts: bool = False) -> str:
    if _is_ne(x):
        return f"not estimable ({x['not_estimable']})"
    if x is None:
        return "–"
    if isinstance(x, bool):
        return "yes" if x else "no"
    if isinstance(x, float):
        return f"{100 * x:+.1f}" if pts else f"{x:.3f}"
    return str(x)


def _pts(x: float) -> str:
    return f"{100 * abs(x):.1f} points"


MIN_PARTS_FOR_INTERVAL = 10


def _cell(r: dict, key: str, pts: tuple[str, ...]) -> str:
    if (
        key in ("ci_lo", "ci_hi")
        and r.get("n_parts", MIN_PARTS_FOR_INTERVAL) < MIN_PARTS_FOR_INTERVAL
    ):
        return "too few"
    return _fmt(r.get(key), key in pts)


def _table(rows: Any, columns: list[tuple[str, str]], pts: tuple[str, ...] = ()) -> dict:
    if _is_ne(rows) or not rows:
        reason = rows["not_estimable"] if _is_ne(rows) else "no rows"
        return {"kind": "para", "text": f"Not estimable: {reason}."}
    return {
        "kind": "table",
        "head": [label for _, label in columns],
        "rows": [[_cell(r, key, pts) for key, _ in columns] for r in rows],
    }


def _headline(result: dict) -> list[dict]:
    m = result["mrd"]
    meta = result["meta"]
    if _is_ne(m):
        return [
            {
                "kind": "para",
                "text": f"Minimum resolvable difference: not estimable ({m['not_estimable']}).",
            }
        ]
    a, b = meta["compare"]
    out = []
    for r in m:
        seen = f"{r['judge']} reports {a} − {b} = {100 * r['diff_observed']:+.1f} points"
        if not _is_ne(r["mrd"]):
            verdict = "larger" if abs(r["diff_observed"]) > r["mrd"] else "not larger"
            text = (
                f"**{seen}.** On {r['n_items']} questions with {r['n_trials']} trial(s) it can "
                f"resolve differences above **{_pts(r['mrd'])}**: {_pts(r['noise'])} from judge "
                f"noise, which "
                f"more trials or questions shrink, plus up to {_pts(r['bias_bound'])} from bias "
                f"between the two systems, which they do not. The reported difference is {verdict} "
                f"than that."
            )
        else:
            known = []
            if not _is_ne(r["noise"]):
                known.append(f"judge noise is {_pts(r['noise'])}")
            if not _is_ne(r["bias_bound"]):
                known.append(f"bias between the systems may be up to {_pts(r['bias_bound'])}")
            text = (
                f"**{seen}.** Its minimum resolvable difference is not estimable "
                f"({r['mrd']['not_estimable']})" + (f"; {' and '.join(known)}." if known else ".")
            )
        out.append({"kind": "para", "text": text})
    if meta["compare"] and len(meta["judges"]) > 1 and "difference_spread" in result:
        out.append(
            {
                "kind": "para",
                "text": f"The judges' own figures for {a} − {b} differ from each other by "
                f"{_pts(result['difference_spread'])}.",
            }
        )
    return out


def _blocks(result: dict) -> list[dict]:
    meta = result["meta"]
    blocks: list[dict] = [
        {"kind": "h1", "text": "Judge measurement system analysis"},
        {
            "kind": "para",
            "text": f"{meta['rows']} verdicts on {meta['parts']} answers "
            f"({meta['items']} questions) "
            f"from {len(meta['judges'])} judge(s): {', '.join(meta['judges'])}. "
            f"{meta['reference_parts']} answers have a reference verdict."
            + (f" Pass = “{meta['positive']}”." if meta["positive"] else ""),
        },
        {"kind": "h2", "text": "What difference can each judge resolve?"},
        *_headline(result),
        {"kind": "h2", "text": "Repeatability: does a judge agree with itself?"},
        {
            "kind": "para",
            "text": "The same judge grading the same answer again. Flip rate is the chance that "
            "two trials of one answer disagree.",
        },
        _table(
            result["within"],
            [
                ("judge", "Judge"),
                ("n_parts", "Answers"),
                ("n_trials", "Trials"),
                ("pct_all_agree", "All trials agree"),
                ("flip_rate", "Flip rate"),
                ("fleiss_kappa", "Kappa"),
            ],
        ),
        {"kind": "h2", "text": "Reproducibility: do judges agree with each other?"},
    ]
    between = result["between"]
    if _is_ne(between):
        blocks.append({"kind": "para", "text": f"Not estimable: {between['not_estimable']}."})
    else:
        blocks += [
            {
                "kind": "para",
                "text": f"On {between['n_parts']} answers graded by every judge, all judges agreed "
                f"on every trial for {100 * between['pct_all_agree']:.1f}%. "
                f"Fleiss' kappa across judges: {_fmt(between['fleiss_kappa'])}.",
            },
            _table(
                between["pairwise"],
                [
                    ("judge_a", "Judge"),
                    ("judge_b", "Judge"),
                    ("agreement", "Agreement"),
                    ("cohen_kappa", "Cohen's kappa"),
                ],
            ),
        ]
    multi = len(meta["systems"]) > 1
    blocks += [
        {"kind": "h2", "text": "Against the reference"},
        {
            "kind": "para",
            "text": "A miss is a pass given to an answer the reference fails; a false alarm is a "
            "fail given to an answer the reference passes.",
        },
        _table(
            result["vs_reference"],
            [("judge", "Judge")]
            + ([("system", "System")] if multi else [])
            + [
                ("n_parts", "Answers"),
                ("agreement", "Agreement"),
                ("cohen_kappa", "Kappa"),
                ("miss_rate", "Miss rate"),
                ("false_alarm_rate", "False-alarm rate"),
            ],
        ),
        {"kind": "h2", "text": "Bias: judge score minus reference score"},
        {
            "kind": "para",
            "text": "In points, on the answers that have a reference, with 95% intervals. A judge "
            "that is equally biased on every system still ranks them fairly; a difference in bias "
            "between systems does not wash out.",
        },
    ]
    bias = result["bias"]
    if not _is_ne(bias) and bias:
        blocks.append({"kind": "chart", "rows": bias, "group": "system"})
    bias_cols = [
        ("n_parts", "Answers"),
        ("judge_score", "Judge score"),
        ("ref_score", "Reference score"),
        ("bias", "Bias (pts)"),
        ("ci_lo", "Low"),
        ("ci_hi", "High"),
    ]
    pts = ("bias", "ci_lo", "ci_hi", "diff_bias", "diff")
    blocks.append(_table(bias, [("judge", "Judge"), ("system", "System")] + bias_cols, pts))
    for name, rows in (result.get("bias_by") or {}).items():
        blocks.append({"kind": "h3", "text": f"Bias by {name}"})
        blocks.append(
            _table(rows, [("judge", "Judge"), (name, name.capitalize())] + bias_cols, pts)
        )
    if meta["compare"]:
        a, b = meta["compare"]
        blocks += [
            {"kind": "h3", "text": f"Difference in bias, {a} minus {b}"},
            _table(
                result["differential_bias"],
                [
                    ("judge", "Judge"),
                    ("n_items", "Reference questions"),
                    ("diff_bias", "Difference in bias (pts)"),
                    ("ci_lo", "Low"),
                    ("ci_hi", "High"),
                ],
                pts,
            ),
            {"kind": "h3", "text": f"{a} minus {b}, as each judge scores it (all answers)"},
            _table(
                result["difference"],
                [
                    ("judge", "Judge"),
                    ("score_a", a),
                    ("score_b", b),
                    ("diff", "Difference (pts)"),
                    ("ci_lo", "Low"),
                    ("ci_hi", "High"),
                ],
                pts,
            ),
        ]
    blocks += [
        {"kind": "h2", "text": "Where the variation comes from"},
        {
            "kind": "para",
            "text": "Share of the variance in pass/fail verdicts due to the answers themselves "
            "(part), to judges being stricter or more lenient overall (judge), to judges "
            "disagreeing about particular answers (judge × part), and to a judge disagreeing with "
            "itself (repeatability)."
            + (
                f" The measurement system accounts for {100 * result['grr_share']:.1f}% "
                "of the variance."
                if isinstance(result.get("grr_share"), float)
                else ""
            ),
        },
        _table(
            result["components"],
            [("component", "Component"), ("variance", "Variance"), ("share", "Share")],
        ),
        {"kind": "h2", "text": "What this data cannot tell you"},
        {"kind": "list", "items": result["notes"] + _mrd_notes(result)},
    ]
    return blocks


def _mrd_notes(result: dict) -> list[str]:
    if _is_ne(result["mrd"]):
        return []
    seen: list[str] = []
    for r in result["mrd"]:
        for n in r["notes"]:
            note = n[0].upper() + n[1:] + "."
            if note not in seen:
                seen.append(note)
    return seen


def render_markdown(result: dict) -> str:
    out: list[str] = []
    for b in _blocks(result):
        kind = b["kind"]
        if kind in ("h1", "h2", "h3"):
            out.append("#" * int(kind[1]) + " " + b["text"])
        elif kind == "para":
            out.append(b["text"])
        elif kind == "list":
            out.append("\n".join(f"- {i}" for i in b["items"]) or "- Nothing to add.")
        elif kind == "table":
            lines = ["| " + " | ".join(b["head"]) + " |", "|" + "---|" * len(b["head"])]
            lines += ["| " + " | ".join(r) + " |" for r in b["rows"]]
            out.append("\n".join(lines))
    return "\n\n".join(out) + "\n"


CSS = """
:root{--bg:#fbfaf7;--fg:#1d1d1b;--muted:#63625c;--line:#dcdad2;--accent:#2f5d8a;--bar:#2f5d8a}
@media (prefers-color-scheme:dark){:root{--bg:#161614;--fg:#ecebe6;--muted:#a3a299;--line:#3a3934;
--accent:#8fb8e0;--bar:#8fb8e0}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);
font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:920px;margin:0 auto;padding:32px 16px 64px}
h1{font-size:1.7rem;margin:0 0 .4em}h2{font-size:1.2rem;margin:2.2em 0 .5em;padding-top:.8em;
border-top:1px solid var(--line)}h3{font-size:1rem;margin:1.6em 0 .4em}
p{margin:.6em 0;max-width:70ch}.wrap{overflow-x:auto}
table{border-collapse:collapse;font-size:.92rem;font-variant-numeric:tabular-nums;margin:.6em 0}
th,td{text-align:left;padding:6px 14px 6px 0;border-bottom:1px solid var(--line);white-space:nowrap}
th{color:var(--muted);font-weight:600}li{margin:.3em 0;max-width:70ch}
svg text{fill:var(--fg);font:12px system-ui,sans-serif}svg .muted{fill:var(--muted)}
"""


def _inline(text: str) -> str:
    """Escape, then turn **bold** into <strong>."""
    parts = html.escape(text).split("**")
    return "".join(f"<strong>{p}</strong>" if i % 2 else p for i, p in enumerate(parts))


def _chart(rows: list[dict], group: str) -> str:
    """Bias per judge and group with its interval, as inline SVG (no external references)."""
    label_w, plot_w, row_h, top = 250, 420, 26, 24
    vals = [v for r in rows for v in (r["ci_lo"], r["ci_hi"], 0.0)]
    lo, hi = min(vals), max(vals)
    pad = (hi - lo) * 0.08 or 0.05
    lo, hi = lo - pad, hi + pad

    def x(v: float) -> float:
        return label_w + (v - lo) / (hi - lo) * plot_w

    height = top + row_h * len(rows) + 28
    out = [
        f'<svg viewBox="0 0 {label_w + plot_w + 20} {height}" role="img" '
        f'aria-label="Bias by judge and {html.escape(group)}, with 95% intervals" '
        f'style="max-width:100%;height:auto">',
        f'<line x1="{x(0):.1f}" x2="{x(0):.1f}" y1="{top - 8}" y2="{height - 24}" '
        f'stroke="var(--muted)" stroke-dasharray="3 3"/>',
        f'<text class="muted" x="{x(0):.1f}" y="{height - 8}" text-anchor="middle">no bias</text>',
    ]
    for i, r in enumerate(rows):
        y = top + row_h * i + row_h / 2
        name = html.escape(f"{r['judge']} · {r[group]}")
        out += [
            f'<text x="0" y="{y + 4:.1f}">{name}</text>',
            f'<line x1="{x(r["ci_lo"]):.1f}" x2="{x(r["ci_hi"]):.1f}" y1="{y:.1f}" y2="{y:.1f}" '
            f'stroke="var(--bar)" stroke-width="2"/>',
            f'<circle cx="{x(r["bias"]):.1f}" cy="{y:.1f}" r="4.5" fill="var(--bar)"/>',
            f'<text class="muted" x="{x(r["ci_hi"]) + 6:.1f}" y="{y + 4:.1f}">'
            f"{100 * r['bias']:+.1f}</text>",
        ]
    return "".join(out) + "</svg>"


def render_html(result: dict) -> str:
    body: list[str] = []
    for b in _blocks(result):
        kind = b["kind"]
        if kind in ("h1", "h2", "h3"):
            body.append(f"<{kind}>{html.escape(b['text'])}</{kind}>")
        elif kind == "para":
            body.append(f"<p>{_inline(b['text'])}</p>")
        elif kind == "list":
            items = b["items"] or ["Nothing to add."]
            body.append("<ul>" + "".join(f"<li>{_inline(i)}</li>" for i in items) + "</ul>")
        elif kind == "chart":
            body.append(_chart(b["rows"], b["group"]))
        elif kind == "table":
            head = "".join(f"<th>{html.escape(h)}</th>" for h in b["head"])
            rows = "".join(
                "<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in r) + "</tr>"
                for r in b["rows"]
            )
            body.append(
                f'<div class="wrap"><table><thead><tr>{head}</tr></thead>'
                f"<tbody>{rows}</tbody></table></div>"
            )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>Judge measurement system analysis</title><style>{CSS}</style></head>"
        f"<body><main>{''.join(body)}</main></body></html>\n"
    )
