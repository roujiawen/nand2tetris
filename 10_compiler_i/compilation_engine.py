
from pathlib import Path
from typing import ClassVar
from base import JackSyntaxError, NonTerminalSyntax, Syntax
from expressions import Expression, SubroutineCall
from nodes import NonTerminalType
from terminals import Keyword, Symbol
from tokenizer import NoMoreTokens, Tokenizer
from utils import rf_process

from intermediates import ClassName, Optional, OptionalOrMore, OneOf, Serial, SubroutineName, Type_, VarName


class Class(NonTerminalSyntax):
    """
    'class' className '{' classVarDec* subroutineDec* '}'
    """
    
    TYPE: ClassVar[NonTerminalType] = "class"
    
    def __init__(self):
        super().__init__()
    
    @classmethod
    def _make_syntax(cls) -> list[Syntax]:
        return [
            Keyword("class"),
            ClassName(),
            Symbol("{"),
            OptionalOrMore([ClassVarDec()]),
            OptionalOrMore([SubroutineDec()]),
            Symbol("}")
        ]
    
class ClassVarDec(NonTerminalSyntax):
    """
    ('static' | 'field' ) type varName (',' varName)* ';'
    """
    
    TYPE: ClassVar[NonTerminalType] = "classVarDec"
    
    def __init__(self):
        super().__init__()
        
    @classmethod
    def _make_syntax(cls) -> list[Syntax]:
        return [
            OneOf([Keyword("static"), Keyword("field")]),
            Type_(),
            VarName(),
            OptionalOrMore([Symbol(","), VarName()]),
            Symbol(";")
        ]
    
class SubroutineDec(NonTerminalSyntax):
    """
    ('constructor' | 'function' | 'method') ('void' | type) subroutineName '('
    parameterList ')' subroutineBody
    """
    
    TYPE: ClassVar[NonTerminalType] = "subroutineDec"
    
    def __init__(self):
        super().__init__()
        
    @classmethod
    def _make_syntax(cls) -> list[Syntax]:
        return [
            OneOf([Keyword("constructor"), Keyword("function"), Keyword("method")]),
            OneOf([Keyword("void"), Type_()]),
            SubroutineName(),
            Symbol("("),
            ParameterList(),
            Symbol(")"),
            SubroutineBody()
        ]

class ParameterList(NonTerminalSyntax):
    """
    ( (type varName) (',' type varName)*)?
    """
    
    TYPE: ClassVar[NonTerminalType] = "parameterList"
    
    def __init__(self):
        super().__init__()
    
    @classmethod
    def _make_syntax(cls) -> list[Syntax]:
        return [
            Optional([
                Serial([
                    Type_(),
                    VarName()
                ]),
                OptionalOrMore([
                    Symbol(","),
                    Type_(),
                    VarName()
                ])
            ])
        ]

class SubroutineBody(NonTerminalSyntax):
    """
    '{' varDec* statements '}'
    """
    
    TYPE: ClassVar[NonTerminalType] = "subroutineBody"
    
    def __init__(self):
        super().__init__()
    
    @classmethod
    def _make_syntax(cls) -> list[Syntax]:
        return [
            Symbol("{"),
            OptionalOrMore([VarDec()]),
            Statements(),
            Symbol("}")
        ]

class VarDec(NonTerminalSyntax):
    """
    'var' type varName (',' varName)* ';'
    """
    
    TYPE: ClassVar[NonTerminalType] = "varDec"
    
    def __init__(self):
        super().__init__()
    
    @classmethod
    def _make_syntax(cls) -> list[Syntax]:
        return [
            Keyword("var"),
            Type_(),
            VarName(),
            OptionalOrMore([Symbol(","), VarName()]),
            Symbol(";")
        ]
        
class Statements(NonTerminalSyntax):
    """
    (letStatement | ifStatement | whileStatement | doStatement | returnStatement)*
    """
    
    TYPE: ClassVar[NonTerminalType] = "statements"
    
    def __init__(self):
        super().__init__()
        
    @classmethod
    def _make_syntax(cls) -> list[Syntax]:
        return [
            OptionalOrMore([OneOf([
                LetStatement(),
                IfStatement(),
                WhileStatement(),
                DoStatement(),
                ReturnStatement()
            ])])
        ]

class LetStatement(NonTerminalSyntax):
    """
    'let' varName ('[' expression ']')? '=' expression ';'
    """
    
    TYPE: ClassVar[NonTerminalType] = "letStatement"
    
    def __init__(self):
        super().__init__()
        
    @classmethod
    def _make_syntax(cls) -> list[Syntax]:
        return [
            Keyword("let"),
            VarName(),
            Optional([Symbol("["), Expression() ,Symbol("]")]),
            Symbol("="),
            Expression(),
            Symbol(";"),
        ]

class IfStatement(NonTerminalSyntax):
    """
    'if' '(' expression ')' '{' statements '}' ( 'else' '{' statements '}' )?
    """
    
    TYPE: ClassVar[NonTerminalType] = "ifStatement"
    
    def __init__(self):
        super().__init__()
    
    @classmethod
    def _make_syntax(cls) -> list[Syntax]:
        return [
            Keyword("if"),
            Symbol("("),
            Expression(),
            Symbol(")"),
            Symbol("{"),
            Statements(),
            Symbol("}"),
            Optional([Keyword("else"), Symbol("{"), Statements(), Symbol("}")])
        ]
        
class WhileStatement(NonTerminalSyntax):
    """
    'while' '(' expression ')' '{' statements '}'
    """
    
    TYPE: ClassVar[NonTerminalType] = "whileStatement"
    
    def __init__(self):
        super().__init__()
    
    @classmethod
    def _make_syntax(cls) -> list[Syntax]:
        return [
            Keyword("while"),
            Symbol("("),
            Expression(),
            Symbol(")"),
            Symbol("{"),
            Statements(),
            Symbol("}")
        ]

class DoStatement(NonTerminalSyntax):
    """
    'do' subroutineCall ';'
    """
    
    TYPE: ClassVar[NonTerminalType] = "doStatement"
    
    def __init__(self):
        super().__init__()
    
    @classmethod
    def _make_syntax(cls) -> list[Syntax]:
        return [
            Keyword("do"),
            SubroutineCall(),
            Symbol(";")
        ]

class ReturnStatement(NonTerminalSyntax):
    """
    'return' expression? ';'
    """
    
    TYPE: ClassVar[NonTerminalType] = "returnStatement"
    
    def __init__(self):
        super().__init__()
        
    @classmethod
    def _make_syntax(cls) -> list[Syntax]:
        return [
            Keyword("return"),
            Optional([Expression()]),
            Symbol(";")
        ]


# class CompilationEngine:
#     def __init__(self, tokenizer: Tokenizer, out_path: Path):
#         self.out_path = out_path
#         self.tokenizer = tokenizer
#         self.class_names = {"Main"}
#         self.cached_lines = []
        
#     def flush(self):
#         with open(self.out_path, "w") as out_file:
#             for line in self.cached_lines:
#                 out_file.write(f"{line}\n")
#         self.cached_lines = []
    
#     def writeline(self, line, flush=False):
#         self.cached_lines.append(line)
#         if flush or len(self.cached_lines) > 500:
#             with open(self.out_path, "w") as out_file:
#                 for line in self.cached_lines:
#                     out_file.write(f"{line}\n")
#             self.cached_lines = []
    
#     def write_terminal(self, token):
#         type_, content = token
#         self.writeline(f"<{type_}> {
#             content
#             .replace("&", "&amp;")
#             .replace("<", "&lt;")
#             .replace(">", "&gt;")
#             .replace('"', "&quot;")
#         } </{type_}>")
            

def collect_class_names(source_path : Path):
    ClassName.add(source_path.stem)
            
def generate_compiled_xml(source_path):
    out_path = source_path.with_suffix(".my.xml")
    with open(source_path, "r") as source_file:
        tokenizer = Tokenizer(source_file, source_path)
        try:
            root_node = Class().resolve(tokenizer)[0]
        except NoMoreTokens:
            raise JackSyntaxError(tokenizer, "Unfinished script.")
        with open(out_path, "w") as out_file:
            root_node.write(out_file)
    
if __name__ == "__main__":
    # apply generate_tokenized_xml to given .jack file or all .jack files in given directory
    rf_process(collect_class_names, "jack")
    rf_process(generate_compiled_xml, "jack")