from builtins import IOError
import functools
import logging
from pathlib import Path
from typing import Any, Callable, cast

LOG_FILE = Path(__file__).with_name("compiler_debug.log")

logger = logging.getLogger("nand2tetris.compiler")
logger.setLevel(logging.DEBUG)
logger.propagate = False
logger.disabled = True
logger.addHandler(logging.NullHandler())


def configure_debug_logging(enabled: bool) -> None:
    """Toggle debug logging to the file handler based on CLI flag."""
    logger.disabled = not enabled
    if not enabled:
        return

    has_file_handler = any(isinstance(h, logging.FileHandler) for h in logger.handlers)
    if not has_file_handler:
        file_handler = logging.FileHandler(LOG_FILE, mode="a")
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


def log_match(func: Callable) -> Callable:
    """Decorator that logs function inputs and outputs"""

    @functools.wraps(func)
    def wrapper(self_, tokenizer, index: int = 0) -> bool:

        if hasattr(self_, "look_ahead"):
            index_log = (
                f" (look_ahead={getattr(self_, 'look_ahead')}, index={index})" if index != 0 else ""
            )
        else:
            index_log = f" (index={index})" if index != 0 else ""

        logger.debug("Matching %s%s...", self_, index_log)
        result = func(self_, tokenizer, index=index)
        if result:
            logger.debug("%s%s matched!", self_, index_log)
        else:
            logger.debug("%s%s not matched!", self_, index_log)

        return cast(bool, result)

    return wrapper


def log_resolve(func: Callable) -> Callable:
    """Decorator that logs function inputs and outputs"""

    @functools.wraps(func)
    def wrapper(self_, tokenizer) -> list[Any]:

        logger.debug("Resolving %s...", self_)
        result = func(self_, tokenizer)
        logger.debug("%s resolved!", self_)

        return cast(list[Any], result)

    return wrapper


def rf_process(call_function, source, ext):
    """Apply call_function to arg.source which is either a file with given ext or a folder with such files"""

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
