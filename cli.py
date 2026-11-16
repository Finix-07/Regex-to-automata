"""Command-line front end.

    python cli.py "(a|b)*abb"
    python cli.py "(a|b)*abb" --test abb aabb ab --steps --out output
"""

import argparse
import shutil
import sys
from pathlib import Path

from core import RegexError, build, simulate
from viz.render import automaton_to_dot, ast_to_dot, table_to_text, transition_table


def main():
    ap = argparse.ArgumentParser(description="Regex -> ε-NFA -> DFA -> Minimized DFA")
    ap.add_argument("regex", help="operators: | or + (union), * (star), ( ), ε or # (epsilon)")
    ap.add_argument("--test", nargs="*", default=[], metavar="STRING", help="strings to test")
    ap.add_argument("--steps", action="store_true", help="print each algorithm's construction steps")
    ap.add_argument("--out", metavar="DIR", help="write .dot files (and .png if Graphviz is installed)")
    args = ap.parse_args()

    try:
        p = build(args.regex)
    except RegexError as e:
        print(f"Error: {e.message}", file=sys.stderr)
        if e.pos is not None:
            print(f"  {args.regex}\n  {' ' * e.pos}^", file=sys.stderr)
        sys.exit(1)

    print(f"Regex:   {args.regex}")
    print(f"Tokens:  {' '.join(map(str, p.tokens_with_concat))}")
    print(f"AST:     {p.ast}")
    for machine in (p.nfa, p.dfa, p.min_dfa):
        print(f"\n=== {machine.kind}  ({len(machine.states)} states) ===")
        print(table_to_text(transition_table(machine)))
        if args.steps:
            print("\nSteps:")
            for i, s in enumerate(machine.steps, 1):
                print(f"  {i:>2}. {s}")

    if args.test:
        print("\n=== String tests ===")
        for text in args.test:
            results = [simulate(m, text) for m in (p.nfa, p.dfa, p.min_dfa)]
            verdict = "ACCEPT" if results[2].accepted else "REJECT"
            path = " → ".join(p.min_dfa.fmt(c) if c else "∅" for c in results[2].configs)
            note = f"  ({results[2].halted})" if results[2].halted else ""
            agree = "" if len({r.accepted for r in results}) == 1 else "  [MISMATCH between machines!]"
            print(f"  {text or 'ε':<12} {verdict}   {path}{note}{agree}")

    if args.out:
        export(p, Path(args.out))


def export(p, out):
    out.mkdir(parents=True, exist_ok=True)
    graphs = {"ast": ast_to_dot(p.ast), "nfa": automaton_to_dot(p.nfa),
              "dfa": automaton_to_dot(p.dfa), "min_dfa": automaton_to_dot(p.min_dfa)}
    has_dot = shutil.which("dot") is not None
    for name, g in graphs.items():
        g.save(out / f"{name}.dot")
        if has_dot:
            g.render(out / name, format="png", cleanup=True)
    print(f"\nSaved {'PNG and .dot' if has_dot else '.dot'} diagrams to {out}/")
    if not has_dot:
        print("Install the Graphviz binary (brew install graphviz) to also get PNG images.")


if __name__ == "__main__":
    main()
