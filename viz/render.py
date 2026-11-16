"""Turn automata and syntax trees into Graphviz diagrams and transition tables.

Only the DOT source is generated here; the Streamlit UI renders it in the
browser, so the Graphviz system binary is needed only for PNG export (CLI).
"""

import graphviz

from core.lexer import EPSILON

HIGHLIGHT = "#fbbf24"
EDGE_HIGHLIGHT = "#d97706"


def automaton_to_dot(a, highlight=frozenset(), active_symbol=None, previous=frozenset()):
    """`highlight`: states to colour. `previous` + `active_symbol`: the edges just taken."""
    g = graphviz.Digraph(a.kind)
    g.attr(rankdir="LR", bgcolor="transparent", fontname="Helvetica")
    g.attr("node", shape="circle", fontname="Helvetica", style="filled", fillcolor="white")
    g.attr("edge", fontname="Helvetica")

    g.node("__start__", label="", shape="none", width="0", height="0")
    for s in a.states:
        attrs = {"shape": "doublecircle" if s in a.accepts else "circle"}
        if s in highlight:
            attrs.update(fillcolor=HIGHLIGHT, penwidth="2")
        g.node(s, **attrs)
    g.edge("__start__", a.start, label="start")

    # Merge parallel edges into one arrow labelled "a, b".
    merged = {}
    symbols = a.alphabet + [EPSILON]
    for src in a.states:
        for sym in symbols:
            for dst in a.targets(src, sym):
                merged.setdefault((src, dst), []).append(sym)
    for (src, dst), syms in merged.items():
        taken = active_symbol in syms and src in previous and dst in highlight
        attrs = {"color": EDGE_HIGHLIGHT, "penwidth": "2.5", "fontcolor": EDGE_HIGHLIGHT} if taken else {}
        g.edge(src, dst, label=", ".join(syms), **attrs)
    return g


def ast_to_dot(root):
    g = graphviz.Digraph("AST")
    g.attr(bgcolor="transparent")
    g.attr("node", fontname="Helvetica", shape="circle", style="filled", fillcolor="white")
    counter = [0]

    def visit(node):
        nid = f"n{counter[0]}"
        counter[0] += 1
        is_leaf = not node.children()
        g.node(nid, node.label, shape="box" if is_leaf else "circle",
               fillcolor="#dbeafe" if is_leaf else "#fef3c7")
        for child in node.children():
            g.edge(nid, visit(child))
        return nid

    visit(root)
    return g


def transition_table(a):
    """Rows of a transition table. '→' marks the start state and '*' accepting states."""
    columns = list(a.alphabet) + ([EPSILON] if a.has_epsilon else [])
    rows = []
    for s in a.states:
        mark = ("→" if s == a.start else "") + ("*" if s in a.accepts else "")
        row = {"State": f"{mark}{s}"}
        if a.represents:
            label = "NFA states" if a.kind == "DFA" else "DFA states"
            row[label] = _fmt_set(a, a.represents[s], a.kind)
        for sym in columns:
            targets = a.targets(s, sym)
            if not targets:
                row[sym] = "—"
            elif a.kind == "ε-NFA":
                row[sym] = a.fmt(targets)
            else:
                row[sym] = next(iter(targets))
        rows.append(row)
    return rows


def _fmt_set(a, states, kind):
    if kind == "DFA":   # NFA state names q0..qn: sort numerically
        return "{" + ", ".join(sorted(states, key=lambda q: int(q[1:]))) + "}"
    return "{" + ", ".join(sorted(states)) + "}"


def table_to_text(rows):
    """Plain-text table for the terminal."""
    if not rows:
        return ""
    headers = list(rows[0])
    widths = {h: max(len(h), *(len(str(r[h])) for r in rows)) for h in headers}
    line = "  ".join(h.ljust(widths[h]) for h in headers)
    out = [line, "  ".join("-" * widths[h] for h in headers)]
    for r in rows:
        out.append("  ".join(str(r[h]).ljust(widths[h]) for h in headers))
    return "\n".join(out)
