from types import FunctionType
from rich.console import Console, OverflowMethod
from rich import print as rprint
from rich.panel import Panel
from rich.text import Text
import sys as _sys
from typing import Any, TypedDict, Optional, Callable, Union

__all__ = (
    "Mode",
    "ArgParser"
)

logo = r"""
 ____                 __    __                      
/\  _`\              /\ \__/\ \                     
\ \ \L\ \ __      ___\ \ ,_\ \ \___      __   _ __  
 \ \ ,__/'__`\  /' _ `\ \ \/\ \  _ `\  /'__`\/\`'__\
  \ \ \/\ \L\.\_/\ \/\ \ \ \_\ \ \ \ \/\  __/\ \ \/ 
   \ \_\ \__/.\_\ \_\ \_\ \__\\ \_\ \_\ \____\\ \_\ 
    \/_/\/__/\/_/\/_/\/_/\/__/ \/_/\/_/\/____/ \/_/
"""

console = Console(
    width=51
)

class Mode:
    INPUT = "input" # inp="Hello World!", inp=., inp=~/project/panther
    SELECT = "select" # run or makeapp or makeproject
    LIST = "list" # -inp=[2'1','2'] 
    FLAG = "flag" # -h or --help
 
class Color:
    WHITE = "#"

class Setting(TypedDict):
    color: Color
    style: str

class Arg(TypedDict):
    name: list[str] | str # argument name TODO: Requiered typing python 3.11 
    desc: str # description for argument
    mode: Mode # argument mode: FLAG: -h | --help, TODO: Requiered typing python 3.11
    required: bool # default is False
    setting: Setting # setting dict use for rich style TODO: Requiered typing python 3.11
    func: Callable[[str | list[str]], Union[str, None]] # if arg on INPUT or LIST mode pass input

class ArgParser:

    def __init__(self) -> None:
        self.__args: list = []

    def parser(self):
        ...

    def help(self):
        print(logo)
        console.rule("Commands")
        for item in self.__args:
            ...

    def style_name(name: str, mode: Mode) -> str | list:
        ... 

    def add_arg(self, name: str, desc: str, mode: Mode, required=False, **setting: dict) -> None:
        match mode:
            case Mode.FLAG:
                ...
            case Mode.LIST:
                ...
            case Mode.SELECT:
                ...
            case Mode.INPUT:
                ...
        
