# coding=utf8
# @author: Matthäus G. Chajdas
# @license: 3-clause BSD

__version__ = '1.0.3'

import collections.abc
import numbers
import string

def _RaiseEndOfFile ():
	raise RuntimeError ("Unexpected end-of-file reached")

def _Consume(text, index, what):
	index = _SkipWhitespace (text, index)
	assert text[index:index+len(what)] == what, "Expected to read '{}' but read '{}' instead".format(what, text[index:index+len(what)])
	return index + len(what)

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

	isQuoted = text[index] == '\"' or text [index] == '['

	if not allowIdentifier and not isQuoted:
		raise RuntimeError ('Quoted string expected')

	rawQuotes = False
	if text[index] == '[':
		if text[index:index+3] == '[=[':
			rawQuotes = True
		else:
			raise RuntimeError ('Raw quoted string must start with [=[')

	if rawQuotes:
		index += 2

	parseIdentifier = False
	if not isQuoted:
		index -= 1
		parseIdentifier = True

	while True:
		index += 1
		c = text[index]

		if parseIdentifier and not _IsIdentifier (c):
			break

		if c == ']' and rawQuotes:
			if text[index:index+3] == ']=]':
				index+=3
				break

		if rawQuotes:
			result.append (c)
			continue

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
	# second lookup character for [=[]=] raw literal strings
	c2 = None

	if (index+1) < len(text):
		c2 = text [index+1]

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
	elif c == '[' and c2 != '=':
		(index, value) = _ParseList (text, index+1)
	elif c == '[' and c2 == '=':
		(index, value) = _ParseString (text, index)
	elif c == '\"':
		(index, value) = _ParseString (text, index)
	else:
		try:
			(index, value) = _ParseNumber (text, index)
		except ValueError:
			(index, value) = _ParseString (text, index, False)
	return (index, value)

def loads(text):
	return _ParseMap (text, 0) [1]

def dumps(o, indent=None):
	_indent = 0
	if indent and indent > 0:
		_indent = indent
	return ''.join (_encode(o, indent=_indent))

def _escapeString (s, quote=True):
	"""Escape a string.

	If quote is set, the string will be returned with quotation marks at the
	beginning and end. If quote is set to false, quotation marks will be only
	added if needed (that is, if the string contains whitespace.)"""
	if True in [c in s for c in string.whitespace]:
		# String must be quoted, even if quote was not requested
		quote = True

	if quote:
		yield '"'

	for key,value in {'\n':'\\n', '\b':'\\b', '\t':'\\t', '\"':'\\"'}.items ():
		s = s.replace (key, value)

	yield s

	if quote:
		yield '"'

def _encode(l, separators=(', ', '\n', ' = '), indent=0, level=0):
	if l is None:
		yield 'null'
	# Must check for true, false before number, as boolean is an instance of
	# Number, and str (l) would return True/False instead of true/false then
	elif l is True:
		yield 'true'
	elif l is False:
		yield 'false'
	elif isinstance (l, numbers.Number):
		yield str (l)
	# Strings are also Sequences, but we don't want to encode as lists
	elif isinstance (l, str):
		yield from _escapeString (l)
	elif isinstance (l, collections.abc.Sequence):
		yield from _encodeList (l, separators, indent, level)
	elif isinstance (l, collections.abc.Mapping):
		yield from _encodeDict (l, separators, indent, level)
	else:
		raise RuntimeError("Invalid object type")

def _indent(level, indent):
	return ' ' * (level * indent)

def _encodeKey (k):
	yield from _escapeString (k, False)

def _encodeList (l, separators, indent, level):
	yield '['
	first = True
	for e in l:
		if first:
			first = False
		else:
			yield separators[0]
		yield _indent (level, indent)
		yield from _encode (e, separators, indent, level+1)
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
		yield from _encodeKey (k)
		yield separators[2]
		yield from _encode (v, separators,  indent, level+1)
	yield '\n'
	yield _indent (level-1, indent)
	if level > 0:
		yield '}'
