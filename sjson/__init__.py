"""Module to parse SJSON files."""
# @author: Matthäus G. Chajdas
# @license: 3-clause BSD

import collections.abc
from abc import abstractmethod
import collections
import numbers
import string
import io
from enum import Enum
import typing

__version__ = '2.2.0'


class _InputStream:
    @abstractmethod
    def read(self, count: int = 1) -> bytes: ...

    @abstractmethod
    def skip(self, count: int = 1): ...

    @abstractmethod
    def peek(self, count: int = 1, allow_end_of_stream=False) -> bytes | None:
        pass

    @abstractmethod
    def get_location(self) -> tuple[int, int]: ...


class MemoryInputStream(_InputStream):
    """Input stream wrapper for reading directly from memory."""

    def __init__(self, s: bytes):
        """
        s -- a bytes object.
        """
        self._stream = s
        self._current_index = 0
        self._length = len(s)

    def read(self, count=1) -> bytes:
        """read ``count`` bytes from the stream."""
        end_index = self._current_index + count
        if end_index > self._length:
            _raise_end_of_stream_exception(self)
        result = self._stream[self._current_index : end_index]
        self._current_index = end_index
        return result

    def peek(self, count=1, allow_end_of_stream=False) -> bytes | None:
        """peek ``count`` bytes from the stream. If ``allow_end_of_stream`` is
        ``True``, no error will be raised if the end of the stream is reached
        while trying to peek."""
        end_index = self._current_index + count
        if end_index > self._length:
            if allow_end_of_stream:
                return None
            _raise_end_of_stream_exception(self)

        return self._stream[self._current_index : end_index]

    def skip(self, count=1):
        """skip ``count`` bytes."""
        self._current_index += count

    def get_location(self) -> tuple[int, int]:
        """Get the current location in the stream."""
        loc = collections.namedtuple('loc', ['line', 'column'])
        bytes_read = self._stream[: self._current_index]
        line = 1
        column = 1
        for byte in bytes_read:
            # We test the individual bytes here, must use ord
            if byte == ord('\n'):
                line += 1
                column = 1
            else:
                column += 1
        return loc(line, column)


class ByteBufferInputStream(_InputStream):
    """Input stream wrapper for reading directly from an I/O object."""

    def __init__(self, stream: io.BufferedReader):
        self._stream = stream
        self._index = 0
        self._line = 1
        self._column = 1

    def read(self, count=1) -> bytes:
        """read ``count`` bytes from the stream."""
        result = self._stream.read(count)
        if len(result) < count:
            _raise_end_of_stream_exception(self)

        for char in result:
            # We test the individual bytes here, must use ord
            if char == ord('\n'):
                self._line += 1
                self._column = 1
            else:
                self._column += 1
        return result

    def peek(self, count=1, allow_end_of_stream=False) -> bytes | None:
        """peek ``count`` bytes from the stream. If ``allow_end_of_stream`` is
        ``True``, no error will be raised if the end of the stream is reached
        while trying to peek."""
        result = self._stream.peek(count)
        if not result and not allow_end_of_stream:
            _raise_end_of_stream_exception(self)
        elif not result and allow_end_of_stream:
            return None

        return result[:count]

    def skip(self, count=1):
        """skip ``count`` bytes."""
        self.read(count)

    def get_location(self) -> tuple[int, int]:
        """Get the current location in the stream."""
        loc = collections.namedtuple('loc', ['line', 'column'])
        return loc(self._line, self._column)


class ParseException(RuntimeError):
    """Parse exception."""

    def __init__(self, msg: str, location: tuple[int, int]):
        super(ParseException, self).__init__(msg)
        self._msg = msg
        self._location = location

    def get_location(self) -> tuple[int, int]:
        """Get the current location at which the exception occurred."""
        return self._location

    def __str__(self):
        return '{} at line {}, column {}'.format(
            self._msg, self._location.line, self._location.column
        )


def _raise_end_of_stream_exception(stream: _InputStream) -> typing.NoReturn:
    raise ParseException('Unexpected end-of-stream', stream.get_location())


def _consume(stream: _InputStream, what: bytes):
    _skip_whitespace(stream)
    what_len = len(what)
    if stream.peek(what_len) != what:
        raise ParseException(
            "Expected to read '{}'".format(what.decode('utf-8')), stream.get_location()
        )
    stream.skip(what_len)


def _skip_characters_and_whitespace(stream: _InputStream, num_char_to_skip: int):
    stream.skip(num_char_to_skip)
    return _skip_whitespace(stream)


# Frozenset of b' \t\n\r' yields a frozen set of integers, but we want a
# frozen set of bytes so we need to enumerate them here
_WHITESPACE_SET = frozenset([b' ', b'\t', b'\n', b'\r'])


def _is_whitespace(char):
    return char in _WHITESPACE_SET


def _skip_c_style_comment(stream: _InputStream):
    comment_start_location = stream.get_location()
    # skip the comment start
    stream.skip(2)
    # we don't support nested comments, so we're not going to
    # count the nesting level. Instead, skip ahead until we
    # find a closing */
    while True:
        next_char = stream.peek(1, allow_end_of_stream=True)
        if next_char == b'*':
            comment_end = stream.peek(2, allow_end_of_stream=True)
            if comment_end == b'*/':
                stream.skip(2)
                break
            else:
                stream.skip()
        elif next_char is None:
            raise ParseException(
                "Could not find closing '*/' for comment", comment_start_location
            )
        stream.skip()


def _skip_cpp_style_comment(stream: _InputStream):
    # skip the comment start
    stream.skip(2)
    while True:
        next_char = stream.peek(allow_end_of_stream=True)
        if next_char is None or next_char == b'\n':
            break
        stream.skip()


def _skip_whitespace(stream: _InputStream):
    """skip whitespace. Returns the next character if a new position within the
    stream was found; returns None if the end of the stream was hit."""
    while True:
        next_char = stream.peek(allow_end_of_stream=True)
        if not _is_whitespace(next_char):
            if next_char == b'/':
                # this could be a C or C++ style comment
                comment_start = stream.peek(2, allow_end_of_stream=True)
                if comment_start == b'/*':
                    _skip_c_style_comment(stream)
                    continue
                elif comment_start == b'//':
                    _skip_cpp_style_comment(stream)
                    continue
            break
        stream.skip()

    return next_char


_IDENTIFIER_SET = frozenset(string.ascii_letters + string.digits + '_')


def _is_identifier(obj):
    return chr(obj[0]) in _IDENTIFIER_SET


def _decode_escaped_character(char):
    match char:
        case b'b':
            return b'\b'
        case b'n':
            return b'\n'
        case b't':
            return b'\t'
        case b'\\' | b'"':
            return char
        case _:
            # If we get here, it's an invalid escape sequence. We will simply
            # return it as-if it was not invalid (i.e. \l for instance will get
            # turned into \\l)
            return b'\\' + char


class RawQuoteStyle(Enum):
    Lua = 1
    Python = 2


def _decode_string(stream: _InputStream, allow_identifier=False):
    # When we enter here, we either start with " or [, or there is no quoting
    # enabled.
    _skip_whitespace(stream)

    result = bytearray()

    is_quoted = stream.peek() == b'"' or stream.peek() == b'['
    if not allow_identifier and not is_quoted:
        raise ParseException('Quoted string expected', stream.get_location())

    raw_quotes = None
    # Try Python-style, """ delimited strings
    if is_quoted and stream.peek(3) == b'"""':
        stream.skip(3)
        raw_quotes = RawQuoteStyle.Python
    # Try Lua-style, [=[ delimited strings
    elif is_quoted and stream.peek(3) == b'[=[':
        stream.skip(3)
        raw_quotes = RawQuoteStyle.Lua
    elif is_quoted and stream.peek() == b'"':
        stream.skip()
    elif is_quoted:
        #
        raise ParseException(
            'Invalid quoted string, must start with ",' '""", or [=[',
            stream.get_location(),
        )

    parse_as_identifier = not is_quoted

    while True:
        next_char = stream.peek()
        if parse_as_identifier and not _is_identifier(next_char):
            break

        if raw_quotes:
            if (
                raw_quotes == RawQuoteStyle.Python
                and next_char == b'"'
                and stream.peek(3) == b'"""'
            ):
                # This is a tricky case -- we're in a """ quoted string, and
                # we spotted three consecutive """. This could mean we're at the
                # end, but it doesn't have to be -- we actually need to check
                # all the cases below:
                #   * """: simple case, just end here
                #   * """": A single quote inside the string,
                #     followed by the end marker
                #   * """"": A double double quote inside the string,
                #     followed by the end marker
                # Note that """""" is invalid, no matter what follows
                # afterwards, as the first group of three terminates the string,
                # and then we'd have an unrelated string afterwards. We don't
                # concat strings automatically so this will trigger an error
                # Start with longest match, as the other is prefix this has
                # to be the first check
                if stream.peek(5, allow_end_of_stream=True) == b'"""""':
                    result += b'""'
                    stream.skip(5)
                    break
                elif stream.peek(4, allow_end_of_stream=True) == b'""""':
                    result += next_char
                    stream.skip(4)
                    break
                stream.skip(3)
                break
            elif (
                raw_quotes == RawQuoteStyle.Lua
                and next_char == b']'
                and stream.peek(3) == b']=]'
            ):
                stream.skip(3)
                break
            else:
                assert next_char is not None
                result += next_char
                stream.skip(1)
        else:
            if next_char == b'"':
                stream.read()
                break
            elif next_char == b'\\':
                stream.skip()
                result += _decode_escaped_character(stream.read())
            else:
                assert next_char is not None
                result += next_char
                stream.skip()

    return str(result, encoding='utf-8')


_NUMBER_SEPARATOR_SET = _WHITESPACE_SET.union({b',', b']', b'}', None})


def _decode_number(stream: _InputStream, next_char):
    """Parse a number.

    next_char -- the next byte in the stream.
    """
    number_bytes = bytearray()
    is_decimal_number = False

    while True:
        if next_char in _NUMBER_SEPARATOR_SET:
            break

        if next_char == b'.' or next_char == b'e' or next_char == b'E':
            is_decimal_number = True

        number_bytes += next_char
        stream.skip()

        next_char = stream.peek(allow_end_of_stream=True)

    value = number_bytes.decode('utf-8')

    if is_decimal_number:
        return float(value)
    return int(value)


def _decode_dict(stream: _InputStream, delimited=False):
    """
    delimited -- if ``True``, parsing will stop once the end-of-dictionary
                 delimiter has been reached(``}``)
    """
    from collections import OrderedDict

    result = OrderedDict()

    if stream.peek() == b'{':
        stream.skip()

    next_char = _skip_whitespace(stream)

    while True:
        if not delimited and next_char is None:
            break

        if next_char == b'}':
            stream.skip()
            break

        key = _decode_string(stream, True)
        next_char = _skip_whitespace(stream)
        # We allow both '=' and ':' as separators inside maps
        if next_char == b'=' or next_char == b':':
            _consume(stream, next_char)
        value = _parse(stream)
        result[key] = value

        next_char = _skip_whitespace(stream)
        if next_char == b',':
            next_char = _skip_characters_and_whitespace(stream, 1)

    return result


def _parse_list(stream: _InputStream):
    result = []
    # skip '['
    next_char = _skip_characters_and_whitespace(stream, 1)

    while True:
        if next_char == b']':
            stream.skip()
            break

        value = _parse(stream)
        result.append(value)

        next_char = _skip_whitespace(stream)
        if next_char == b',':
            next_char = _skip_characters_and_whitespace(stream, 1)

    return result


def _parse(stream: _InputStream):
    next_char = _skip_whitespace(stream)

    match next_char:
        case b't':
            _consume(stream, b'true')
            return True
        case b'f':
            _consume(stream, b'false')
            return False
        case b'n':
            _consume(stream, b'null')
            return None
        case b'{':
            return _decode_dict(stream, True)
        case b'"':
            return _decode_string(stream)
        case b'[':
            peek = stream.peek(2, allow_end_of_stream=False)
            # second lookup character for [=[]=] raw literal strings
            assert peek is not None
            assert len(peek) == 2
            next_char_2 = peek[1:2]
            if next_char_2 != b'=':
                return _parse_list(stream)
            elif next_char_2 == b'=':
                return _decode_string(stream)

    try:
        return _decode_number(stream, next_char)
    except ValueError:
        raise ParseException('Invalid character', stream.get_location())


def load(stream: io.RawIOBase):
    """Load a SJSON object from a stream.

    The stream is assumed to point to UTF-8 encoded data.
    """
    return _decode_dict(ByteBufferInputStream(io.BufferedReader(stream)))


def loads(text: str):
    """Load a SJSON object from a string."""
    return _decode_dict(MemoryInputStream(text.encode('utf-8')))


def dumps(obj, indent=None) -> str:
    """Dump an object to a string."""
    import io

    stream = io.StringIO()
    dump(obj, stream, indent)
    return stream.getvalue()


def dump(obj, fp: io.TextIOBase, indent: int | None | str = None):
    """Dump an object to a text stream.

    The output is always text, not binary."""
    if not indent:
        _indent = ''
    elif isinstance(indent, int):
        if indent < 0:
            indent = 0
        _indent = ' ' * indent
    else:
        _indent = indent

    for e in _encode(obj, indent=_indent):
        fp.write(e)


_ESCAPE_CHARACTER_SET = {'\n': '\\n', '\b': '\\b', '\t': '\\t', '"': '\\"'}


def _escape_string(obj: str, quote=True) -> typing.Generator[str, None, None]:
    """Escape a string.

    If quote is set, the string will be returned with quotation marks at the
    beginning and end. If quote is set to false, quotation marks will be only
    added if needed(that is, if the string is not an identifier.)"""
    if any([c not in _IDENTIFIER_SET for c in obj]):
        # String must be quoted, even if quote was not requested
        quote = True

    if quote:
        yield '"'

    for key, value in _ESCAPE_CHARACTER_SET.items():
        obj = obj.replace(key, value)

    yield obj

    if quote:
        yield '"'


_SUPPORTED_ENCODE_TYPE: typing.TypeAlias = typing.Union[
    None,
    bool,
    numbers.Number,
    str,
    typing.Sequence['_SUPPORTED_ENCODE_TYPE'],
    typing.Mapping[str, '_SUPPORTED_ENCODE_TYPE'],
]


def _encode(
    obj: _SUPPORTED_ENCODE_TYPE,
    separators: tuple[str, str, str] = (', ', '\n', ' = '),
    indent=0,
    level=0,
):
    match obj:
        case None:
            yield 'null'
        # Must check for true, false before number, as boolean is an instance of
        # Number, and str(obj) would return True/False instead of true/false then
        case True:
            yield 'true'
        case False:
            yield 'false'
        case _ if isinstance(obj, numbers.Number):
            yield str(obj)
        # Strings are also Sequences, but we don't want to encode as lists
        case _ if isinstance(obj, str):
            yield from _escape_string(obj)
        case _ if isinstance(obj, collections.abc.Sequence):
            yield from _encode_list(obj, separators, indent, level)
        case _ if isinstance(obj, collections.abc.Mapping):
            yield from _encode_dict(obj, separators, indent, level)
        case _:
            raise RuntimeError("Unsupported object type")


def _indent(level: int, indent: str):
    return indent * level


def _encode_key(k: str):
    yield from _escape_string(k, False)


def _encode_list(
    obj: typing.Sequence, separators: tuple[str, str, str], indent: str, level: int
):
    yield '['
    first = True
    for element in obj:
        if first:
            first = False
        else:
            yield separators[0]
        yield from _encode(element, separators, indent, level + 1)
    yield ']'


def _encode_dict(
    obj: typing.Mapping, separators: tuple[str, str, str], indent: str, level: int
):
    if level > 0:
        yield '{\n'
    first = True
    for key, value in obj.items():
        if first:
            first = False
        else:
            yield '\n'
        yield _indent(level, indent)
        yield from _encode_key(key)
        yield separators[2]
        yield from _encode(value, separators, indent, level + 1)
    yield '\n'
    yield _indent(level - 1, indent)
    if level > 0:
        yield '}'
