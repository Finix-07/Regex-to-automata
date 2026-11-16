"""The full compiler-style pipeline: regex -> tokens -> AST -> ε-NFA -> DFA -> Min-DFA."""

from dataclasses import dataclass

from .ast_nodes import Node
from .automaton import Automaton
from .dfa import subset_construction
from .lexer import insert_concat, tokenize
from .minimize import minimize
from .nfa import thompson
from .parser import parse_tokens


@dataclass
class Pipeline:
    regex: str
    tokens: list
    tokens_with_concat: list
    ast: Node
    nfa: Automaton
    dfa: Automaton
    min_dfa: Automaton


def build(regex):
    """Raises lexer.RegexError on invalid input."""
    tokens = tokenize(regex)
    with_concat = insert_concat(tokens)
    ast = parse_tokens(with_concat)
    nfa = thompson(ast)
    dfa = subset_construction(nfa)
    return Pipeline(regex, tokens, with_concat, ast, nfa, dfa, minimize(dfa))
