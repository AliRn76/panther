from typing import *

class Mode:
    INPUT: str = "input"
    SELECT: str = "select"
    LIST: str = "list"
    FLAG: str = "flag"


class Arg(TypedDict):
    """
    Argument fields
    """

    name: tuple
    desc: str
    mode: Mode
    required: bool
    setting: dict
    func: Callable[[str | list[str]], None]
    default: str | list | None


class ArgParser:
    def __init__(self, cwd: str) -> None: 
        self.cwd: str = ''
        self._args: dict = {}
        ...

    def __str__(self) -> str: ...

    def __repr__(self) -> str: ...

    def __help(self) -> None: ...

    @staticmethod
    def __cli_style(name, mode) -> tuple: ...

    @staticmethod
    def __cmd_process(command: dict, data: Any) -> None: ...

    def add_arg(
        self,
        name: List[str] | str,
        desc: str,
        mode: Mode | str,
        func: Callable[[str | list[str]], Union[str, None]],
        required: bool = False,
        default: Any = None,
        **setting: dict
    ) -> Self: ... # TODO: python 3.11 change return type to self

    def parse(self, argv: list) -> None: ...
