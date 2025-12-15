from tokenizer import Token, Tokenizer
from typing import ClassVar, override
from terminals import Identifier, Keyword, Symbol
from nodes import Node, TerminalNode
from base import HelperSyntax, JackSyntaxError, Syntax


class Optional(HelperSyntax):
    
    TYPE: ClassVar[str] = "optional"
    
    def __init__(self, seq : list[Syntax]):
        super().__init__()
        self.seq : list[Syntax] = seq
    
    def resolve(self, tokenizer : Tokenizer) -> list[Node]:
        result = []
        first_token = tokenizer.peek()
        print("Optional: peeking", first_token)
        if self.seq[0].match(first_token):
            print("Matched", self.seq[0])
            for ele in self.seq:
                result += ele.resolve(tokenizer)
        return result
    
    def match(self, t: Token) -> bool:
        if self.seq[0].match(t):
            return True
        return False

class OptionalOrMore(HelperSyntax):
    
    TYPE: ClassVar[str] = "optionalOrMore"
    
    def __init__(self, seq : list):
        super().__init__()
        self.seq : list[Syntax] = seq
    
    def resolve(self, tokenizer : Tokenizer) -> list[Node]:
        result = []
        match_found = True
        while match_found:
            first_token = tokenizer.peek()
            if self.seq[0].match(first_token):
                for ele in self.seq:
                    result += ele.resolve(tokenizer)
            else:
                match_found = False
        
        return result
    
    def match(self, t: Token) -> bool:
        if self.seq[0].match(t):
            return True
        return False

class Serial(HelperSyntax):
    
    TYPE: ClassVar[str] = "Serial" #TODO: not right
    
    def __init__(self, seq : list):
        super().__init__()
        self.seq : list[Syntax] = seq
    
    def resolve(self, tokenizer) -> list[Node]:
        result = []
        for ele in self.seq:
            result += ele.resolve(tokenizer)
        return result
    
    def match(self, t: Token) -> bool:
        if self.seq[0].match(t):
            return True
        return False

class OneOf(HelperSyntax):
    
    TYPE: ClassVar[str] = "oneOf"
    
    def __init__(self, options : list):
        super().__init__()
        self.options : list[Syntax] = options
        
    def match(self, t : Token) -> bool:
        if any(o.match(t) for o in self.options):
            print("OneOf() matched!")
            return True
        return False
        
    def resolve(self, tokenizer : Tokenizer) -> list[Node]:
        print("Resolving", "OneOf()")
        first_token = None
        for option in self.options:
            first_token = tokenizer.peek()
            print("Peeking token:", first_token)
            if option.match(first_token):
                print("Option matched:", option)
                result = option.resolve(tokenizer)
                return result
        
        options_text = ", ".join((o.type) for o in self.options)
        error_message = f"Must be one of the following: {options_text}. Instead found {first_token}."
        raise JackSyntaxError(tokenizer, error_message)    
        


class Type_(OneOf):
    """
    'int' | 'char' | 'boolean' | className
    """
    
    TYPE: ClassVar[str] = "type"
    
    def __init__(self):
        options : list[Syntax] = [Keyword("int"), Keyword("char"), Keyword("boolean"), ClassName()]
        super().__init__(options)
        
class KeywordConstant(OneOf):
    """
    'true' | 'false' | 'null' | 'this'
    """
    
    TYPE: ClassVar[str] = "keywordConstant"
    
    def __init__(self):
        options : list[Syntax] = [Keyword("true"), Keyword("false"), Keyword("null"), Keyword("this")]
        super().__init__(options)
        
class Operator(OneOf):
    """
    '+' | '-' | '*' | '/' | '&' | '|' | '<' | '>' | '='
    """
    
    TYPE: ClassVar[str] = "op"
    
    def __init__(self):
        options : list[Syntax] = [
            Symbol("+"), 
            Symbol("-"), 
            Symbol("*"), 
            Symbol("/"), 
            Symbol("&"), 
            Symbol("|"), 
            Symbol("<"), 
            Symbol(">"), 
            Symbol("=")
        ]
        super().__init__(options)

class UnaryOperator(OneOf):
    """
    '-' | '~'
    """
    
    TYPE: ClassVar[str] = "unaryOp"
    
    def __init__(self):
        options : list[Syntax] = [
            Symbol("-"),
            Symbol("~")
        ]
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
    _class_name_registry = {"Math", "String", "Array", "Output", "Screen", "Keyboard", "Memory", "Sys"}
    def __init__(self):
        super().__init__()
        
    @classmethod
    def add(cls, new_name):
        cls._class_name_registry.add(new_name)
        
    @override
    def match(self, t : Token) -> bool:
        if (self.type == t.type) and (t.name in ClassName._class_name_registry):
            return True
        return False
    
    @override
    def resolve(self, tokenizer : Tokenizer) -> list[Node]:
        t = tokenizer.next()
        if not self.match(t):
            raise JackSyntaxError(tokenizer, "Expected valid class name")
        return [TerminalNode.from_token(t)]