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
        
    def write(self, out_file, depth=0):
        pass
        
    
class TerminalNode(Node):
    def __init__(self, type_ : TerminalType, content : str):
        super().__init__(type_)
        self.content = content
        
    @classmethod
    def from_token(cls, t):
        return cls(t.type, t.name)
    
    def write(self, out_file, depth=0):
        out_file.write("  " * depth + f"<{self.type}> {
            self.content
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        } </{self.type}>\n")

class NonTerminalNode(Node):
    def __init__(self, type_ : NonTerminalType, children):
        super().__init__(type_)
        self.children = children
    
    def add_children(self, children : list[Node]):
        assert all(isinstance(each, Node) for each in children)
        self.children += children
    
    def write(self, out_file, depth=0):
        out_file.write("  " * depth + f"<{self.type}>\n")
        for each in self.children:
            each.write(out_file, depth+1)
        out_file.write("  " * depth + f"</{self.type}>\n")