
from collections import deque
import string
from typing import Iterator, Literal

from utils import rf_process, TokenizerError

LexicalType = Literal["keyword", "symbol", "integerConstant", "stringConstant", "identifier"]

class Token:
    def __init__(self, type_, name):
        self.type = type_
        self.name = name
    
    def __str__(self):
        return f"{self.type} `{self.name}`"

class Tokenizer:
    
    SYMBOLS = {'{' , '}' , '(' , ')' , '[' , ']' , '.' , ',' , ';' , '+' , '-' , '*' , '/' , '&' , '|' , '<' , '>' , '=' , '~'}
    
    KEYWORDS = {'class' , 'constructor' , 'function' , 'method' , 'field' , 'static' ,
    'var' , 'int' , 'char' , 'boolean' , 'void' , 'true' , 'false' , 'null' , 'this' ,
    'let' , 'do' , 'if' , 'else' , 'while' , 'return'}
    
    def __init__(self, source_file, filename):
        self.filename = filename
        self.source_file = source_file
        self.line_count = 0
        self.buffer : str = ""
        
        self.skip = 0
        self.p = -1
        self.token_chars : list[str] = []
        self.in_comment = False
        self.multiline = False
        self.in_string = False
        
        self.buffered_tokens : deque[Token] = deque()
        self.wait_to_add_buffer: Token | None = None
        
        self.eof = False
        
    def _get_token(self) -> str:
        token = "".join(self.token_chars)
        self.token_chars = []
        return token
        
    def _get_typed_token_list(self) -> list[Token]:
        token = self._get_token()
        if not token:
            return []
        
        # Identify its type
        if token in Tokenizer.KEYWORDS:
            return [Token("keyword", token)]
        
        try:
            integer = int(token)
            if 0 <= integer <= 32767:
                return [Token("integerConstant", token)]
            else:
                raise TokenizerError(f"Line {self.line_count}: Integer out of range 0...32767")
        except ValueError:
            if token[0] in string.digits:
                raise TokenizerError(f"Line {self.line_count}: Identifier cannot start with a digit")
                
            is_valid_identifier = all(c.isalnum() or c == '_' for c in token)
            if not is_valid_identifier:
                raise TokenizerError(f"Line {self.line_count}: Identifier must be a sequence of letters, digits, and underscore")
                
            return [Token("identifier", token)]
    
    def peek(self, index=0) -> Token | None:
        size = len(self.buffered_tokens)
        while size <= index:
            token = self.next()
            if token is None:
                return None
            self.buffered_tokens.appendleft(token)
            size = len(self.buffered_tokens)
        print(f"peeked {index}-th token:", self.buffered_tokens[index])
        return self.buffered_tokens[index]
    
    def next(self) -> Token | None:
        # Return already parsed buffered token
        if self.buffered_tokens:
            token = self.buffered_tokens.popleft()
            return token
            
        while not self.eof:
            tokens = self._next_char()
            if tokens:
                self.buffered_tokens += tokens[1:]
                return tokens[0]
        
        return None
    
    def tokens(self) -> Iterator[Token]:
        while True:
            token_or_none = self.next()
            if token_or_none:
                yield token_or_none
            else:
                break
        
    def _next_char(self) -> list[Token]:
        """Process the next character , return [] (if token incomplete), or a list of 1 or 2 Tokens if complete token(s) have been extracted.
        """
        
        self.p += 1
        
        # Skip characters
        if self.skip > 0:
            self.skip -= 1
            return []
        
        # Read next line if previous line is finished
        if self.p == len(self.buffer):
            self.line_count += 1
            self.buffer = self.source_file.readline()
            if not self.buffer:
                self.eof = True
                return []
            self.p = 0
        
        p = self.p
        char = self.buffer[p]
        
        # - If inside a comment, is comment ending?
        if self.in_comment:
            if self.multiline:
                if self.buffer[p:p+2] == "*/":
                    self.in_comment = False
                    self.skip = 1
            else:
                if char == "\n":
                    self.in_comment = False
            # Ignore
            return []
        
        # - If inside a string, is string ending?
        if self.in_string:
            if char in ('"', "\n"):
                self.in_string = False
                return [Token("stringConstant", self._get_token())]
            self.token_chars.append(char)
            return []
        
        # - If not in a string and not in comment, is comment starting?
        if self.buffer[p:p+2] == "/*":
            self.in_comment = True
            self.multiline = True
            self.skip = 1
            # the start of a comment could be the end of a previous token
            return self._get_typed_token_list()
        
        if self.buffer[p:p+2] == "//":
            self.in_comment = True
            self.multiline = False
            self.skip = 1
            # the start of a comment could be the end of a previous token
            return self._get_typed_token_list()
        
        # - if not in a string and not in a comment, is string starting?
        if char == '"':
            self.in_string = True
            return []
                
        # - symbols could end a token
        if char in Tokenizer.SYMBOLS:
             # return the complete token and the symbol after
            return self._get_typed_token_list() + [Token("symbol", char)]
        
        # - white space could end a token
        if char in string.whitespace:
            return self._get_typed_token_list()
        
        # otherwise, part of a keyword, constant, or identifier
        self.token_chars.append(char)
        
        return []

def generate_tokenized_xml(source_path):
    out_path = source_path.with_suffix(".my.xml")
    with open(source_path, "r") as source_file:
        tokenizer = Tokenizer(source_file, source_path)
        with open(out_path, "w") as out_file:
            out_file.write("<tokens>\n")
            for token in tokenizer.tokens():
                out_file.write(f"<{token.type}> {
                    token.name
                    .replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace('"', "&quot;")
                } </{token.type}>\n")
            out_file.write("</tokens>\n")

if __name__ == "__main__":
    # apply generate_tokenized_xml to given .jack file or all .jack files in given directory
    rf_process(generate_tokenized_xml, "jack")
       
                
