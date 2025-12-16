
        
from typing import ClassVar, override
from base import NonTerminalSyntax, Syntax
from intermediates import ClassName, KeywordConstant, OneOf, Operator, Optional, OptionalOrMore, Serial, SubroutineName, UnaryOperator, VarName
from nodes import Node, NonTerminalType
from terminals import IntegerConstant, StringConstant, Symbol
from tokenizer import Tokenizer
from utils import log_resolve


class Expression(NonTerminalSyntax):
    """
    term (op term)*
    """
    
    TYPE: ClassVar[NonTerminalType] = "expression"
    def __init__(self):
        super().__init__()
        
    @classmethod
    def _make_syntax(cls) -> list[Syntax]:
        return  [
            Term(),
            OptionalOrMore([Operator(), Term()])
        ]

class ExpressionList(NonTerminalSyntax):
    """
    (expression (',' expression)* )?
    """
    
    TYPE: ClassVar[NonTerminalType] = "expressionList"
    
    def __init__(self):
        super().__init__()
    
    @classmethod
    def _make_syntax(cls) -> list[Syntax]:
        return [
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
    
    TYPE: ClassVar[NonTerminalType] = "term"
    
    def __init__(self):
        super().__init__()
        
    @classmethod
    def _make_syntax(cls) -> list[Syntax]:
        return [
            OneOf([
                IntegerConstant(),
                StringConstant(),
                KeywordConstant(),
                Serial([
                    Symbol("("),
                    Expression(),
                    Symbol(")"),
                ]),
                Serial([
                    UnaryOperator(),
                    Term()
                ]),
                SubroutineCall(),
                Serial([
                    VarName(), 
                    Symbol("["),
                    Expression(),
                    Symbol("]"),
                ], look_ahead=1),
                VarName()
            ])
        ]

class SubroutineCall(OneOf):
    """
    subroutineName '(' expressionList ')' | ( className | varName) '.' subroutineName '('
    expressionList ')'
    """
    
    TYPE: ClassVar[str] = "subroutineCall"
    
    def __init__(self):
        options = [
            Serial([
                SubroutineName(),
                Symbol("("),
                ExpressionList(),
                Symbol(")"),
            ], look_ahead=1),
            Serial([
                OneOf([ClassName(), VarName()]),
                Symbol("."),
                SubroutineName(),
                Symbol("("),
                ExpressionList(),
                Symbol(")"),
            ], look_ahead=1)
        ]
        super().__init__(options)
    
    @log_resolve
    @override
    def resolve(self, tokenizer : Tokenizer) -> list[Node]:
        if Symbol(".").match(tokenizer, index=1):
            option = self.options[1]
        else:
            option = self.options[0]
        result = option.resolve(tokenizer)
        return result
        