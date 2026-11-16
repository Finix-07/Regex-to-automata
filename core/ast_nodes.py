"""Abstract syntax tree for regular expressions."""

from dataclasses import dataclass

from .lexer import EPSILON


class Node:
    def children(self):
        return ()

    @property
    def label(self):
        raise NotImplementedError


@dataclass(frozen=True)
class Symbol(Node):
    char: str

    @property
    def label(self):
        return self.char

    def __str__(self):
        return self.char


@dataclass(frozen=True)
class Epsilon(Node):
    @property
    def label(self):
        return EPSILON

    def __str__(self):
        return EPSILON


@dataclass(frozen=True)
class Union(Node):
    left: Node
    right: Node

    def children(self):
        return (self.left, self.right)

    @property
    def label(self):
        return "|"

    def __str__(self):
        return f"({self.left}|{self.right})"


@dataclass(frozen=True)
class Concat(Node):
    left: Node
    right: Node

    def children(self):
        return (self.left, self.right)

    @property
    def label(self):
        return "·"

    def __str__(self):
        return f"{self.left}{self.right}"


@dataclass(frozen=True)
class Star(Node):
    child: Node

    def children(self):
        return (self.child,)

    @property
    def label(self):
        return "*"

    def __str__(self):
        # Symbols, ε and unions (which print their own parentheses) need no extra wrapping.
        if isinstance(self.child, (Symbol, Epsilon, Union)):
            return f"{self.child}*"
        return f"({self.child})*"


def alphabet_of(node):
    """Sorted list of input symbols used in the tree."""
    found = set()
    stack = [node]
    while stack:
        n = stack.pop()
        if isinstance(n, Symbol):
            found.add(n.char)
        stack.extend(n.children())
    return sorted(found)
