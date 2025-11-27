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
        self.function_name: str = ""
        self.label_counter: dict[str, int] = {}
        self.rtn_addr_counter: int = 0 #for unique return address
        self.sys_init_found: bool = False
        
    def get_bootstrap_code(self):
        translation = """
        // SP=256 // initialize the stack pointer to 0x0100
        @256
        D=A
        @SP
        M=D
        // call Sys.init // invoke Sys.init
        """
        translation += self._formulate_call(Command("call", "Sys.init", 0))
        return translation
    
    def set_vm_filename(self, vm_filename: str):
        self.vm_filename = vm_filename
        self.set_function_name("")
        
    def set_function_name(self, function_name: str):
        # Naive assumption: code is treated as inside a function unless a new function declaration starts
        # TODO: there no clear marker of end of a function in the syntax. how to discern whether a block 
        # of code is still inside a function or in the global environment?
        self.function_name = function_name
        
    def write(self, command: Command):
        self.file.write(f"\n// ################## {command} ##################\n")
        if command.ctype == "arithmetic":
            self._write_arithmetic(command)
        elif command.ctype == "push" or command.ctype == "pop":
            self._write_push_pop(command)
        elif command.ctype == "label":
            self._write_label(command)
        elif command.ctype == "goto":
            self._write_goto(command)
        elif command.ctype == "if-goto":
            self._write_if_goto(command)
        elif command.ctype == "call":
            self._write_call(command)
        elif command.ctype == "function":
            self._write_function(command)
        elif command.ctype == "return":
            self._write_return(command)
    
    def _write_label(self, command: Command):
        function = self.function_name
        label = command.arg1
        translation = f"({function}:{label})"
        self.file.write(f"{translation}\n")
        
    def _write_goto(self, command: Command):
        function = self.function_name
        label = command.arg1
        translation = f"""
        @{function}:{label}
        0;JMP
        """
        self.file.write(f"{translation}\n")
        
    def _write_if_goto(self, command: Command):
        # pop value
        # if the value is not zero, execution continues from the location marked by the label
        function = self.function_name
        label = command.arg1
        translation = f"""
        @SP
        M=M-1
        A=M
        D=M
        @{function}:{label}
        D;JNE
        """
        self.file.write(f"{translation}\n")
    
    def _formulate_call(self, command: Command):
        self.rtn_addr_counter += 1
        return_address = f"RETURN_ADDRESS_{self.rtn_addr_counter}"
        function = command.arg1
        if command.arg2 is None:
            raise ValueError("Second argument of Call command is required")
        num_args = command.arg2
        push_D = """
        @SP
        A=M
        M=D
        @SP
        M=M+1
        """
        translation = f"""
        // push return-address
        @{return_address}
        D=A  
        {push_D}
        
        // push LCL, ARG, THIS, THAT
        @LCL
        D=M
        {push_D}
        @ARG
        D=M
        {push_D}
        @THIS
        D=M
        {push_D}
        @THAT
        D=M
        {push_D}
        
        // ARG = SP-n-5
        @{num_args+5}
        D=A
        @SP
        D=M-D
        @ARG
        M=D
        
        // LCL = SP
        @SP
        D=M
        @LCL
        M=D
        
        // goto f
        @{function}
        0;JMP
        
        //label for the return address
        ({return_address})
        """ 
        return translation
        
    def _write_call(self, command: Command):
        translation = self._formulate_call(command)
        self.file.write(f"{translation}\n")
        
    def _write_function(self, command: Command):
        function = command.arg1
        if function is None:
            raise ValueError("First argument of the function declaration command `function f k` is missing")
        self.set_function_name(function)
        if function == "Sys.init":
            self.sys_init_found = True
        
        num_locals = command.arg2
        if num_locals is None:
            raise ValueError("Second argument of the function declaration command `function f k` is missing")
        
        translation = f"""
({function})
"""
        for i in range(num_locals):
            # Push 0 (initialise all local variables to be zero)
            translation += """
@SP
A=M
M=0
@SP
M=M+1
"""
        
        self.file.write(f"{translation}\n")
        
    def _write_return(self, command: Command):
        
        translation = """
        // FRAME=LCL // FRAME is a temporary variable
        @LCL
        D=M
        @FRAME
        M=D
        // RET=*(FRAME-5) // save return address in a temp. var
        @5
        D=A
        @FRAME
        A=M-D
        D=M
        @RET
        M=D
        // *ARG=pop() // reposition return value for caller
        @SP
        M=M-1
        A=M
        D=M
        @ARG
        A=M
        M=D
        // SP=ARG+1 // restore SP for caller
        @ARG
        D=M+1
        @SP
        M=D
        //THAT=*(FRAME-1) // restore THAT of calling function
        @FRAME
        AM=M-1
        D=M
        @THAT
        M=D
        //THIS=*(FRAME-2) // restore THIS of calling function
        @FRAME
        AM=M-1
        D=M
        @THIS
        M=D
        //ARG=*(FRAME-3) // restore ARG of calling function
        @FRAME
        AM=M-1
        D=M
        @ARG
        M=D
        //LCL=*(FRAME-4) // Restore LCL of calling function
        @FRAME
        A=M-1
        D=M
        @LCL
        M=D
        //goto RET // GOTO the return-address
        @RET
        A=M
        0;JMP
        """
        self.file.write(f"{translation}\n")
            
    
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

