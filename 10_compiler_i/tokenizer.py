from builtins import IOError
from argparse import ArgumentParser
from pathlib import Path
import string
from typing import Iterator, Tuple

class Tokenizer:
    SYMBOLS = {'{' , '}' , '(' , ')' , '[' , ']' , '.' , ',' , ';' , '+' , '-' , '*' , '/' , '&' , '|' , '<' , '>' , '=' , '~'}
    
    KEYWORDS = {'class' , 'constructor' , 'function' , 'method' , 'field' , 'static' ,
    'var' , 'int' , 'char' , 'boolean' , 'void' , 'true' , 'false' , 'null' , 'this' ,
    'let' , 'do' , 'if' , 'else' , 'while' , 'return'}
    
    def __init__(self, source_file):
        self.source_file = source_file
        self.line_counter = 0
        self.buffer = ""
        
        self.skip = 0
        self.p = -1
        self.token_chars = []
        self.in_comment = False
        self.multiline = False
        self.in_string = False
        
        self.buffered_token : None | Tuple[str, str] = None
        
        self.eof = False
        
    def _get_token(self) -> str:
        token = "".join(self.token_chars)
        self.token_chars = []
        return token
        
    def _get_typed_token(self) -> None | Tuple[str, str]:
        token = self._get_token()
        if not token:
            return None
        
        # Identify its type
        if token in Tokenizer.KEYWORDS:
            return "keyword", token
        
        try:
            integer = int(token)
            if 0 <= integer <= 32767:
                return "integerConstant", token
            else:
                raise ValueError(f"Line {self.line_counter}: Integer out of range 0...32767")
        except ValueError:
            if token[0] in string.digits:
                raise ValueError(f"Line {self.line_counter}: Identifier cannot start with a digit")
                
            is_valid_identifier = all(c.isalnum() or c == '_' for c in token)
            if not is_valid_identifier:
                raise ValueError(f"Line {self.line_counter}: Identifier must be a sequence of letters, digits, and underscore")
                
            return "identifier", token
    
    def tokens(self) -> Iterator[Tuple[str, str]]:
        while not self.eof:
            token_or_none = self._next_char()
            if token_or_none:
                yield token_or_none
        
    def _next_char(self) -> None | Tuple[str, str]:
        """Process the next character (unless there is a parsed token buffered), return None (if token incomplete), or Tuple(token_type, token_content) if a complete token has been extracted.
        """
        
        # Return already parsed buffered token
        if self.buffered_token:
            token = self.buffered_token
            self.buffered_token = None
            return token
        
        self.p += 1
        
        # Skip characters
        if self.skip > 0:
            self.skip -= 1
            return None
        
        # Read next line if previous line is finished
        if self.p == len(self.buffer):
            self.line_counter += 1
            self.buffer = self.source_file.readline()
            if not self.buffer:
                self.eof = True
                return None
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
            return None
        
        # - If inside a string, is string ending?
        if self.in_string:
            if char in ('"', "\n"):
                self.in_string = False
                return "stringConstant", self._get_token()
            self.token_chars.append(char)
            return None
        
        # - If not in a string and not in comment, is comment starting?
        if self.buffer[p:p+2] == "/*":
            self.in_comment = True
            self.multiline = True
            self.skip = 1
            # the start of a comment could be the end of a previous token
            return self._get_typed_token()
        
        if self.buffer[p:p+2] == "//":
            self.in_comment = True
            self.multiline = False
            self.skip = 1
            # the start of a comment could be the end of a previous token
            return self._get_typed_token()
        
        # - if not in a string and not in a comment, is string starting?
        if char == '"':
            self.in_string = True
            return None
                
        # - symbols could end a token
        if char in Tokenizer.SYMBOLS:
            self.buffered_token = ("symbol", char) # to be returned in the next call
            return self._get_typed_token()
        
        # - white space could end a token
        if char in string.whitespace:
            return self._get_typed_token()
        
        # otherwise, part of a keyword, constant, or identifier
        self.token_chars.append(char)
        return None

def generate_tokenized_xml(source_path):
    out_path = source_path.with_suffix(".my.xml")
    with open(source_path, "r") as source_file:
        tokenizer = Tokenizer(source_file)
        with open(out_path, "w") as out_file:
            out_file.write("<tokens>\n")
            for type_, content in tokenizer.tokens():
                out_file.write(f"<{type_}> {
                    content
                    .replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace('"', "&quot;")
                } </{type_}>\n")
            out_file.write("</tokens>\n")

if __name__ == "__main__":
    arg_parser = ArgumentParser()
    arg_parser.add_argument("source")
    arg = arg_parser.parse_args()
    
    source = arg.source
    source_path = Path(source)
    
    if source_path.is_dir():
        for each in source_path.glob("*.jack"):
            source_path = Path(each)
            if source_path.suffix == ".jack":
                generate_tokenized_xml(source_path)          
    else:
        if source_path.suffix != ".jack":
            raise IOError("Source must be a directory or a .jack file")
        with open(source_path, "r") as source_file:
            generate_tokenized_xml(source_path)
       
                
