# coding=utf8
# @author: Matthäus G. Chajdas
# @license: 3-clause BSD

def dumps(o, indent=None):
    _indent = 0
    if indent and indent > 0:
        _indent = indent
    return ''.join (_encode(o, indent=_indent))

def _encode(l, separators=(', ', '\n', ' = '), indent=0, level=0):
    if isinstance (l, str):
        yield '"{}"'.format (str(l))
    elif l is None:
        yield 'null'
    elif l is True:
        yield 'true'
    elif l is False:
        yield 'false'
    elif isinstance (l, int):
        yield str(l)
    elif isinstance (l, float):
        yield str (l)
    elif isinstance (l, (tuple, list)):
        for c in _encodeList (l, separators, indent, level):
            yield c
    elif isinstance (l, dict):
        for c in _encodeDict(l, separators, indent, level):
            yield c
    else:
        raise RuntimeError("Invalid object type")

def _indent(level, indent):
    return ' ' * (level * indent)
    
def _encodeKey(k):
    import string
    hasWhitespace = False
    for c in k:
        if string.whitespace.find (c) != -1:
            hasWhitespace = True
            break
    
    if hasWhitespace:
        return '\"' + k + '\"'
    else:
        return k

def _encodeList(l, separators, indent, level):
    yield '['
    first = True
    for e in l:
        if first:
            first = False
        else:
            yield separators[0]
        yield _indent(level, indent)
        for c in _encode (e, separators, indent, level+1):
            yield c
    yield ']'
    
def _encodeDict(l, separators, indent, level):
    if level > 0:
        yield '{\n'
    first = True
    for (k, v) in l.items ():
        if first:
            first = False
        else:
            yield '\n'
        yield _indent(level, indent)
        yield _encodeKey (k)
        yield separators[2]
        for c in _encode(v, separators,  indent, level+1):
            yield c
    yield '\n'
    yield _indent (level-1, indent)
    if level > 0:
        yield '}'