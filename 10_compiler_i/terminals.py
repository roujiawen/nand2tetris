from base import TerminalSyntax
from tokenizer import Tokenizer
from nodes import TerminalType

class Keyword(TerminalSyntax):
    def __init__(self, expected_name):
        super().__init__()
        self.expected_type : TerminalType = "keyword"
        self.expected_name : str | None = expected_name
        self.match = self._match_type_and_name
        assert expected_name in Tokenizer.KEYWORDS

class Symbol(TerminalSyntax):
    def __init__(self, expected_name : str):
        super().__init__()
        self.expected_type : TerminalType = "symbol"
        self.expected_name : str | None = expected_name
        self.match = self._match_type_and_name
        assert expected_name in Tokenizer.SYMBOLS

class Identifier(TerminalSyntax):
    def __init__(self):
        super().__init__()
        self.expected_type : TerminalType = "identifier"
        self.match = self._match_type
    
class IntegerConstant(TerminalSyntax):
    def __init__(self):
        super().__init__()
        self.expected_type : TerminalType = "integerConstant"
        self.match = self._match_type

class StringConstant(TerminalSyntax):
    def __init__(self):
        super().__init__()
        self.expected_type : TerminalType = "stringConstant"
        self.match = self._match_type