from io import TextIOWrapper

from models import Command

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

