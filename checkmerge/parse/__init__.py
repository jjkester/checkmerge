import typing

from checkmerge.ir import tree


class ParseError(Exception):
    """
    Exception that is thrown when source code could not be parsed.
    """
    def __init__(self, message, file=None, *args):
        self.file = file
        super(ParseError, self).__init__(message, *args)


class Parser(object):
    """
    Abstract class for parser front ends of CheckMerge.
    """
    key: str = ''
    name: str = ''
    description: str = ''

    def parse(self, obj: object) -> typing.List[tree.IRNode]:
        """
        Parses the input into CheckMerge intermediate representation (IR). May raise a TypeError if the given object is
        not supported.

        :param obj: The object to parse.
        :return: The parsed IR of the object.
        """
        parse_func = None

        if isinstance(obj, typing.IO):
            parse_func = self.parse_stream
        elif isinstance(obj, str):
            parse_func = self.parse_str

        if parse_func is None:
            raise TypeError(f"Objects of type {type(obj)} cannot be parsed.")

        return parse_func(obj)

    def parse_str(self, val: str) -> typing.List[tree.IRNode]:
        """
        Parses the code in the given string into CheckMerge IR.

        :param val: The code to parse.
        :return: The parsed IR.
        """
        raise NotImplementedError()

    def parse_stream(self, stream: typing.IO) -> typing.List[tree.IRNode]:
        """
        Parses the code in the given stream into CheckMerge IR.
        :param stream: The stream containing the code to parse.
        :return: The parsed IR.
        """
        raise NotImplementedError()

    def parse_file(self, path: str) -> typing.List[tree.IRNode]:
        """
        Parses the code in the file on the given path into CheckMerge IR.

        :param path: The file containing the code to parse.
        :return: The parsed IR.
        """
        with open(path) as file:
            return self.parse_stream(file)
