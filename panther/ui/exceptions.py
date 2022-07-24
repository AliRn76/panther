class ArgParserException(Exception):
    pass


class NotNotCallable(ArgParserException):
    pass


class ArgumentIsRequired(ArgParserException):
    pass


class IsNotModeInstance(ArgParserException):
    pass


class InputRequired(ArgParserException):
    pass


class ArgvIsNotListOrTuple(ArgParserException):
    pass
