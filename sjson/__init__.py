# coding=utf8
# @author: Matthäus G. Chajdas
# @license: 3-clause BSD

__version__ = '1.0.4'

import collections.abc
import collections
import numbers
import string
import io

class InputStream:
	def __init__ (self, s):
		self._stream = s
		self._index = 0
		self._line = 1
		self._column = 1

	def Read (self, count = 1):
		r = self._stream.read (count)

		if len (r) < count:
			_RaiseEndOfFile (stream)

		for c in r:
			# We test the individual bytes here, must use ord
			if c == ord ('\n'):
				self._line += 1
				self._column = 1
			else:
				self._column += 1
		return r

	def Peek (self, count = 1, allowEndOfFile = False):
		r = self._stream.peek (count)
		if len(r) == 0 and not allowEndOfFile:
			_RaiseEndOfFile (stream)
		elif len (r) == 0 and allowEndOfFile:
			return None
		else:
			return r[:count]

	def Skip (self, count = 1):
		self.Read (count)

	def GetLocation (self):
		loc = collections.namedtuple ('Location', ['line', 'column'])
		return loc (self._line, self._column)

class ParseException (RuntimeError):
	def __init__ (self, msg, location):
		super (ParseException, self).__init__ (msg)
		self._msg = msg
		self._location = location

	def GetLocation (self):
		return self._location

	def __str__ (self):
		return '{} at line {}, column {}'.format (self._msg,
			self._location.line, self._location.column)

def _RaiseEndOfFile (stream):
	raise ParseException ('Unexpected end-of-stream', stream.GetLocation ())

def _Consume (stream, what):
	_SkipWhitespace (stream)
	if stream.Peek (len (what)) != what:
		raise ParseException ("Expected to read '{}'".format(what), stream.GetLocation ())
	stream.Skip (len (what))

def _IsWhitespace (c):
	r = c in {b' ', b'\t', b'\n', b'\r'}
	return r

def _SkipWhitespace(stream):
	'''Skip whitespace. Return true if a new position within the stream was
	found; returns false if the end of the stream was hit.'''
	while True:
		w = stream.Peek (allowEndOfFile = True)
		if w == None:
			return False
		elif _IsWhitespace (w):
			stream.Skip ()
		else:
			break

	return True

def _IsIdentifier(c):
	import string
	return chr(c [0]) in set(string.ascii_letters + string.digits + '_')

def _Peek (stream):
	try:
		_SkipWhitespace (stream)
		return stream.Peek ()
	except:
		return None

def _ParseString (stream, allowIdentifier = False):
	_SkipWhitespace (stream)

	result = bytearray ()

	isQuoted = stream.Peek () == b'\"' or stream.Peek () == b'['
	if not allowIdentifier and not isQuoted:
		raise ParseException ('Quoted string expected', stream.GetLocation ())

	rawQuotes = False
	if isQuoted and stream.Peek () == b'[':
		if stream.Read (3) == b'[=[':
			rawQuotes = True
		else:
			raise ParseException ('Raw quoted string must start with [=[',
				stream.GetLocation ())
	elif isQuoted and stream.Peek () == b'\"':
		stream.Skip ()

	parseIdentifier = False
	if not isQuoted:
		parseIdentifier = True

	while True:
		c = stream.Peek ()
		if parseIdentifier and not _IsIdentifier (c):
			break

		if rawQuotes:
			if c == b']' and stream.Peek (3) == b']=]':
				stream.Skip (3)
				break
			else:
				result += c
				stream.Skip (1)
		else:
			if c == b'\"':
				stream.Read ()
				break
			elif c == b'\\':
				stream.Skip ()
				d = stream.Read ()

				if d == b'b':
					result += b'\b'
				elif d == b'n':
					result += b'\n'
				elif d == b't':
					result += b'\t'
				elif d == b'\\' or d == b'\"':
					result += d
			else:
				result += c
				stream.Skip ()

	s = str (result, encoding='utf-8')
	return s

def _ParseNumber (stream):
	_SkipWhitespace (stream)

	numberBytes = bytearray ()
	while True:
		p = stream.Peek (allowEndOfFile = True)

		if p is None:
			break

		if _IsWhitespace(p) or p == b',' or p == b']' or p == b'}':
			break
		else:
			numberBytes += stream.Read ()

	value = str (numberBytes, encoding='utf-8')

	try:
		return int(value)
	except ValueError:
		return float(value)

def _ParseMap (stream, delimited = False):
	from collections import OrderedDict
	result = OrderedDict()

	if stream.Peek () == b'{':
		stream.Skip ()

	while True:
		if delimited:
			_SkipWhitespace (stream)
		else:
			if not _SkipWhitespace (stream):
				break

		if stream.Peek () == b'}':
			_Consume (stream, b'}')
			break

		key = _ParseString (stream, True)
		_Consume (stream, b'=')
		value = _Parse (stream)
		result [key] = value

		if _Peek (stream) == b',':
			_Consume (stream, b',')

	return result

def _ParseList (stream):
	result = []
	_Consume (stream, b'[')

	while True:
		_SkipWhitespace (stream)
		if stream.Peek () == b']':
			stream.Skip ()
			break

		value = _Parse (stream)
		result.append (value)

		if _Peek (stream) == b',':
			_Consume (stream, b',')

	return result

def _Parse (stream):
	_SkipWhitespace (stream)

	peek = stream.Peek (2, allowEndOfFile = True)

	if peek is None:
		_RaiseEndOfFile (stream)

	c = bytes ([peek [0]])
	c2 = bytes ([peek [1]]) if len (peek) > 1 else None
	# second lookup character for [=[]=] raw literal strings

	value = None
	if c == b't':
		_Consume (stream, b'true')
		value = True
	elif c == b'f':
		_Consume (stream, b'false')
		value = False
	elif c == b'n':
		_Consume (stream, b'null')
		value = None
	elif c == b'{':
		value = _ParseMap (stream, True)
	elif c == b'[' and c2 != b'=':
		value = _ParseList (stream)
	elif (c == b'[' and c2 == b'=') or c == b'\"':
		value = _ParseString (stream)
	else:
		try:
			value = _ParseNumber (stream)
		except ValueError:
			raise ParseException ('Invalid character', stream.GetLocation ())
	return value

def loads (text):
	return _ParseMap (InputStream (io.BufferedReader (io.BytesIO (text.encode ('utf-8')))))

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
