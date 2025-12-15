from tokenizer import Token, Tokenizer
from typing import override
from nodes import Node, TerminalNode, TerminalType
from utils import JackSyntaxError

class TerminalSyntax:
    def __init__(self) -> None:
        self.expected_type : TerminalType
        self.expected_name : str | None = None
    
    @property
    def type(self):
        return self.expected_type
        
    def __str__(self):
        return f"{self.expected_type}({self.expected_name})"
        
    def match(self, t):
        if (self.expected_type == t.type) and (self.expected_name == t.name):
            return True
        return False
        
    def _create_syntax_error(self, t : Token, tokenizer : Tokenizer) -> JackSyntaxError:
        if self.expected_name:
            error_message = f"{tokenizer.filename} Line {tokenizer.line_count}: Expected {self.expected_type} `{self.expected_name}`, got {t.type} `{t.name}`"
        else:
            error_message = f"{tokenizer.filename} Line {tokenizer.line_count}: Expected {self.expected_type}, got {t.type} `{t.name}`"
        return JackSyntaxError(tokenizer, error_message)
        
    def _validate_type(self, t, line_num):
        type_mismatched = (self.expected_type != t.type)
        if type_mismatched:
            raise self._create_syntax_error(t, line_num)
            
    def _validate_name(self, t, line_num):
        name_mismatched = (self.expected_name != t.name)
        if name_mismatched:
            raise self._create_syntax_error(t, line_num)
    
    def resolve(self, tokenizer) -> list[Node]:
        t = tokenizer.next()
        self._validate_type(t, tokenizer.line_count)
        self._validate_name(t, tokenizer.line_count)
        print("Resolved", self, "==", t)
        return [TerminalNode.from_token(t)]

class Keyword(TerminalSyntax):
    def __init__(self, expected_name):
        super().__init__()
        self.expected_type : TerminalType = "keyword"
        self.expected_name : str | None = expected_name
        assert expected_name in Tokenizer.KEYWORDS

class Symbol(TerminalSyntax):
    def __init__(self, expected_name : str):
        super().__init__()
        self.expected_type : TerminalType = "symbol"
        self.expected_name : str | None = expected_name
        assert expected_name in Tokenizer.SYMBOLS

class Identifier(TerminalSyntax):
    def __init__(self):
        super().__init__()
        self.expected_type : TerminalType = "identifier"
    
    @override
    def match(self, t):
        if (self.expected_type == t.type):
            return True
        return False

    @override
    def resolve(self, tokenizer) -> list[Node]:
        t = tokenizer.next()
        self._validate_type(t, tokenizer.line_count)
        print("Resolved", self, "==", t)
        return [TerminalNode.from_token(t)]
    

class IntegerConstant(TerminalSyntax):
    def __init__(self):
        super().__init__()
        self.expected_type : TerminalType = "integerConstant"
    
    @override
    def resolve(self, tokenizer) -> list[Node]:
        t = tokenizer.next()
        self._validate_type(t, tokenizer.line_count)
        return [TerminalNode.from_token(t)]

class StringConstant(TerminalSyntax):
    def __init__(self):
        super().__init__()
        self.expected_type : TerminalType = "stringConstant"
    
    @override
    def resolve(self, tokenizer) -> list[Node]:
        t = tokenizer.next()
        self._validate_type(t, tokenizer.line_count)
        return [TerminalNode.from_token(t)]