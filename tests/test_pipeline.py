import itertools
import re

import pytest

from core import RegexError, build, simulate
from core.lexer import TokenType, insert_concat, tokenize
from core.parser import parse


# ---- lexer / parser ---------------------------------------------------------

def test_concat_insertion():
    toks = insert_concat(tokenize("(a|b)*abb"))
    assert " ".join(map(str, toks)) == "( a | b ) * . a . b . b"


def test_plus_is_union_and_hash_is_epsilon():
    kinds = [t.type for t in tokenize("a+#")]
    assert kinds == [TokenType.SYMBOL, TokenType.UNION, TokenType.EPSILON]


@pytest.mark.parametrize("regex, expected", [
    ("ab|c", "(ab|c)"),          # concat binds tighter than union
    ("ab*", "ab*"),              # star binds tighter than concat
    ("(ab)*", "(ab)*"),
    ("a|b|c", "((a|b)|c)"),      # left associative
])
def test_precedence(regex, expected):
    assert str(parse(regex)) == expected


@pytest.mark.parametrize("regex, message", [
    ("", "Empty regular expression"),
    ("(ab", "Unmatched '('"),
    ("ab)", "Unmatched ')'"),
    ("()", "Empty group"),
    ("|a", "Missing operand before '|'"),
    ("a|", "Missing operand after '|'"),
    ("*a", "nothing to repeat"),
    ("a$b", "Unexpected character"),
])
def test_errors(regex, message):
    with pytest.raises(RegexError, match=re.escape(message)):
        build(regex)


# ---- known textbook results --------------------------------------------------

@pytest.mark.parametrize("regex, nfa, dfa, min_dfa", [
    ("(a|b)*abb", 14, 5, 4),     # Dragon Book, Example 3.24 / 3.40
    ("a*b*", 8, 3, 2),
    ("(aa+bb)*", 12, 5, 3),
    ("a**", 6, 2, 1),
])
def test_state_counts(regex, nfa, dfa, min_dfa):
    p = build(regex)
    assert (len(p.nfa.states), len(p.dfa.states), len(p.min_dfa.states)) == (nfa, dfa, min_dfa)


def test_min_dfa_is_deterministic():
    p = build("(a|b)*a(a|b)(a|b)")
    for machine in (p.dfa, p.min_dfa):
        assert not machine.has_epsilon
        for by_sym in machine.transitions.values():
            assert all(len(t) == 1 for t in by_sym.values())


# ---- language equivalence against Python's own regex engine ---------------------

REGEXES = ["(a|b)*abb", "(aa+bb)*", "a*b*", "(a|b)*a(a|b)", "(ab|ba)*", "a(b|ε)c",
           "(a|ε)(b|ε)", "((a|b)(a|b))*", "(a*b*)*", "a*(ba*ba*)*", "ε", "(0|1)*00"]


def to_python_regex(regex):
    out = []
    for tok in tokenize(regex):
        out.append({TokenType.UNION: "|", TokenType.EPSILON: "(?:)"}.get(tok.type, tok.value))
    return "".join(out)


def all_strings(alphabet, max_len):
    for n in range(max_len + 1):
        for chars in itertools.product(alphabet, repeat=n):
            yield "".join(chars)


@pytest.mark.parametrize("regex", REGEXES)
def test_all_machines_match_python_re(regex):
    p = build(regex)
    oracle = re.compile(to_python_regex(regex))
    alphabet = p.nfa.alphabet or ["a"]
    for s in all_strings(alphabet, 7):
        expected = oracle.fullmatch(s) is not None
        for machine in (p.nfa, p.dfa, p.min_dfa):
            assert simulate(machine, s).accepted == expected, (regex, machine.kind, s)


def test_symbol_outside_alphabet_is_rejected():
    t = simulate(build("ab").min_dfa, "ac")
    assert not t.accepted and "not in the alphabet" in t.halted
