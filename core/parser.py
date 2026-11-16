"""Recursive-descent parser: tokens -> AST.

Grammar (operator precedence: * binds tightest, then ., then |):

    expr   -> term   ( '|' term )*
    term   -> factor ( '.' factor )*
    factor -> base '*'*
    base   -> SYMBOL | 'ε' | '(' expr ')'

Each non-terminal is one method below, which is what makes this a
recursive-descent parser.
"""

from .ast_nodes import Concat, Epsilon, Star, Symbol, Union
from .lexer import RegexError, TokenType, insert_concat, tokenize


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.i = 0

    # helpers ---------------------------------------------------------------
    def peek(self):
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def previous(self):
        return self.tokens[self.i - 1] if self.i > 0 else None

    def accept(self, ttype):
        tok = self.peek()
        if tok is not None and tok.type == ttype:
            self.i += 1
            return tok
        return None

    def end_pos(self):
        last = self.tokens[-1]
        return last.pos + 1

    # grammar ---------------------------------------------------------------
    def parse(self):
        node = self.expr()
        tok = self.peek()
        if tok is not None:
            if tok.type == TokenType.RPAREN:
                raise RegexError("Unmatched ')'", tok.pos)
            raise RegexError(f"Unexpected '{tok.value}'", tok.pos)
        return node

    def expr(self):
        node = self.term()
        while self.accept(TokenType.UNION):
            node = Union(node, self.term())
        return node

    def term(self):
        node = self.factor()
        while self.accept(TokenType.CONCAT):
            node = Concat(node, self.factor())
        return node

    def factor(self):
        node = self.base()
        while self.accept(TokenType.STAR):
            node = Star(node)
        return node

    def base(self):
        tok = self.peek()
        if tok is None:
            prev = self.previous()
            if prev is not None and prev.type == TokenType.UNION:
                raise RegexError("Missing operand after '|'", prev.pos)
            raise RegexError("Unexpected end of expression", self.end_pos())

        if self.accept(TokenType.SYMBOL):
            return Symbol(tok.value)
        if self.accept(TokenType.EPSILON):
            return Epsilon()
        if self.accept(TokenType.LPAREN):
            if self.peek() is not None and self.peek().type == TokenType.RPAREN:
                raise RegexError("Empty group '()'", tok.pos)
            node = self.expr()
            if not self.accept(TokenType.RPAREN):
                raise RegexError("Unmatched '('", tok.pos)
            return node

        if tok.type == TokenType.UNION:
            raise RegexError("Missing operand before '|'", tok.pos)
        if tok.type == TokenType.STAR:
            raise RegexError("'*' has nothing to repeat", tok.pos)
        if tok.type == TokenType.RPAREN:
            raise RegexError("Unmatched ')'", tok.pos)
        raise RegexError(f"Unexpected '{tok.value}'", tok.pos)


def parse_tokens(tokens):
    """Parse a token list that already contains explicit CONCAT tokens."""
    return Parser(tokens).parse()


def parse(regex):
    """Convenience wrapper: regex string -> AST."""
    return parse_tokens(insert_concat(tokenize(regex)))
