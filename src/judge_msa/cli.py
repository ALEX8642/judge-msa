"""Command line: ``judge-msa analyze`` and ``judge-msa simulate``."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from judge_msa.bootstrap import DEFAULT_N_BOOT
from judge_msa.report import analyze, render_html, render_markdown
from judge_msa.simulate import JudgeSpec, simulate
from judge_msa.table import TableError, load_table


def _analyze(args: argparse.Namespace) -> int:
    by = tuple(args.by or ())
    keep = by + (("weight",) if args.weight else ())
    try:
        df = load_table(
            args.table,
            item=args.item,
            judge=args.judge,
            trial=args.trial,
            verdict=args.verdict,
            system=args.system,
            reference=args.reference,
            by=tuple(args.weight if k == "weight" else k for k in keep),
        )
    except TableError as e:
        print(f"judge-msa: {e}", file=sys.stderr)
        return 2
    if args.weight and args.weight != "weight":
        df = df.rename(columns={args.weight: "weight"})
    values = sorted(df["verdict"].unique())
    if args.positive is None and len(values) == 2:
        print(
            f"judge-msa: the verdict column has two values, {values}. "
            "Say which one counts as a pass with --positive.",
            file=sys.stderr,
        )
        return 2
    try:
        result = analyze(
            df,
            positive=args.positive,
            compare=tuple(args.compare) if args.compare else None,
            by=by,
            n_boot=args.n_boot,
            seed=args.seed,
        )
    except ValueError as e:
        print(f"judge-msa: {e}", file=sys.stderr)
        return 2
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    (out / "report.md").write_text(render_markdown(result))
    (out / "report.html").write_text(render_html(result))
    print(f"wrote {out / 'report.html'}, report.md and result.json")
    return 0


def _judge_spec(text: str) -> tuple[str, JudgeSpec]:
    """name:flip:miss:false_alarm, where miss and false_alarm may be A=0.3/B=0.05."""

    def rate(s: str) -> float | dict[str, float]:
        if "=" not in s:
            return float(s)
        return {k: float(v) for k, v in (pair.split("=") for pair in s.split("/"))}

    name, flip, miss, fa = (text.split(":") + ["0", "0", "0"])[:4]
    return name, JudgeSpec(flip=float(flip), miss=rate(miss), false_alarm=rate(fa))


def _simulate(args: argparse.Namespace) -> int:
    systems = {k: float(v) for k, v in (pair.split("=") for pair in args.systems.split(","))}
    judges = dict(_judge_spec(j) for j in args.judge)
    df = simulate(
        args.items, systems, judges, args.trials, ref_fraction=args.ref_fraction, seed=args.seed
    )
    df.to_csv(args.out, index=False)
    print(f"wrote {args.out}: {len(df)} verdicts")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="judge-msa", description="Measurement system analysis for LLM judges."
    )
    sub = ap.add_subparsers(dest="command", required=True)

    a = sub.add_parser("analyze", help="analyse a table of judge verdicts")
    a.add_argument("table", help="CSV, JSONL or Parquet with one row per verdict")
    a.add_argument("--item", default="item", help="column naming the question")
    a.add_argument("--judge", default="judge", help="column naming the judge")
    a.add_argument("--trial", default="trial", help="column numbering repeated gradings")
    a.add_argument("--verdict", default="verdict", help="column holding the verdict")
    a.add_argument("--system", help="column naming the system that wrote the answer")
    a.add_argument("--reference", help="column holding the reference (human) verdict")
    a.add_argument("--weight", help="column of sampling weights for the reference answers")
    a.add_argument("--positive", help="the verdict value that counts as a pass")
    a.add_argument("--compare", nargs=2, metavar=("A", "B"), help="report system A minus B")
    a.add_argument("--by", nargs="*", help="extra columns to break bias down by")
    a.add_argument("--out", default="judge-msa-report", help="output directory")
    a.add_argument("--n-boot", type=int, default=DEFAULT_N_BOOT)
    a.add_argument("--seed", type=int, default=0)
    a.set_defaults(func=_analyze)

    s = sub.add_parser("simulate", help="write a simulated verdict table with planted behaviour")
    s.add_argument("--out", required=True)
    s.add_argument("--items", type=int, default=200)
    s.add_argument("--trials", type=int, default=3)
    s.add_argument(
        "--systems", default="A=0.7,B=0.6", help="system=true pass rate, comma-separated"
    )
    s.add_argument(
        "--judge",
        action="append",
        required=True,
        metavar="NAME:FLIP:MISS:FALSE_ALARM",
        help="e.g. strict:0.05:A=0.3/B=0.05:0.1 (repeat for more judges)",
    )
    s.add_argument("--ref-fraction", type=float, default=1.0)
    s.add_argument("--seed", type=int, default=0)
    s.set_defaults(func=_simulate)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
