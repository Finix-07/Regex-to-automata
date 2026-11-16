"""Run an input string on any automaton and record every configuration."""

from dataclasses import dataclass


@dataclass
class Trace:
    text: str
    configs: list        # configs[i] = set of current states after reading i symbols
    accepted: bool
    halted: str = None   # reason the run stopped early, if it did

    @property
    def last_step(self):
        return len(self.configs) - 1


def simulate(automaton, text):
    """Works for the ε-NFA (tracks a set of states) and for DFAs (a set of one state)."""
    current = automaton.epsilon_closure({automaton.start})
    configs = [current]
    for ch in text:
        if ch not in automaton.alphabet:
            configs.append(frozenset())
            return Trace(text, configs, False, f"'{ch}' is not in the alphabet {{{', '.join(automaton.alphabet)}}}")
        current = automaton.epsilon_closure(automaton.move(current, ch))
        configs.append(current)
        if not current:
            return Trace(text, configs, False, f"no transition on '{ch}' (dead)")
    return Trace(text, configs, bool(current & automaton.accepts))
