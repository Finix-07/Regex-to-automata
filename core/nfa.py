"""Thompson's construction: AST -> ε-NFA.

Every sub-expression becomes a fragment with exactly one start state and one
accepting state. Fragments are glued together with ε-transitions:

    a        :  s --a--> f
    ε        :  s --ε--> f
    R S      :  R.f --ε--> S.s
    R | S    :  s --ε--> R.s, S.s      R.f, S.f --ε--> f
    R*       :  s --ε--> R.s, f        R.f --ε--> R.s, f
"""

from collections import deque

from .ast_nodes import Concat, Epsilon, Star, Symbol, Union, alphabet_of
from .automaton import Automaton
from .lexer import EPSILON


class _Builder:
    def __init__(self):
        self.count = 0
        self.edges = []   # (src, symbol, dst) using raw integer ids
        self.log = []     # (template, raw ids) - formatted after renumbering

    def new_state(self):
        self.count += 1
        return self.count - 1

    def edge(self, src, symbol, dst):
        self.edges.append((src, symbol, dst))

    def build(self, node):
        """Return (start, accept) of the fragment for `node`."""
        if isinstance(node, (Symbol, Epsilon)):
            s, f = self.new_state(), self.new_state()
            sym = node.char if isinstance(node, Symbol) else EPSILON
            self.edge(s, sym, f)
            self.log.append((f"'{node}': {{}} --{sym}--> {{}}", [s, f]))
            return s, f

        if isinstance(node, Concat):
            s1, f1 = self.build(node.left)
            s2, f2 = self.build(node.right)
            self.edge(f1, EPSILON, s2)
            self.log.append((f"Concat '{node}': link {{}} --ε--> {{}}; start {{}}, accept {{}}",
                             [f1, s2, s1, f2]))
            return s1, f2

        if isinstance(node, Union):
            s1, f1 = self.build(node.left)
            s2, f2 = self.build(node.right)
            s, f = self.new_state(), self.new_state()
            for e in [(s, s1), (s, s2), (f1, f), (f2, f)]:
                self.edge(e[0], EPSILON, e[1])
            self.log.append((f"Union '{node}': new start {{}} --ε--> {{}}, {{}}; "
                             f"{{}}, {{}} --ε--> new accept {{}}", [s, s1, s2, f1, f2, f]))
            return s, f

        if isinstance(node, Star):
            s1, f1 = self.build(node.child)
            s, f = self.new_state(), self.new_state()
            for e in [(s, s1), (s, f), (f1, s1), (f1, f)]:
                self.edge(e[0], EPSILON, e[1])
            self.log.append((f"Star '{node}': new start {{}}, new accept {{}}; "
                             f"skip {{}} --ε--> {{}}, loop back {{}} --ε--> {{}}", [s, f, s, f, f1, s1]))
            return s, f

        raise TypeError(f"Unknown node {node!r}")


def thompson(ast):
    b = _Builder()
    start, accept = b.build(ast)

    # Renumber states in breadth-first order from the start so the diagram reads left to right.
    out = {}
    for src, sym, dst in b.edges:
        out.setdefault(src, []).append(dst)
    order, seen, queue = [], {start}, deque([start])
    while queue:
        s = queue.popleft()
        order.append(s)
        for t in out.get(s, []):
            if t not in seen:
                seen.add(t)
                queue.append(t)
    name = {raw: f"q{i}" for i, raw in enumerate(order)}

    nfa = Automaton(
        kind="ε-NFA",
        states=[name[s] for s in order],
        alphabet=alphabet_of(ast),
        start=name[start],
        accepts={name[accept]},
    )
    for src, sym, dst in b.edges:
        nfa.add_transition(name[src], sym, name[dst])
    nfa.steps = [tmpl.format(*(name[x] for x in ids)) for tmpl, ids in b.log]
    nfa.steps.append(f"Done: start state {nfa.start}, accepting state {nfa.fmt(nfa.accepts)}, "
                     f"{len(nfa.states)} states.")
    return nfa
