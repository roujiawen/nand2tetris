from tokenizer import Token, Tokenizer
from typing import override
from terminals import Identifier, IntegerConstant, Keyword, StringConstant, Symbol
from nodes import Node, NonTerminalNode, NonTerminalType, TerminalNode
from utils import JackSyntaxError


class NonTerminalSyntax:
    def __init__(self):
        self.type : NonTerminalType
        self.syntax : list = []
    
    def __str__(self):
        return f"{self.type}()"
        
    def _instantiate_syntax(self):
        pass
        
    def resolve(self, tokenizer) -> list[Node]:
        print("Resolving", self)
        if not self.syntax:
            self._instantiate_syntax()
        node = NonTerminalNode(self.type, [])
        for ele in self.syntax:
            node.add_children(ele.resolve(tokenizer))
        return [node]
    
    def match(self, t):
        if not self.syntax:
            self._instantiate_syntax()
        if self.syntax[0].match(t):
            print(self, "matched!")
            return True
        return False
        
class Expression(NonTerminalSyntax):
    """
    term (op term)*
    """
    def __init__(self):
        super().__init__()
        self.type = "expression"
        
    def _instantiate_syntax(self):
        # self.syntax = [
        #     Term(),
        #     OptionalOrMore([Operator(), Term()])
        # ]
        self.syntax = [
            Term()
        ]
        # self.syntax = [
        #     OneOf([
        #         Identifier(),
        #         ClassName(),
        #         SubroutineName(),
        #         VarName(),
        #         KeywordConstant(),
        #     ])
            
        # ]

class ExpressionList(NonTerminalSyntax):
    """
    (expression (',' expression)* )?
    """
    def __init__(self):
        super().__init__()
        self.type = "expressionList"
    
    def _instantiate_syntax(self):  
        self.syntax = [
            Optional([
                Expression(),
                OptionalOrMore([
                    Symbol(","),
                    Expression()
                ])
            ])
        ]

class Term(NonTerminalSyntax):
    """
    integerConstant | stringConstant | keywordConstant | varName | varName '[' expression
    ']' | subroutineCall | '(' expression ')' | unaryOp term
    """
    def __init__(self):
        super().__init__()
        self.type = "term"
        
    def _instantiate_syntax(self):
        self.syntax = [
            OneOf([
                IntegerConstant(),
                StringConstant(),
                KeywordConstant(),
                VarName(),
                Serial([
                    VarName(), 
                    Symbol("["),
                    Expression(),
                    Symbol("]"),
                ]),
                SubroutineCall(),
                Serial([
                    Symbol("("),
                    Expression(),
                    Symbol(")"),
                ]),
                Serial([
                    UnaryOperator(),
                    Term()
                ]),
            ])
        ]

class Optional:
    def __init__(self, seq : list):
        self.seq = seq
    
    def resolve(self, tokenizer) -> list[Node]:
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

class OptionalOrMore:
    def __init__(self, seq : list):
        self.seq = seq
    
    def resolve(self, tokenizer) -> list[Node]:
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

class Serial:
    def __init__(self, seq : list):
        self.seq = seq
        self.type = "Serial" #TODO: not right
    
    def resolve(self, tokenizer) -> list[Node]:
        result = []
        for ele in self.seq:
            result += ele.resolve(tokenizer)
        return result
    
    def match(self, t: Token) -> bool:
        if self.seq[0].match(t):
            return True
        return False

class OneOf:
    def __init__(self, options : list):
        super().__init__()
        self.options = options
        
    def match(self, t) -> bool:
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
        
class SubroutineCall(OneOf):
    """
    subroutineName '(' expressionList ')' | ( className | varName) '.' subroutineName '('
    expressionList ')'
    """
    def __init__(self):
        options = [
            Serial([
                SubroutineName(),
                Symbol("("),
                ExpressionList(),
                Symbol(")"),
            ]),
            Serial([
                OneOf([ClassName(), VarName()]),
                Symbol("."),
                SubroutineName(),
                Symbol("("),
                ExpressionList(),
                Symbol(")"),
            ])
        ]
        super().__init__(options)
        self.type = "subroutineCall"
    
    @override
    def resolve(self, tokenizer : Tokenizer) -> list[Node]:
        print("Resolving", "subroutineCall()")
        second_token = tokenizer.peek(index=1)
        if Symbol(".").match(second_token):
            option = self.options[1]
        else:
            option = self.options[0]
        
        result = option.resolve(tokenizer)
        return result

class Type_(OneOf):
    """
    'int' | 'char' | 'boolean' | className
    """
    def __init__(self):
        options = [Keyword("int"), Keyword("char"), Keyword("boolean"), ClassName()]
        super().__init__(options)
        self.type = "type"
        
class KeywordConstant(OneOf):
    """
    'true' | 'false' | 'null' | 'this'
    """
    def __init__(self):
        options = [Keyword("true"), Keyword("false"), Keyword("null"), Keyword("this")]
        super().__init__(options)
        self.type = "keywordConstant"
        
class Operator(OneOf):
    """
    '+' | '-' | '*' | '/' | '&' | '|' | '<' | '>' | '='
    """
    def __init__(self):
        options = [
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
        self.type = "op"

class UnaryOperator(OneOf):
    """
    '-' | '~'
    """
    def __init__(self):
        options = [
            Symbol("-"),
            Symbol("~")
        ]
        super().__init__(options)
        self.type = "unaryOp"

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
    VALID_CLASS_NAMES = {"Math", "String", "Array", "Output", "Screen", "Keyboard", "Memory", "Sys"}
    def __init__(self):
        super().__init__()
        
    @classmethod
    def add(cls, new_name):
        cls.VALID_CLASS_NAMES.add(new_name)
        
    @override
    def match(self, t):
        if (self.expected_type == t.type) and (t.name in ClassName.VALID_CLASS_NAMES):
            return True
        return False
    
    @override
    def resolve(self, tokenizer) -> list[Node]:
        # print("Class Names:", ClassName.VALID_CLASS_NAMES)
        t = tokenizer.next()
        self._validate_type(t, tokenizer.line_count)
        name_not_valid = t.name not in ClassName.VALID_CLASS_NAMES
        if name_not_valid:
            raise JackSyntaxError(tokenizer, "Expected valid class name")
        return [TerminalNode.from_token(t)]