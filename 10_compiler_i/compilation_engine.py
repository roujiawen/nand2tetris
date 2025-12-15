
from pathlib import Path
from terminals import Keyword, Symbol
from tokenizer import Tokenizer
from utils import rf_process

from intermediates import ClassName, Expression, NonTerminalSyntax, Optional, OptionalOrMore, OneOf, Serial, SubroutineCall, SubroutineName, Type_, VarName




class Class(NonTerminalSyntax):
    def __init__(self):
        """
        'class' className '{' classVarDec* subroutineDec* '}'
        """
        super().__init__()
        self.type = "class"
        
    def _instantiate_syntax(self):#TODO use @property instead?
        self.syntax = [
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
    def __init__(self):
        super().__init__()
        self.type = "classVarDec" # TODO: would func.__qualname__.split("_")[0] work?
        
    def _instantiate_syntax(self):
        self.syntax = [
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
    def __init__(self):
        super().__init__()
        self.type = "subroutineDec"
        
    def _instantiate_syntax(self):
        self.syntax = [
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
    def __init__(self):
        super().__init__()
        self.type = "parameterList"
    
    def _instantiate_syntax(self):
        self.syntax = [
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
    def __init__(self):
        super().__init__()
        self.type = "subroutineBody"
    
    def _instantiate_syntax(self):
        self.syntax = [
            Symbol("{"),
            OptionalOrMore([VarDec()]),
            Statements(),
            Symbol("}")
        ]

class VarDec(NonTerminalSyntax):
    """
    'var' type varName (',' varName)* ';'
    """
    def __init__(self):
        super().__init__()
        self.type = "varDec"
    
    def _instantiate_syntax(self):
        self.syntax = [
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
    def __init__(self):
        super().__init__()
        self.type = "statements"
        
    def _instantiate_syntax(self):
        self.syntax = [
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
    def __init__(self):
        super().__init__()
        self.type = "letStatement"
        
    def _instantiate_syntax(self):
        self.syntax = [
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
    def __init__(self):
        super().__init__()
        self.type = "ifStatement"
    
    def _instantiate_syntax(self):
        self.syntax = [
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
    def __init__(self):
        super().__init__()
        self.type = "whileStatement"
    
    def _instantiate_syntax(self):
        self.syntax = [
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
    def __init__(self):
        super().__init__()
        self.type = "doStatement"
    
    def _instantiate_syntax(self):
        self.syntax = [
            Keyword("do"),
            SubroutineCall(),
            Symbol(";")
        ]

class ReturnStatement(NonTerminalSyntax):
    """
    'return' expression? ';'
    """
    def __init__(self):
        super().__init__()
        self.type = "returnStatement"
        
    def _instantiate_syntax(self):
        self.syntax = [
            Keyword("return"),
            Optional([Expression()]),
            Symbol(";")
        ]


        
class CompilationEngine:
    def __init__(self, tokenizer: Tokenizer, out_path: Path):
        self.out_path = out_path
        self.tokenizer = tokenizer
        self.class_names = {"Main"}
        self.cached_lines = []
        
    def flush(self):
        with open(self.out_path, "w") as out_file:
            for line in self.cached_lines:
                out_file.write(f"{line}\n")
        self.cached_lines = []
    
    def writeline(self, line, flush=False):
        self.cached_lines.append(line)
        if flush or len(self.cached_lines) > 500:
            with open(self.out_path, "w") as out_file:
                for line in self.cached_lines:
                    out_file.write(f"{line}\n")
            self.cached_lines = []
    
    def write_terminal(self, token):
        type_, content = token
        self.writeline(f"<{type_}> {
            content
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        } </{type_}>")
            

def collect_class_names(source_path : Path):
    ClassName.add(source_path.stem)
            
def generate_compiled_xml(source_path):
    out_path = source_path.with_suffix(".my.xml")
    with open(source_path, "r") as source_file:
        tokenizer = Tokenizer(source_file, source_path)
        root_node = Class().resolve(tokenizer)[0]
        with open(out_path, "w") as out_file:
            root_node.write(out_file)
    
if __name__ == "__main__":
    # apply generate_tokenized_xml to given .jack file or all .jack files in given directory
    rf_process(collect_class_names, "jack")
    rf_process(generate_compiled_xml, "jack")