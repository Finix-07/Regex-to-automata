# Regex → Automata Visualizer (Python prototype)

A compiler-design mini project that converts a regular expression into an
**ε-NFA**, a **DFA**, and a **minimized DFA**, shows each one as a diagram and a
transition table, explains every construction step, and lets you trace an input
string through any of the machines.

It is a Python re-implementation of the core of
[regex-to-automata-visualizer](https://github.com/Sainath-10/regex-to-automata-visualizer).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Optional: `brew install graphviz` is needed **only** for PNG export from the CLI.
The web UI renders diagrams in the browser and does not need it.

## Run

```bash
streamlit run app.py                        # web UI at http://localhost:8501

python cli.py "(a|b)*abb"                   # tables in the terminal
python cli.py "(a|b)*abb" --test abb ab --steps --out output

python -m pytest                            # test suite
```

## Regex syntax

| Syntax      | Meaning                           | Example      |
|-------------|-----------------------------------|--------------|
| `ab`        | concatenation (implicit)          | `abb`        |
| `a\|b`, `a+b` | union (`+` is textbook notation) | `(a+b)*`     |
| `a*`        | Kleene star (zero or more)        | `(ab)*`      |
| `( )`       | grouping                          | `(a\|b)*abb` |
| `ε` or `#`  | empty string                      | `a(b\|#)`    |

Symbols are single letters or digits. Precedence: `*` > concatenation > `|`.

## How it works: the pipeline

```
 regex ──► Lexer ──► Parser ──► AST ──► Thompson ──► ε-NFA ──► Subset ──► DFA ──► Minimize ──► Min-DFA
          tokens    recursive          construction           construction        partition
          + '.'     descent                                                       refinement
```

| Phase | File | Theory |
|---|---|---|
| Lexical analysis | `core/lexer.py` | Scan characters into tokens; insert explicit concatenation `.` between `ab`, `a(`, `)a`, `*a`, … |
| Syntax analysis | `core/parser.py` | Recursive descent over the grammar below; builds an AST and reports syntax errors with positions |
| ε-NFA | `core/nfa.py` | **Thompson's construction**: one fragment per AST node, joined with ε-transitions |
| DFA | `core/dfa.py` | **Subset construction**: DFA state = `ε-closure(move(T, a))` |
| Minimization | `core/minimize.py` | **Moore's partition refinement**: split {accepting, non-accepting} until stable |
| Simulation | `core/simulate.py` | Track the set of current states symbol by symbol |
| Visualization | `viz/render.py`, `app.py` | Graphviz DOT diagrams, transition tables, Streamlit UI |

Parser grammar:

```
expr   → term   ( '|' term )*
term   → factor ( '.' factor )*
factor → base '*'*
base   → SYMBOL | 'ε' | '(' expr ')'
```

All three machines share one `Automaton` class (`core/automaton.py`), so
drawing, tables, and simulation are written only once.

## Verification

`tests/test_pipeline.py` checks:

* lexer output, operator precedence, and every syntax-error message;
* known textbook results, e.g. `(a|b)*abb` → 14-state NFA, 5-state DFA (A–E),
  4-state minimal DFA (Dragon Book, Examples 3.24 and 3.40);
* **language equivalence**: for 12 regexes, every string up to length 7 is run on
  the NFA, DFA, and Min-DFA and compared with Python's own `re` engine.

## Project structure

```
core/        lexer, parser, AST, automaton model, the three algorithms, simulator
viz/         Graphviz diagrams and transition tables
app.py       Streamlit web UI
cli.py       command-line interface
tests/       pytest suite
```

## Future scope

1. **Direct regex → DFA** (Dragon Book §3.9) using `nullable`, `firstpos`,
   `lastpos`, and `followpos` on the existing AST, skipping the NFA.
2. **More operators**: `?`, `+` as one-or-more, character classes `[a-z]`, escapes.
3. **Lexer generator (mini-Lex)**: several token regexes (`ID`, `NUM`, `IF`, …)
   combined into one DFA with longest-match and priority rules.
4. **Grammars and parsing**: CFG input, FIRST/FOLLOW sets, LL(1) parse tables,
   then LR(0)/SLR(1). The recursive-descent parser here is the starting point.
5. **UI**: draggable, interactive graphs and image/PDF export from the browser.

## References

* Aho, Lam, Sethi, Ullman: *Compilers: Principles, Techniques, and Tools*, Ch. 3
* Hopcroft, Motwani, Ullman: *Introduction to Automata Theory, Languages, and Computation*, Ch. 2–4
