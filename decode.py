# coding=utf8
# @author: Matthäus G. Chajdas
# @license: 3-clause BSD

def _RaiseEndOfFile ():
    raise RuntimeError ("Unexpected end-of-file reached")

def _Consume(text, index, what):
    index = _SkipWhitespace (text, index)
    assert text[index:index+len(what)] == what, "Expected to read '{}' but read '{}' instead".format(what, text[index:index+len(what)])
    return index + len(what)

def _ParseIdentifier(text, index):
    return _ParseString (text, index, True)

def _IsWhitespace (c):
    return c == ' ' or c == '\t' or c == '\n' or c == '\r'

def _SkipWhitespace(text, index):

    while True:
        if index >= len(text):
            return -1

        c = text[index]

        if _IsWhitespace (c):
            index += 1
            continue
        break

    return index

def _IsIdentifier(c):
    import string
    return c in set(string.ascii_letters + string.digits + '_')

def _Peek (text, index):
    try:
        index = _SkipWhitespace (text, index)
        return text[index]
    except:
        return None

def _ParseString(text, index, allowIdentifier = True):
    index = _SkipWhitespace (text, index)

    result = list ()

    if not allowIdentifier and text[index] != '\"':
        raise RuntimeError ("Quoted string expected")

    parseIdentifier = False
    if (text[index] != '\"'):
        index -= 1
        parseIdentifier = True

    while True:
        index += 1
        c = text[index]

        if parseIdentifier and not _IsIdentifier (c):
            break
        if c == '\"':
            index += 1
            break
        elif c == '\\':
            index += 1
            d = text[index]

            if d == 'b':
                result.append ('\b')
            elif d == 'n':
                result.append ('\n')
            elif d == 't':
                result.append ('\t')
            elif d == '\\' or d == '\"':
                result.append (d)

        else:
            result.append (c)

    s = ''.join(result)

    return (index, s)

def _ParseNumber (text, index):
    index = _SkipWhitespace(text, index)

    value = list()
    while True:
        if index == len(text):
            break
        if _IsWhitespace(text[index]) or text[index] == ',' or text[index] == ']' or text[index] == '}':
            break
        else:
            value.append (text[index])
        index += 1

    value = ''.join(value)

    try:
        return (index, int(value))
    except ValueError:
        return (index, float(value))

def _ParseMap (text, index):
    from collections import OrderedDict
    result = OrderedDict()

    while True:
        index = _SkipWhitespace (text, index)
        if (index == -1):
            break
        elif (text[index] == '}'):
            index = _Consume (text, index, '}')
            break

        (index, key) = _ParseString (text, index, True)
        index = _Consume (text, index, '=')
        (index, value) = _Parse (text, index)
        result [key] = value

        if _Peek(text, index) == ',':
            index = _Consume(text, index, ',')
        if index == len(text)-1:
            break

    return (index, result)

def _ParseList (text, index):
    result = []

    while True:
        index = _SkipWhitespace (text, index)
        if index == -1:
            _RaiseEndOfFile ()
        elif text[index] == ']':
            index += 1
            break

        (index, value) = _Parse (text, index)
        result.append (value)

        if _Peek(text, index) == ',':
            index = _Consume (text, index, ',')

    return (index, result)

def _Parse(text, index):
    index = _SkipWhitespace (text, index)

    if index == -1:
        _RaiseEndOfFile()

    c = text[index]
    value = None
    if c == 't':
        index = _Consume (text, index, 'true')
        value = True
    elif c == 'f':
        index = _Consume (text, index, 'false')
        value = False
    elif c == 'n':
        index = _Consume (text, index, 'null')
        value = None
    elif c == '{':
        (index, value) = _ParseMap (text, index+1)
    elif c == '[':
        (index, value) = _ParseList (text, index+1)
    elif c == '\"':
        (index, value) = _ParseString (text, index)
    else:
        try:
            (index, value) = _ParseNumber (text, index)
        except ValueError:
            (index, value) = _ParseString (text, index, True)
    return (index, value)

def loads(text):
    return _ParseMap (text, 0) [1]