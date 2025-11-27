import argparse
from io import TextIOWrapper

from pathlib import Path
from typing import Literal, cast
from collections.abc import Iterator
from dataclasses import dataclass

CommandType = Literal["arithmetic", "push", "pop", "label", "goto", "if-goto", "function", "return", "call"]
SEGMENT_POINTERS = {"local": "LCL", "argument": "ARG", "this": "THIS", "that": "THAT"}
SEGMENT_BASE = {"pointer": 3, "temp": 5}

CMP_TEMPLATE =  """
@SP
AM=M-1
D=M

A=A-1
D=M-D

@IFGOTO
D;{jump}

@SP
A=M-1
M=0

@ENDIF
0;JMP
(IFGOTO)

@SP
A=M-1
M=-1

(ENDIF)
"""

ARITHMETIC_TRANSLATIONS = {
    "add": """
@SP
AM=M-1
D=M

A=A-1
M=D+M
""",

    "sub": """
@SP
AM=M-1
D=M

A=A-1
M=M-D
""",
    
    "neg": """
@SP
A=M-1
M=-M
""",

    "eq":CMP_TEMPLATE.format(jump="JEQ"),

    "gt":CMP_TEMPLATE.format(jump="JGT"),  
 
    "lt": CMP_TEMPLATE.format(jump="JLT"),

    "and": """
@SP
AM=M-1
D=M

A=A-1
M=D&M
""",
    
    "or": """
@SP
AM=M-1
D=M

A=A-1
M=D|M
""",
    
    "not": """
@SP
A=M-1
M=!M
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
        
    def _read_next_command(self) -> Command | None:
        parts: list[str] = []

        while not parts:
            line = self._file.readline()
            if not line:
                return None  # EOF
            # remove comments and split
            line = line.split("//", 1)[0]
            parts = line.split()

        # parse command
        if parts[0] not in self.VALID_COMMANDS:
            raise ValueError(f"{parts[0]} is not a valid command")
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
            try:
                arg2 = int(parts[2])
            except ValueError:
                raise ValueError(f"Invalid integer {parts[2]} in command {parts}") from None

        return Command(ctype, arg1, arg2)


class CodeWriter:
    
    def __init__(self, file: TextIOWrapper):
        self.file: TextIOWrapper = file
        self.vm_filename: str = ""
        self.label_counter: dict[str, int] = {}
    
    def set_vm_filename(self, vm_filename: str):
        self.vm_filename = vm_filename
        
    def write(self, command: Command):
        if command.ctype == "arithmetic":
            self._write_arithmetic(command)
        elif command.ctype == "push" or command.ctype == "pop":
            self._write_push_pop(command)
    
    def _write_arithmetic(self, command: Command):
        
        if command.arg1 not in ARITHMETIC_TRANSLATIONS:
            raise ValueError("arg1 is not one of the valid arithmetic operations")
        translation = ARITHMETIC_TRANSLATIONS[command.arg1]
        
        if "ENDIF" in translation:
            translation = self._add_unique_label(translation, "ENDIF")
        if "IFGOTO" in translation:
            translation = self._add_unique_label(translation, "IFGOTO")
        
        self.file.write(f"{translation}\n")
        
    def _add_unique_label(self, translation: str, base_label: str):
        assert base_label in translation, f"Label {base_label} is not in translation: \n {translation}"
        
        if base_label not in self.label_counter:
            self.label_counter[base_label] = 0
        
        self.label_counter[base_label] += 1
        unique_label = f"{base_label}_{self.label_counter[base_label]}"
        
        return translation.replace(base_label, unique_label)
        
    def _translate_push_constant(self, constant: int):
        if constant < 0 or constant > 32767:
            raise ValueError(f"Constant {constant} is out of range 0...32767")
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
        if command.arg1 not in SEGMENT_POINTERS:
            raise ValueError(f"Arg1 {command.arg1} is not a standard segment name")
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
@R13
M=D

@SP
M=M-1
A=M
D=M
@R13
A=M
M=D
"""
        
    def _translate_fixed_segments(self, command: Command):
        if command.arg1 not in SEGMENT_BASE:
            raise ValueError(f"Arg1 {command.arg1} is not a fixed segment name in command {command}")
        if command.arg2 is None:
            raise ValueError(f"Arg2 is None in command {command}")
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
    def _translate_static(self, command: Command):
        if not self.vm_filename:
            raise ValueError("VM filename cannot be empty for mapping static variable @Xxx.i")
        if command.arg2 is None:
            raise ValueError(f"Arg2 is None in command {command}")
        variable_name = self.vm_filename + "." + str(command.arg2)
        
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
        
    def _write_push_pop(self, command: Command):
        if command.arg2 is None:
            raise ValueError(f"Missing constant value in command {command}")
        if command.arg1 == "constant":
            if command.ctype != "push":
                raise ValueError(f"command `{command.ctype}` is invalid for `constant`")
            translation = self._translate_push_constant(command.arg2)
        elif command.arg1 in ("local", "argument", "this", "that"):
            translation = self._translate_standard_segments(command)
        elif command.arg1 in ("pointer", "temp"):
            translation = self._translate_fixed_segments(command)
        elif command.arg1 == "static":
            translation = self._translate_static(command)
        else:
            raise ValueError(f"Invalid Arg1 for command {command}")
            
        self.file.write(f"{translation}\n")

def translate_file(vm_path: Path, code_writer: CodeWriter):
    with open(vm_path, "r") as infile:
        parser = Parser(infile)
        code_writer.set_vm_filename(vm_path.stem)
        
        for command in parser:
            code_writer.write(command)

def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("vm_filename")
    args = arg_parser.parse_args()
    source_path = Path(args.vm_filename)
    out_filename = f"{source_path.parent}/{source_path.stem}.asm"
    
    with open(out_filename, "w") as outfile:
        code_writer = CodeWriter(outfile)
        if source_path.is_dir():
                for each_vm_path in source_path.glob("*.vm"):
                    translate_file(each_vm_path, code_writer)
        elif source_path.is_file() and source_path.suffix == ".vm":
            print("File")
            translate_file(source_path, code_writer)
        else:
            raise ValueError("input path is invalid (must be either a directory or a .vm file)")

if __name__ == "__main__":
    main()
