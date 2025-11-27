from typing import Literal
from dataclasses import dataclass

CommandType = Literal["arithmetic", "push", "pop", "label", "goto", "if-goto", "function", "return", "call"]


@dataclass
class Command:
    ctype: CommandType
    arg1: str | None = None #TODO: validate str format e.g. allowed special characters
    arg2: int | None = None
