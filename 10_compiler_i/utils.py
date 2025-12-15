from builtins import IOError
from argparse import ArgumentParser
from pathlib import Path

class JackSyntaxError(Exception):
    def __init__(self, tokenizer, message, *args: object) -> None:
        message = f"{tokenizer.filename} Line {tokenizer.line_count}: {message}"
        super().__init__(message, *args)

class TokenizerError(Exception):
    pass


def rf_process(call_function, ext):
    """Apply call_function to arg.source which is either a file with given ext or a folder with such files"""
    arg_parser = ArgumentParser()
    arg_parser.add_argument("source")
    arg = arg_parser.parse_args()
    
    source = arg.source
    source_path = Path(source)
    
    if source_path.is_dir():
        for each in source_path.glob(f"*.{ext}"):
            source_path = Path(each)
            if source_path.suffix == f".{ext}":
                call_function(source_path)          
    else:
        if source_path.suffix != f".{ext}":
            raise IOError(f"Source must be a directory or a .{ext} file")
        call_function(source_path)