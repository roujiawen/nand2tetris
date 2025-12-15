from abc import ABC, abstractmethod
from typing import ClassVar, Literal
from nodes import Node, NonTerminalNode, NonTerminalType, TerminalNode, TerminalType
from tokenizer import Token, Tokenizer

class JackSyntaxError(Exception):
    def __init__(self, tokenizer, message, *args: object) -> None:
        message = f"{tokenizer.filename} Line {tokenizer.line_count}: {message}"
        super().__init__(message, *args)
        
class Syntax(ABC):
    @property
    @abstractmethod
    def type(self) -> TerminalType | NonTerminalType | str:
        pass
    
    @abstractmethod  
    def match(self, t : Token) -> bool:
        pass
        
    @abstractmethod
    def resolve(self, tokenizer : Tokenizer) -> list[Node]:
        pass
        
class HelperSyntax(Syntax, ABC):
    TYPE: ClassVar[str]
    
    @property
    def type(self) -> str:
        return self.TYPE

class TerminalSyntax(Syntax, ABC):
    
    # Class variable to select implementation
    MATCH_MODE: ClassVar[Literal["exact_match", "type_match"]]
    TYPE: ClassVar[TerminalType]
    
    @property
    def type(self) -> TerminalType:
        return self.TYPE
        
    def __str__(self):
        if hasattr(self, "name"):
            return f"{self.type}({getattr(self, "name")})"
        else:
            return f"{self.type}()"
        
    def _create_syntax_error(self, t : Token, tokenizer : Tokenizer) -> JackSyntaxError:
        if hasattr(self, "name"):
            error_message = f"{tokenizer.filename} Line {tokenizer.line_count}: Expected {self.type} `{getattr(self, "name")}`, got {t.type} `{t.name}`"
        else:
            error_message = f"{tokenizer.filename} Line {tokenizer.line_count}: Expected {self.type}, got {t.type} `{t.name}`"
        return JackSyntaxError(tokenizer, error_message)
            
    def _match_type_and_name(self, t) -> bool:
        if (self.type == t.type) and (getattr(self, "name") == t.name):
            return True
        return False
    
    def _match_type(self, t) -> bool:
        if (self.type == t.type):
            return True
        return False
        
    def match(self, t) -> bool:
        if self.MATCH_MODE == "exact_match":
            return self._match_type_and_name(t)
        else:
            return self._match_type(t)
    
    def resolve(self, tokenizer) -> list[Node]:
        t = tokenizer.next()
        if not self.match(t):
            raise self._create_syntax_error(t, tokenizer)
        print("Resolved", self, "==", t)
        return [TerminalNode.from_token(t)]

class NonTerminalSyntax(Syntax, ABC):
    # Define as class variable, computed once per class
    _syntax_cache: ClassVar[list[Syntax] | None] = None
    TYPE : ClassVar[NonTerminalType]
    
    @property
    def type(self) -> NonTerminalType:
        return self.TYPE
     
    @property
    def syntax(self) -> list[Syntax]:
        """Get syntax, caching at class level"""
        if self.__class__._syntax_cache is None:
            self.__class__._syntax_cache = self.__class__._make_syntax()
        return self.__class__._syntax_cache
    
    @classmethod
    @abstractmethod
    def _make_syntax(cls) -> list[Syntax]:
        """Factory method for syntax"""
        pass
        
    def __str__(self):
        return f"{self.type}()"
        
    def match(self, t : Token) -> bool:
        if self.syntax[0].match(t):
            print(self, "matched!")
            return True
        return False
        
    def resolve(self, tokenizer : Tokenizer) -> list[Node]:
        print("Resolving", self)
        node = NonTerminalNode(self.type, [])
        for ele in self.syntax:
            node.add_children(ele.resolve(tokenizer))
        return [node]
    
    