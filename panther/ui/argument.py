from typing import TypedDict, Callable
from .exceptions import (
    IsNotModeInstance,
    NotNotCallable,
    ArgumentIsRequired,
    InputRequired,
    ArgvIsNotListOrTuple,
)

__author__ = 'Mahan Bakhshi'
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

descriptions = """Panther Library

"""


class Mode:
    """
    list mode of Argparse Commands Mode
    """

    INPUT = "input"  # -inp "Hello World!", --inp ., inp ~/project/panther
    SELECT = "select"  # run or makeapp or makeproject
    LIST = "list"  # -inp=[2'1','2']
    FLAG = "flag"  # -h or --help response True or False


class Arg(TypedDict):
    """
    Argument fields
    """

    name: tuple  # argument name TODO: Required typing python 3.11
    desc: str  # description for argument
    mode: Mode  # argument mode: FLAG: -h | --help, TODO: Required typing python 3.11
    required: bool  # default is False
    setting: dict  # setting dict use for rich style TODO: NotRequired typing python 3.11
    func: Callable[[str | list[str]], None]  # if arg on INPUT, LIST or SELECT mode pass input
    default: str | list | None


class ArgParser:
    """
    class for argument parser Panther Mixed With Rich and Can use from client for create custom command.
    """

    def __init__(self, cwd):
        self._args = {}
        self.cwd = cwd

    def __str__(self):
        return f"{self._args}"

    def __repr__(self):
        return f"ArgParser({self._args})"

    def __help(self):
        """
        if -h, --help in argv run this function
        """

        print("#help")

    @staticmethod
    def __cli_style(name, mode):
        """
        change name of command to styled
        """

        if mode != Mode.SELECT:
            # and this for another modes
            return f"-{name[0]}", f"--{name}"
        # this style for SELECT mode
        return tuple(name.split(" "))

    @staticmethod
    def __cmd_process(command, data):
        """
        after find commands send it here and run command function.
        """

        try:
            command['func'](data)
        except TypeError:
            command['func']()

    def add_arg(self, name, desc, mode, func=None, required=False, default=None, **setting):
        """
        method for add Argument For parse
        """

        # add_arg Exception Handling
        if mode not in ("input", "select", "list", "flag"):
            raise IsNotModeInstance('mode in not Mode Class Instance.')
        if not callable(func):
            raise NotNotCallable(f"{func} is not callable")

        name = self.__cli_style(name, mode)
        # create command with Arg change data to dict
        self._args[(name, required)] = Arg(
            name=name,
            desc=desc,
            mode=mode,
            func=func,
            required=required,
            default=default,
            setting=setting
        )
        return self

    def parse(self, argv):
        """
        parse function send sys.argv to parse and fun command function
        """

        # parse Exception Handling
        if len(argv) <= 1 or '-h' in argv or '--help' in argv:
            self.__help()
            return
        elif not isinstance(argv, list | tuple):
            raise ArgvIsNotListOrTuple(f"{argv} is not tuple or list")

        # find arguments
        for inx, arg in enumerate(argv[1:]):
            for key, value in self._args.items():
                if arg in key[0]:

                    if value["mode"] in ("input", "list"):
                        try:
                            self.__cmd_process(value, (self.cwd, argv[inx + 1]))
                        except IndexError:
                            InputRequired(f"{arg} need input.")
                    elif value["mode"] == "select":
                        self.__cmd_process(value, (self.cwd, arg))
                    else:
                        self.__cmd_process(value, None)
                elif key[1]:
                    raise ArgumentIsRequired(f"{' '.join(key[0])} This Command Is Required.")
                else:
                    print(f"{arg} Command Not Found.")  # TODO: change to rich
                    return
