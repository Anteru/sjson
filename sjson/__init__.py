# coding=utf8
# @author: Matthäus G. Chajdas
# @license: 3-clause BSD

__version__ = '1.0.0'

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
