from typing import Callable
from nodes import Node, NonTerminalNode, NonTerminalType, TerminalNode, TerminalType
from tokenizer import Token, Tokenizer

class JackSyntaxError(Exception):
    def __init__(self, tokenizer, message, *args: object) -> None:
        message = f"{tokenizer.filename} Line {tokenizer.line_count}: {message}"
        super().__init__(message, *args)

class TerminalSyntax:
    def __init__(self) -> None:
        self.expected_type : TerminalType
        self.expected_name : str | None = None
        self.match : Callable
    
    @property
    def type(self):
        return self.expected_type
        
    def __str__(self):
        return f"{self.expected_type}({self.expected_name})"
        
    def _create_syntax_error(self, t : Token, tokenizer : Tokenizer) -> JackSyntaxError:
        if self.expected_name:
            error_message = f"{tokenizer.filename} Line {tokenizer.line_count}: Expected {self.expected_type} `{self.expected_name}`, got {t.type} `{t.name}`"
        else:
            error_message = f"{tokenizer.filename} Line {tokenizer.line_count}: Expected {self.expected_type}, got {t.type} `{t.name}`"
        return JackSyntaxError(tokenizer, error_message)
        
    # def _validate_type(self, t, line_num):
    #     type_mismatched = (self.expected_type != t.type)
    #     if type_mismatched:
    #         raise self._create_syntax_error(t, line_num)
            
    # def _validate_name(self, t, line_num):
    #     name_mismatched = (self.expected_name != t.name)
    #     if name_mismatched:
    #         raise self._create_syntax_error(t, line_num)
            
    def _match_type_and_name(self, t):
        if (self.expected_type == t.type) and (self.expected_name == t.name):
            return True
        return False
    
    def _match_type(self, t):
        if (self.expected_type == t.type):
            return True
        return False
    
    def resolve(self, tokenizer) -> list[Node]:
        t = tokenizer.next()
        if not self.match(t):
            raise self._create_syntax_error(t, tokenizer)
        print("Resolved", self, "==", t)
        return [TerminalNode.from_token(t)]

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