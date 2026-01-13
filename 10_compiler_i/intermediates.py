from tokenizer import Tokenizer
from typing import ClassVar, override
from terminals import Identifier, Keyword, Symbol
from nodes import Node, TerminalNode
from base import HelperSyntax, JackSyntaxError, Syntax
from utils import log_match, log_resolve


class Optional(HelperSyntax):

    TYPE: ClassVar[str] = "optional"

    def __init__(self, seq: list[Syntax]):
        super().__init__()
        self.seq: list[Syntax] = seq

    @log_resolve
    def resolve(self, tokenizer: Tokenizer) -> list[Node]:
        result = []
        if self.seq[0].match(tokenizer):
            for ele in self.seq:
                result += ele.resolve(tokenizer)
        return result

    @log_match
    def match(self, tokenizer: Tokenizer, index: int = 0) -> bool:
        if self.seq[0].match(tokenizer, index=index):
            return True
        return False


class OptionalOrMore(HelperSyntax):

    TYPE: ClassVar[str] = "optionalOrMore"

    def __init__(self, seq: list):
        super().__init__()
        self.seq: list[Syntax] = seq

    @log_resolve
    def resolve(self, tokenizer: Tokenizer) -> list[Node]:
        result = []
        match_found = True
        while match_found:
            if self.seq[0].match(tokenizer):
                for ele in self.seq:
                    result += ele.resolve(tokenizer)
            else:
                match_found = False

        return result

    @log_match
    def match(self, tokenizer: Tokenizer, index: int = 0) -> bool:
        if self.seq[0].match(tokenizer, index=index):
            return True
        return False


class Serial(HelperSyntax):

    TYPE: ClassVar[str] = "Serial"  # TODO: not right

    def __init__(self, seq: list, look_ahead: int = 0):
        super().__init__()
        self.seq: list[Syntax] = seq
        self.look_ahead = look_ahead
        assert self.look_ahead < len(self.seq)

    @log_resolve
    def resolve(self, tokenizer) -> list[Node]:
        result = []
        for ele in self.seq:
            result += ele.resolve(tokenizer)
        return result

    @log_match
    def match(self, tokenizer: Tokenizer, index: int = 0) -> bool:
        for i in range(self.look_ahead + 1):
            if not self.seq[i].match(tokenizer, index=index + i):
                return False
        return True


class OneOf(HelperSyntax):

    TYPE: ClassVar[str] = "oneOf"

    def __init__(self, options: list):
        super().__init__()
        self.options: list[Syntax] = options

    @log_match
    def match(self, tokenizer: Tokenizer, index: int = 0) -> bool:
        if any(o.match(tokenizer, index=index) for o in self.options):
            return True
        return False

    @log_resolve
    def resolve(self, tokenizer: Tokenizer) -> list[Node]:
        for option in self.options:
            if option.match(tokenizer):
                result = option.resolve(tokenizer)
                return result

        options_text = ", ".join((o.type) for o in self.options)
        error_message = (
            f"Must be one of the following: {options_text}. Instead found {tokenizer.peek()}."
        )
        raise JackSyntaxError(tokenizer, error_message)


class Type_(OneOf):
    """
    'int' | 'char' | 'boolean' | className
    """

    TYPE: ClassVar[str] = "type"

    def __init__(self):
        options: list[Syntax] = [Keyword("int"), Keyword("char"), Keyword("boolean"), ClassName()]
        super().__init__(options)


class KeywordConstant(OneOf):
    """
    'true' | 'false' | 'null' | 'this'
    """

    TYPE: ClassVar[str] = "keywordConstant"

    def __init__(self):
        options: list[Syntax] = [
            Keyword("true"),
            Keyword("false"),
            Keyword("null"),
            Keyword("this"),
        ]
        super().__init__(options)


class Operator(OneOf):
    """
    '+' | '-' | '*' | '/' | '&' | '|' | '<' | '>' | '='
    """

    TYPE: ClassVar[str] = "op"

    def __init__(self):
        options: list[Syntax] = [
            Symbol("+"),
            Symbol("-"),
            Symbol("*"),
            Symbol("/"),
            Symbol("&"),
            Symbol("|"),
            Symbol("<"),
            Symbol(">"),
            Symbol("="),
        ]
        super().__init__(options)


class UnaryOperator(OneOf):
    """
    '-' | '~'
    """

    TYPE: ClassVar[str] = "unaryOp"

    def __init__(self):
        options: list[Syntax] = [Symbol("-"), Symbol("~")]
        super().__init__(options)


class VarName(Identifier):
    """
    Identifier
    """

    def __init__(self):
        super().__init__()


class SubroutineName(Identifier):
    """
    Identifier
    """

    def __init__(self):
        super().__init__()


class ClassName(Identifier):
    """
    Identifier
    """

    _class_name_registry = {
        "Math",
        "String",
        "Array",
        "Output",
        "Screen",
        "Keyboard",
        "Memory",
        "Sys",
    }

    def __init__(self):
        super().__init__()

    @classmethod
    def add(cls, new_name):
        cls._class_name_registry.add(new_name)

    @log_match
    @override
    def match(self, tokenizer: Tokenizer, index: int = 0) -> bool:
        t = tokenizer.peek(index=index)
        if (self.type == t.type) and (t.name in ClassName._class_name_registry):
            return True
        return False

    @log_resolve
    @override
    def resolve(self, tokenizer: Tokenizer) -> list[Node]:
        if not self.match(tokenizer):
            raise JackSyntaxError(tokenizer, "Expected valid class name")
        t = tokenizer.next()
        return [TerminalNode.from_token(t)]
