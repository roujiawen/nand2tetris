from io import TextIOWrapper
from typing import Literal
from tokenizer import LexicalType


TerminalType = LexicalType
NonTerminalType = Literal["class", "classVarDec", "subroutineDec", "parameterList", "subroutineBody", "varDec", "statements", "whileStatement", "ifStatement", "returnStatement", "letStatement", "doStatement", "expression", "term", "expressionList"]

class Node:
    def __init__(self, type_ : TerminalType | NonTerminalType):
        self.type : TerminalType | NonTerminalType = type_
        self.content : str = ""
    
    def __str__(self):
        return f"{self.type}({self.content})"
        
    def write(self, out_file, depth=0) -> None:
        pass
        
    
class TerminalNode(Node):
    def __init__(self, type_ : TerminalType, content : str):
        super().__init__(type_)
        self.content : str = content
        
    @classmethod
    def from_token(cls, t) -> "TerminalNode":
        return cls(t.type, t.name)
    
    def write(self, out_file : TextIOWrapper, depth=0) -> None:
        out_file.write("  " * depth + f"<{self.type}> {
            self.content
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        } </{self.type}>\n")

class NonTerminalNode(Node):
    def __init__(self, type_ : NonTerminalType, children : list[Node]):
        super().__init__(type_)
        self.children : list[Node] = children
    
    def add_children(self, children : list[Node]) -> None:
        assert all(isinstance(each, Node) for each in children)
        self.children += children
    
    def write(self, out_file : TextIOWrapper, depth=0) -> None:
        out_file.write("  " * depth + f"<{self.type}>\n")
        for each in self.children:
            each.write(out_file, depth+1)
        out_file.write("  " * depth + f"</{self.type}>\n")