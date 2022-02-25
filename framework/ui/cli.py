from argparse import ArgumentParser
from ..metaclasses import Singleton


class CliParser(metaclass=Singleton):
    def __init__(self) -> None:
        self.parser = ArgumentParser(description="")

    @property
    def parser(self) -> ArgumentParser:
        self.__parser.add_argument('', '', help='')
        return self.__parser

    @parser.setter
    def parser(self, new_parser):
        self.__parser = new_parser
