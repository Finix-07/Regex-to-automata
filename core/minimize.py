"""DFA minimization by partition refinement (Moore's algorithm).

1. Make the DFA complete by adding a dead state ∅ for missing transitions.
2. Start with two groups: accepting states and non-accepting states.
3. Repeatedly split a group when two of its states go to *different groups*
   on some input symbol. Stop when no group splits.
4. Each final group becomes one state. The dead state is dropped again so the
   result is the minimal partial DFA (the usual textbook answer).
"""

from collections import deque

from .automaton import Automaton

DEAD = "∅"


def _complete(dfa):
    """Copy of the DFA's transition function with every missing move sent to DEAD."""
    states = list(dfa.states)
    delta = {s: {a: next(iter(dfa.targets(s, a)), DEAD) for a in dfa.alphabet} for s in states}
    if any(DEAD in row.values() for row in delta.values()):
        states.append(DEAD)
        delta[DEAD] = {a: DEAD for a in dfa.alphabet}
    return states, delta


def minimize(dfa):
    states, delta = _complete(dfa)
    steps = []
    if DEAD in states:
        steps.append(f"Added dead state {DEAD} for missing transitions to make the DFA complete.")

    def show(partition):
        return "  ".join("{" + ", ".join(g) + "}" for g in partition)

    accepting = [s for s in states if s in dfa.accepts]
    rejecting = [s for s in states if s not in dfa.accepts]
    partition = [g for g in (accepting, rejecting) if g]
    steps.append(f"Round 0 (accepting / non-accepting): {show(partition)}")

    round_no = 0
    while True:
        round_no += 1
        group_of = {s: i for i, g in enumerate(partition) for s in g}
        refined = []
        for group in partition:
            buckets = {}
            for s in group:
                signature = tuple(group_of[delta[s][a]] for a in dfa.alphabet)
                buckets.setdefault(signature, []).append(s)
            refined.extend(buckets.values())
            if len(buckets) > 1:
                parts = " | ".join("{" + ", ".join(b) + "}" for b in buckets.values())
                steps.append(f"Round {round_no}: split {{{', '.join(group)}}} into {parts}")
        if len(refined) == len(partition):
            steps.append(f"Round {round_no}: no group split, partition is stable: {show(refined)}")
            break
        partition = refined
        steps.append(f"Round {round_no} result: {show(partition)}")

    # Representative for each group: its first real (non-dead) DFA state.
    group_of = {s: i for i, g in enumerate(partition) for s in g}
    rep = {i: next((s for s in g if s != DEAD), DEAD) for i, g in enumerate(partition)}
    dead_groups = {i for i, g in enumerate(partition) if DEAD in g}

    # Build the minimal DFA in breadth-first order from the start group, skipping the dead group.
    start_group = group_of[dfa.start]
    order, seen, queue = [], {start_group}, deque([start_group])
    while queue:
        g = queue.popleft()
        order.append(g)
        for a in dfa.alphabet:
            t = group_of[delta[rep[g]][a]]
            if t not in seen and t not in dead_groups:
                seen.add(t)
                queue.append(t)

    m = Automaton(kind="Min-DFA", states=[rep[g] for g in order], alphabet=list(dfa.alphabet),
                  start=rep[start_group], accepts=set())
    for g in order:
        name = rep[g]
        m.represents[name] = frozenset(s for s in partition[g] if s != DEAD)
        if partition[g][0] in dfa.accepts:
            m.accepts.add(name)
        for a in dfa.alphabet:
            t = group_of[delta[name][a]]
            if t not in dead_groups:
                m.add_transition(name, a, rep[t])

    if dead_groups:
        steps.append(f"Removed the dead group containing {DEAD} from the result.")
    merged = [f"{{{', '.join(m.order(m.represents[s]))}}} → {s}"
              for s in m.states if len(m.represents[s]) > 1]
    if merged:
        steps.append("Merged equivalent states: " + "; ".join(merged))
    steps.append(f"Minimal DFA has {len(m.states)} states (DFA had {len(dfa.states)}).")
    m.steps = steps
    return m
