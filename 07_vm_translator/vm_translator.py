import argparse
from io import TextIOWrapper
import random
from pathlib import Path
from typing import Literal, cast
from collections.abc import Iterator
from dataclasses import dataclass

CommandType = Literal["arithmetic", "push", "pop", "label", "goto", "if-goto", "function", "return", "call"]
SEGMENT_POINTERS = {"local": "LCL", "argument": "ARG", "this": "THIS", "that": "THAT"}
SEGMENT_BASE = {"pointer": 3, "temp": 5}
ARITHMETIC_TRANSLATIONS = {
    "add": """
@SP
M=M-1

A=M
D=M

@SP
M=M-1

A=M
M=D+M

@SP
M=M+1
""",

    "sub": """
@SP
M=M-1

A=M
D=M

@SP
M=M-1

A=M
M=M-D

@SP
M=M+1
""",
    
    "neg": """
@SP
M=M-1

A=M
M=-M

@SP
M=M+1
""",

    "eq": """
@SP
M=M-1

A=M
D=M

@SP
M=M-1

A=M
D=M-D

@IFGOTO
D;JEQ

@0
D=A
@SP
A=M
M=D

@ENDIF
0;JMP
(IFGOTO)

@0
D=!A
@SP
A=M
M=D

(ENDIF)

@SP
M=M+1
""",

    "gt": """
@SP
M=M-1

A=M
D=M

@SP
M=M-1

A=M
D=M-D

@IFGOTO
D;JGT

@0
D=A
@SP
A=M
M=D

@ENDIF
0;JMP
(IFGOTO)

@0
D=!A
@SP
A=M
M=D

(ENDIF)

@SP
M=M+1
""",     
 
    "lt": """
@SP
M=M-1

A=M
D=M

@SP
M=M-1

A=M
D=M-D

@IFGOTO
D;JLT

@0
D=A
@SP
A=M
M=D

@ENDIF
0;JMP
(IFGOTO)

@0
D=!A
@SP
A=M
M=D

(ENDIF)

@SP
M=M+1
""",

    "and": """
@SP
M=M-1

A=M
D=M

@SP
M=M-1

A=M
M=D&M

@SP
M=M+1
""",
    
    "or": """
@SP
M=M-1

A=M
D=M

@SP
M=M-1

A=M
M=D|M

@SP
M=M+1
""",
    
    "not": """
@SP
M=M-1

A=M
M=!M

@SP
M=M+1
""",
}


@dataclass
class Command:
    ctype: CommandType
    arg1: str | None = None
    arg2: int | None = None


class Parser(Iterator[Command]):
    ARITHMETIC: set[str] = set(
        ["add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"]
    )
    VALID_COMMANDS: set[str] = (
        set(["push", "pop", "label", "goto", "if-goto", "function", "return", "call"])
        | ARITHMETIC
    )

    def __init__(self, file: TextIOWrapper):
        self._file: TextIOWrapper = file
        self._eof: bool = False
        self._current: Command | None = None

    def __iter__(self) -> "Parser":
        return self
        
    def __next__(self) -> Command:
        if self._eof:
            raise StopIteration
            
        command = self._read_next_command()
        if command is None:
            self._eof = True
            raise StopIteration
        
        self._current = command
        return command
        
    def _read_next_command(self) -> Command|None:
        parts: list[str] = []

        while not parts:
            line = self._file.readline()
            if not line:
                return None  # EOF
            # remove comments and split
            line = line.split("//", 1)[0]
            parts = line.split()

        # parse command
        assert parts[0] in self.VALID_COMMANDS, f"{parts[0]} is not a valid command"
        ctype: CommandType = cast(CommandType, parts[0])
        
        arg1: str | None = None
        arg2: int | None = None
    
        if ctype in self.ARITHMETIC:
            arg1 = ctype
            ctype = "arithmetic"
        else:
            if len(parts) > 1:
                arg1 = parts[1]

        if len(parts) > 2:
            arg2 = int(parts[2])

        return Command(ctype, arg1, arg2)


class CodeWriter:
    
    
    def __init__(self, file: TextIOWrapper):
        self.file: TextIOWrapper = file
        self.used_labels = set()
        
    def write(self, command, filename_root):
        if command.ctype == "arithmetic":
            self._write_arithmetic(command)
        elif command.ctype == "push" or command.ctype == "pop":
            self._write_push_pop(command, filename_root)

    def _write_arithmetic(self, command):
        
        assert command.arg1 in ARITHMETIC_TRANSLATIONS, "arg1 is not one of the valid arithmetic operations"
        translation = ARITHMETIC_TRANSLATIONS[command.arg1]
        
        if "ENDIF" in translation:
            translation = self._add_unique_label(translation, "ENDIF")
        if "IFGOTO" in translation:
            translation = self._add_unique_label(translation, "IFGOTO")
        
        self.file.write(f"{translation}\n")
        
    def _add_unique_label(self, translation: str, label: str):
        ROM_SIZE = 32768
        assert label in translation, f"Label {label} is not in translation: \n {translation}"
        unique_label = ""
        while (not unique_label) or (unique_label in self.used_labels):
            unique_label = label + "_" + str(random.randint(0, ROM_SIZE*1000))
        self.used_labels.add(unique_label)
        return translation.replace(label, unique_label)
        
    def _translate_push_constant(self, constant: int):
        assert constant >= 0 and constant <= 32767, f"Constant {constant} is out of range 0...32767"
        return f"""
@{constant}
D=A
@SP
A=M
M=D

@SP
M=M+1
"""
    def _translate_standard_segments(self, command: Command):
        assert command.arg1 in SEGMENT_POINTERS, f"Arg1 {command.arg1} is not a standard segment name"
        base = SEGMENT_POINTERS[command.arg1]
        if command.ctype == "push":
            return f"""
@{base}
D=M
@{command.arg2}
A=D+A
D=M

@SP
A=M
M=D

@SP
M=M+1
"""
        elif command.ctype == "pop":
            return f"""
@{base}
D=M
@{command.arg2}
D=D+A
@RAM13
M=D

@SP
M=M-1
A=M
D=M
@RAM13
A=M
M=D
"""
        
    def _translate_fixed_segments(self, command: Command):
        
        
        assert command.arg1 in SEGMENT_BASE, f"Arg1 {command.arg1} is not a fixed segment name in command {command}"
        assert command.arg2 is not None, f"Arg2 is None in command {command}"
        address = SEGMENT_BASE[command.arg1] + command.arg2
        
        if command.ctype == "push":
            return f"""
@{address}
D=M

@SP
A=M
M=D

@SP
M=M+1
"""
        elif command.ctype == "pop":
            return f"""
@SP
M=M-1
A=M
D=M

@{address}
M=D
"""

    def _translate_static(self, command: Command, filename_root: str):
        assert filename_root, "VM filename cannot be empty for mapping static variable"
        assert command.arg2 is not None, f"Arg2 is None in command {command}"
        variable_name = filename_root + "." + str(command.arg2)
        
        if command.ctype == "push":
            return f"""
@{variable_name}
D=M

@SP
A=M
M=D

@SP
M=M+1
"""
        elif command.ctype == "pop":
            return f"""
@SP
M=M-1
A=M
D=M

@{variable_name}
M=D
"""
        
    def _write_push_pop(self, command, filename_root):
        if command.arg1 == "constant":
            if command.ctype != "push":
                raise ValueError(f"command `{command.ctype}` is invalid for `constant`")
            translation = self._translate_push_constant(command.arg2)
        elif command.arg1 in ("local", "argument", "this", "that"):
            translation = self._translate_standard_segments(command)
        elif command.arg1 in ("pointer", "temp"):
            translation = self._translate_fixed_segments(command)
        elif command.arg1 == "static":
            translation = self._translate_static(command, filename_root)
        else:
            raise ValueError(f"Invalid Arg1 for command {command}")
            
        self.file.write(f"{translation}\n")


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("vm_filename")
    args = arg_parser.parse_args()
    source_filename = args.vm_filename
    source_path = Path(source_filename)

    assert source_path.suffix == ".vm", "input file does not have an .vm extension"
    out_filename = f"{source_path.parent}/{source_path.stem}.asm"

    with open(source_filename, "r") as infile, open(out_filename, "w") as outfile:
        p = Parser(infile)
        c = CodeWriter(outfile)
        for command in p:
            c.write(command, source_path.stem)


if __name__ == "__main__":
    main()
