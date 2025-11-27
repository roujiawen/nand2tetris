from typing import cast
from collections.abc import Iterator
from io import TextIOWrapper

from models import Command, CommandType

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

