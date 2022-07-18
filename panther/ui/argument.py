from rich.console import Console
from rich import print as rprint
from rich.panel import Panel
from rich.text import Text
import sys as sys
from typing import Any, TypedDict, Callable, Union, NoReturn
from exceptions import IsNotModeInstance, NotNotCallable , ArgumentIsRequired

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
    func: Callable[[str | list[str]], None] # if arg on INPUT, LIST or SELECT mode pass input

class ArgParser:

    def __init__(self) -> None:
        self._args: dict = {}

    def __str__(self) -> str:
       pass
    
    def __repr__(self) -> str:
        pass

    def __simple_man(self) -> None:
        print(logo)
        console.rule("Info")

    def __help(self) -> None:
        for item in self._args.values():
            print(f"{item['name']}")

    @staticmethod
    def __cli_style(name: str, mode: Mode) -> tuple:
        if mode != Mode.SELECT:
            return f"-{name[0]}", f"--{name}"
        return tuple(name.split(" "))

    @staticmethod
    def proccess_command(command: dict, inp: str | list=None):
        result = command.get('func')(inp)

    def add_arg(self, name: str, desc: str, mode: Mode, func: Callable[[str | list[str]], Union[str, None]]=None, required=False, **setting: dict) -> None:
        if not callable(func):
            raise NotNotCallable(f"{func} is not callable")
        # if not isinstance(mode, Mode):
        #     raise IsNotModeInstance(f"{mode} is not Mode Instance")

        name = self.__cli_style(name, mode)
        self._args[(name, required, mode)] = Arg(
            name=name,
            desc=desc,
            mode=mode,
            func=func,
            required=required,
            setting=Setting(**setting)
        )

    def parser(self, argv: list):
        try:
            if argv[1] in ("-h", "--help"):
                self.__help()
                return None
        except IndexError:
            self.__simple_man()
            return None

        for item in self._args.items():

            name: tuple = item[0][0]
            required: bool = item[0][1]
            mode: Mode = item[0][2]

            for i, arg in enumerate(argv):                    
                if arg in name:
                    match mode:
                        case Mode.SELECT:
                            self.proccess_command(item[1], arg)
                            continue
                        case Mode.INPUT | Mode.LIST:
                            self.proccess_command(item[1], argv.pop(i+1))
                            continue
                        case Mode.FLAG:
                            self.proccess_command(item[1])
                            continue
                else:
                    if required is True:
                        raise ArgumentIsRequired(f"{' '.join(item[1].get())}")
