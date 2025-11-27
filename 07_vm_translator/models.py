from typing import Literal
from dataclasses import dataclass

CommandType = Literal["arithmetic", "push", "pop", "label", "goto", "if-goto", "function", "return", "call"]


@dataclass
class Command:
    ctype: CommandType
    arg1: str | None = None
    arg2: int | None = None
