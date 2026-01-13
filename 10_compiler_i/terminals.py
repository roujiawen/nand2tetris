from typing import ClassVar, Literal
from base import TerminalSyntax
from tokenizer import Tokenizer
from nodes import TerminalType


class Keyword(TerminalSyntax):

    MATCH_MODE: ClassVar[Literal["exact_match", "type_match"]] = "exact_match"
    TYPE: ClassVar[TerminalType] = "keyword"

    def __init__(self, name: str):
        super().__init__()
        self.name: str = name
        assert name in Tokenizer.KEYWORDS


class Symbol(TerminalSyntax):

    MATCH_MODE: ClassVar[Literal["exact_match", "type_match"]] = "exact_match"
    TYPE: ClassVar[TerminalType] = "symbol"

    def __init__(self, name: str):
        super().__init__()
        self.name: str = name
        assert name in Tokenizer.SYMBOLS


class Identifier(TerminalSyntax):

    MATCH_MODE: ClassVar[Literal["exact_match", "type_match"]] = "type_match"
    TYPE: ClassVar[TerminalType] = "identifier"  # TODO: how to make this unchanged for subclass?

    def __init__(self):
        super().__init__()


class IntegerConstant(TerminalSyntax):

    MATCH_MODE: ClassVar[Literal["exact_match", "type_match"]] = "type_match"
    TYPE: ClassVar[TerminalType] = "integerConstant"

    def __init__(self):
        super().__init__()


class StringConstant(TerminalSyntax):

    MATCH_MODE: ClassVar[Literal["exact_match", "type_match"]] = "type_match"
    TYPE: ClassVar[TerminalType] = "stringConstant"

    def __init__(self):
        super().__init__()
