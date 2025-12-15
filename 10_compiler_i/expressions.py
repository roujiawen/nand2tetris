
        
from typing import ClassVar, override
from base import NonTerminalSyntax, Syntax
from intermediates import ClassName, KeywordConstant, OneOf, Optional, OptionalOrMore, Serial, SubroutineName, UnaryOperator, VarName
from nodes import Node, NonTerminalType
from terminals import IntegerConstant, StringConstant, Symbol
from tokenizer import Tokenizer


class Expression(NonTerminalSyntax):
    """
    term (op term)*
    """
    
    TYPE: ClassVar[NonTerminalType] = "expression"
    def __init__(self):
        super().__init__()
        
    @classmethod
    def _make_syntax(cls) -> list[Syntax]:
        return [
            Term()
        ]
        # self.syntax = [
        #     Term(),
        #     OptionalOrMore([Operator(), Term()])
        # ]
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
        