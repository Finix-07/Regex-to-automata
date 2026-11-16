"""One data model shared by the ε-NFA, the DFA and the minimized DFA."""

from dataclasses import dataclass, field

from .lexer import EPSILON


@dataclass
class Automaton:
    kind: str                      # "ε-NFA", "DFA" or "Min-DFA"
    states: list                   # state names, in display order
    alphabet: list                 # input symbols (ε excluded)
    start: str
    accepts: set
    transitions: dict = field(default_factory=dict)   # state -> symbol -> set(states)
    represents: dict = field(default_factory=dict)    # DFA state -> set of states it stands for
    steps: list = field(default_factory=list)         # human-readable construction log

    def add_transition(self, src, symbol, dst):
        self.transitions.setdefault(src, {}).setdefault(symbol, set()).add(dst)

    def targets(self, state, symbol):
        return self.transitions.get(state, {}).get(symbol, set())

    @property
    def has_epsilon(self):
        return any(EPSILON in by_sym for by_sym in self.transitions.values())

    # Core NFA operations (they also work on a DFA, which simply has no ε-moves)
    def epsilon_closure(self, states):
        """All states reachable from `states` using only ε-transitions."""
        closure = set(states)
        stack = list(states)
        while stack:
            s = stack.pop()
            for t in self.targets(s, EPSILON):
                if t not in closure:
                    closure.add(t)
                    stack.append(t)
        return frozenset(closure)

    def move(self, states, symbol):
        """States reachable from `states` on exactly one `symbol` transition."""
        result = set()
        for s in states:
            result |= self.targets(s, symbol)
        return frozenset(result)

    def order(self, states):
        """Sort a collection of state names into display order."""
        index = {s: i for i, s in enumerate(self.states)}
        return sorted(states, key=lambda s: index.get(s, len(index)))

    def fmt(self, states):
        return "{" + ", ".join(self.order(states)) + "}"
