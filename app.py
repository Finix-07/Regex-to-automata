"""Streamlit UI.  Run with:  streamlit run app.py"""

import time

import pandas as pd
import streamlit as st

from core import RegexError, build, simulate
from viz.render import automaton_to_dot, ast_to_dot, transition_table

EXAMPLES = ["(a|b)*abb", "(aa+bb)*", "a*b*", "(a|b)*a(a|b)", "(ab|ba)*", "a(b|c)*d", "(0|1)*00"]

st.set_page_config(page_title="Regex → Automata", page_icon="🔁", layout="wide")


def use_example():
    st.session_state.regex = st.session_state.example


st.title("Regex → ε-NFA → DFA → Minimized DFA")
st.caption("Thompson's construction · Subset construction · Partition-refinement minimization")

if "regex" not in st.session_state:
    st.session_state.regex = EXAMPLES[0]

col_in, col_ex = st.columns([3, 1])
with col_in:
    regex = st.text_input("Regular expression", key="regex",
                          help="Operators: | or + (union), * (Kleene star), ( ) grouping, "
                               "ε or # (epsilon). Concatenation is implicit. Symbols: letters and digits.")
with col_ex:
    st.selectbox("Examples", EXAMPLES, key="example", on_change=use_example, index=None,
                 placeholder="Pick an example")

try:
    p = build(regex)
except RegexError as e:
    st.error(f"**Syntax error:** {e.message}")
    if e.pos is not None:
        st.code(f"{regex}\n{' ' * e.pos}^", language=None)
    st.stop()

m1, m2, m3, m4 = st.columns(4)
m1.metric("Alphabet", "{" + ", ".join(p.nfa.alphabet) + "}")
m2.metric("ε-NFA states", len(p.nfa.states))
m3.metric("DFA states", len(p.dfa.states))
m4.metric("Min-DFA states", len(p.min_dfa.states),
          delta=len(p.min_dfa.states) - len(p.dfa.states) or None, delta_color="inverse")

tab_parse, tab_nfa, tab_dfa, tab_min, tab_test = st.tabs(
    ["1 · Lexer & Parser", "2 · ε-NFA", "3 · DFA", "4 · Minimized DFA", "5 · String Tester"])


def show_steps(machine, title):
    with st.expander(f"Step-by-step: {title}", expanded=False):
        st.markdown("\n".join(f"{i}. {s}" for i, s in enumerate(machine.steps, 1)))


def show_machine(machine, title, explanation):
    st.markdown(explanation)
    st.graphviz_chart(automaton_to_dot(machine))
    st.markdown("**Transition table**  (→ start, * accepting, — no transition)")
    st.dataframe(pd.DataFrame(transition_table(machine)), hide_index=True)
    show_steps(machine, title)


with tab_parse:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Tokens** (lexical analysis)")
        st.code("  ".join(f"{t.type.value}({t.value})" for t in p.tokens), language=None)
        st.markdown("**With explicit concatenation** ( `.` )")
        st.code(" ".join(map(str, p.tokens_with_concat)), language=None)
        st.markdown("**Parsed back from the AST**")
        st.code(str(p.ast), language=None)
        with st.expander("Grammar used by the recursive-descent parser"):
            st.code("expr   → term   ( '|' term )*\n"
                    "term   → factor ( '.' factor )*\n"
                    "factor → base '*'*\n"
                    "base   → SYMBOL | 'ε' | '(' expr ')'", language=None)
            st.markdown("Precedence: `*` > concatenation > `|`. All binary operators are left-associative.")
    with c2:
        st.markdown("**Abstract syntax tree**")
        st.graphviz_chart(ast_to_dot(p.ast))

with tab_nfa:
    show_machine(p.nfa, "Thompson's construction",
                 "Built bottom-up from the AST: every sub-expression becomes a fragment with one start "
                 "and one accepting state, glued together with **ε-transitions**.")

with tab_dfa:
    show_machine(p.dfa, "Subset construction",
                 "Each DFA state is a **set of NFA states**: `ε-closure(move(T, a))`. "
                 "Missing transitions mean the input is rejected.")

with tab_min:
    show_machine(p.min_dfa, "Partition refinement",
                 "States that no input string can tell apart are merged. Start from "
                 "{accepting, non-accepting} and keep splitting groups until nothing changes.")

with tab_test:
    machines = {"Minimized DFA": p.min_dfa, "DFA": p.dfa, "ε-NFA": p.nfa}
    c1, c2 = st.columns([2, 1])
    text = c1.text_input("Input string", value="abb" if p.nfa.alphabet[:2] == ["a", "b"] else "")
    choice = c2.radio("Machine", list(machines), horizontal=True)
    machine = machines[choice]
    trace = simulate(machine, text)

    # Reset the step counter whenever the input, machine or regex changes.
    key = (regex, text, choice)
    if st.session_state.get("trace_key") != key:
        st.session_state.trace_key = key
        st.session_state.step = 0
    st.session_state.step = min(st.session_state.step, trace.last_step)

    def go(delta=None, to=None):
        st.session_state.step = to if to is not None else max(0, min(trace.last_step, st.session_state.step + delta))

    b = st.columns(6)
    b[0].button("⏮ Reset", on_click=go, kwargs={"to": 0}, width="stretch")
    b[1].button("◀ Back", on_click=go, kwargs={"delta": -1}, width="stretch")
    b[2].button("Next ▶", on_click=go, kwargs={"delta": 1}, width="stretch")
    b[3].button("End ⏭", on_click=go, kwargs={"to": trace.last_step}, width="stretch")
    play = b[4].button("▶ Play", width="stretch")
    speed = b[5].select_slider("Speed", ["slow", "normal", "fast"], value="normal", label_visibility="collapsed")

    status_box = st.empty()
    graph_box = st.empty()

    def render(i):
        current = trace.configs[i]
        prev = trace.configs[i - 1] if i > 0 else frozenset()
        symbol = text[i - 1] if i > 0 else None
        tape = f"read `{text[:i] or 'ε'}` · remaining `{text[i:] or 'ε'}`"
        if i == trace.last_step and trace.halted:
            msg, kind = f"**REJECTED**: {trace.halted}", "error"
        elif i == trace.last_step:
            msg, kind = ("**ACCEPTED**", "success") if trace.accepted else \
                        ("**REJECTED**: ended in a non-accepting state", "error")
        else:
            msg, kind = f"Step {i}/{len(text)}", "info"
        states = machine.fmt(current) if current else "∅"
        getattr(status_box, kind)(f"{msg}  \nTape: {tape}  \nCurrent state(s): **{states}**")
        graph_box.graphviz_chart(automaton_to_dot(machine, highlight=current, active_symbol=symbol, previous=prev))

    if play:
        delay = {"slow": 1.2, "normal": 0.7, "fast": 0.3}[speed]
        for i in range(trace.last_step + 1):
            render(i)
            time.sleep(delay)
        st.session_state.step = trace.last_step
    else:
        render(st.session_state.step)

    st.markdown("**Full trace**")
    rows = [{"Step": i, "Read": text[i - 1] if i else "—",
             "State(s)": machine.fmt(c) if c else "∅"} for i, c in enumerate(trace.configs)]
    st.dataframe(pd.DataFrame(rows), hide_index=True)

    st.markdown("**All three machines must agree** (they recognise the same language)")
    verdicts = {name: ("✅ accept" if simulate(m, text).accepted else "❌ reject") for name, m in machines.items()}
    st.dataframe(pd.DataFrame([verdicts]), hide_index=True)
