"""Lexical analysis of a regular expression.

The lexer turns the raw regex string into a list of tokens and then makes
concatenation explicit by inserting CONCAT tokens, e.g.

    (a|b)*abb   ->   ( a | b ) * . a . b . b
"""

from dataclasses import dataclass
from enum import Enum

EPSILON = "ε"
EPSILON_ALIASES = {"ε", "#"}  # '#' is easier to type than 'ε'
UNION_CHARS = {"|", "+"}      # '+' is union in textbook notation, e.g. (a+b)*


class RegexError(Exception):
    """Raised for any malformed regular expression."""

    def __init__(self, message, pos=None):
        super().__init__(message)
        self.message = message
        self.pos = pos


class TokenType(Enum):
    SYMBOL = "SYMBOL"
    EPSILON = "EPSILON"
    UNION = "UNION"
    STAR = "STAR"
    CONCAT = "CONCAT"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: str
    pos: int

    def __str__(self):
        return self.value


def tokenize(regex):
    """Split the regex into tokens. Whitespace is ignored."""
    tokens = []
    for pos, ch in enumerate(regex):
        if ch.isspace():
            continue
        if ch in UNION_CHARS:
            tokens.append(Token(TokenType.UNION, "|", pos))
        elif ch == "*":
            tokens.append(Token(TokenType.STAR, "*", pos))
        elif ch == "(":
            tokens.append(Token(TokenType.LPAREN, "(", pos))
        elif ch == ")":
            tokens.append(Token(TokenType.RPAREN, ")", pos))
        elif ch in EPSILON_ALIASES:
            tokens.append(Token(TokenType.EPSILON, EPSILON, pos))
        elif ch.isalnum():
            tokens.append(Token(TokenType.SYMBOL, ch, pos))
        else:
            raise RegexError(f"Unexpected character '{ch}'", pos)
    if not tokens:
        raise RegexError("Empty regular expression", 0)
    return tokens


# A concatenation sits between a token that can END an operand and a token
# that can START one: 'ab', 'a(', ')a', ')(', 'a*b', 'a*(' ...
_ENDS_OPERAND = {TokenType.SYMBOL, TokenType.EPSILON, TokenType.STAR, TokenType.RPAREN}
_STARTS_OPERAND = {TokenType.SYMBOL, TokenType.EPSILON, TokenType.LPAREN}


def insert_concat(tokens):
    """Return a new token list with explicit CONCAT ('.') tokens."""
    result = []
    for i, tok in enumerate(tokens):
        if i > 0 and tokens[i - 1].type in _ENDS_OPERAND and tok.type in _STARTS_OPERAND:
            result.append(Token(TokenType.CONCAT, ".", tok.pos))
        result.append(tok)
    return result
