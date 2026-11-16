"""Subset construction: ε-NFA -> DFA.

Each DFA state stands for a *set* of NFA states:

    D-start = ε-closure({nfa.start})
    for every unmarked D-state T and every input symbol a:
        U = ε-closure(move(T, a))
        add the transition T --a--> U (creating U if it is new)

A D-state is accepting if it contains an NFA accepting state. Empty sets are
not added, so the DFA is *partial*: a missing transition means "reject".
"""

from collections import deque

from .automaton import Automaton


def state_name(i):
    """A, B, ..., Z, A1, B1, ... (the Dragon Book convention)."""
    letter = chr(ord("A") + i % 26)
    return letter if i < 26 else f"{letter}{i // 26}"


def subset_construction(nfa):
    start_set = nfa.epsilon_closure({nfa.start})
    names = {start_set: state_name(0)}
    queue = deque([start_set])

    dfa = Automaton(kind="DFA", states=[names[start_set]], alphabet=list(nfa.alphabet),
                    start=names[start_set], accepts=set())
    dfa.represents[dfa.start] = start_set
    dfa.steps.append(f"Start: ε-closure({{{nfa.start}}}) = {nfa.fmt(start_set)} = {dfa.start}")

    while queue:
        T = queue.popleft()
        for a in nfa.alphabet:
            moved = nfa.move(T, a)
            if not moved:
                dfa.steps.append(f"{names[T]} on '{a}': move = ∅ (no transition)")
                continue
            U = nfa.epsilon_closure(moved)
            is_new = U not in names
            if is_new:
                names[U] = state_name(len(names))
                dfa.states.append(names[U])
                dfa.represents[names[U]] = U
                queue.append(U)
            dfa.add_transition(names[T], a, names[U])
            dfa.steps.append(
                f"{names[T]} on '{a}': move = {nfa.fmt(moved)}, ε-closure = {nfa.fmt(U)}"
                f" = {names[U]}{'  (new)' if is_new else ''}"
            )

    for subset, name in names.items():
        if subset & nfa.accepts:
            dfa.accepts.add(name)
    dfa.steps.append(f"Accepting states (contain {nfa.fmt(nfa.accepts)}): {dfa.fmt(dfa.accepts)}")
    return dfa
