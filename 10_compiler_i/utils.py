from builtins import IOError
from argparse import ArgumentParser
import functools
from pathlib import Path
from typing import Callable

def log_match(func: Callable) -> Callable:
    """Decorator that logs function inputs and outputs"""
    
    @functools.wraps(func)
    def wrapper(self_, tokenizer, index : int = 0) -> bool:
        
        if hasattr(self_, "look_ahead"):
            index_log = f" (look_ahead={getattr(self_, "look_ahead")}, index={index})" if index != 0 else ""
        else:
            index_log = f" (index={index})" if index != 0 else ""
        
        print(f"Matching {self_}{index_log}...")
        result = func(self_, tokenizer, index=index)
        if result:
            print(f"{self_}{index_log} matched!")
        else:
            print(f"{self_}{index_log} not matched!")
        
        return result
    
    return wrapper

def log_resolve(func: Callable) -> Callable:
    """Decorator that logs function inputs and outputs"""
    
    @functools.wraps(func)
    def wrapper(self_, tokenizer) -> list:
        
        print(f"Resolving {self_}...")
        result = func(self_, tokenizer)
        print(f"{self_} resolved!")
        
        return result
    
    return wrapper

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
