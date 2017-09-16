# coding=utf8
# @author: Matthäus G. Chajdas
# @license: 3-clause BSD

import sjson
import pytest
import io

from collections import OrderedDict
import collections.abc

def testEncodeList():
    r = sjson.dumps([1,2,3])
    assert ("[1, 2, 3]" == r)

def testEncodeTuple():
    r = sjson.dumps ((1, 2, 3,))
    assert ("[1, 2, 3]" == r)

def testEncodeIntValue():
    r = sjson.dumps ({'key' : 23})
    assert ("key = 23\n" == r)

def testEncodeFloatValue():
    r = sjson.dumps ({'key' : 23.0})
    assert ("key = 23.0\n" == r)

def testEncodeStringValue():
    r = sjson.dumps ({'key' : '23'})
    assert ("key = \"23\"\n" == r)

def testEncodeNullValue():
    r = sjson.dumps ({'key' : None})
    assert ("key = null\n" == r)

def testEncodeTrueValue():
    assert (sjson.dumps ({'key' : True}) == "key = true\n")

def testEncodeFalseValue():
    assert (sjson.dumps ({'key' : False}) == "key = false\n")

def testDecodeNull():
    assert (sjson.loads ('key = null') == {'key' : None})

def testDecodeTrue():
    assert (sjson.loads ('key = true') == {'key' : True})

def testKeyWithWhitespaceIsEscaped():
    assert (sjson.dumps ({'k y' : None}) == '"k y" = null\n')

def testDecodeFalse():
    assert (sjson.loads ('key = false') == {'key' : False})

def testEncodeStringValueWithQuoteGetsEscaped():
    r = sjson.dumps ({'key' : '"Quoted string"'})
    assert ('key = "\\"Quoted string\\""\n' == r)

def testDecodeStringValueWithEscapedQuote():
    r = sjson.loads ('key = "\\"Quoted string\\""')
    assert (r == {'key' : '"Quoted string"'})

def testEncodeStringValueWithNewlineGetsEscaped():
    r = sjson.dumps ({'key' : 'New\nline'})
    assert ('key = "New\\nline"\n' == r)

def testDecodeStringValueWithNewline():
    r = sjson.loads ('key = "New\\nline"\n')
    assert (r == {'key' : 'New\nline'})

def testDecodeStringValueWithTab():
    r = sjson.loads ('key = "Tab\\tulator"')
    assert (r == {'key' : 'Tab\tulator'})

def testEncodeDict ():
    r = sjson.dumps(OrderedDict([('a',23), ('b',False)]))
    assert ("a = 23\nb = false\n" == r)

def testEncodeDictLike ():
    class DictLike (collections.abc.Mapping):
        def __init__ (self, d=[]):
            super(DictLike, self).__init__ ()
            self.__d = OrderedDict ()
            for (k,v) in d:
                self.__d [k] = v

        def __contains__ (self, i):
            return i in self.__d

        def __len__ (self):
            return len (self.__d)

        def __iter__ (self):
            return iter (self.__d)

        def __getitem__ (self, k):
            return self.__d [k]

    dl = DictLike ([('foo', 'test'), ('test', 42)])
    r = sjson.dumps (dl)
    assert ("foo = \"test\"\ntest = 42\n" == r)

def testEncodeNestedDict ():
    r = sjson.dumps({'n': OrderedDict([('a',1), ('b',2)])})
    assert ('n = {\na = 1\nb = 2\n}\n' == r)

def testDecodeDict ():
    r = sjson.loads('n={a=1 b=2}')
    assert (r == {'n':{'a':1, 'b':2}})

def testDecodeList ():
    r = sjson.loads ('n=[1, 2, 3]')
    assert (r == {'n' : [1, 2, 3]})

def testBugDecodeFailure1():
    s = """Application = {
    Window = {
            Width = 1280
            Height = 720
            sRGB = true
            AA = 1
    }
    RenderSystem = "Preferred"
}"""
    r = sjson.loads(s)
    assert(r == {'Application' : {'Window' : {'Width' : 1280,
                                                          'Height' : 720,
                                                          'sRGB' : True,
                                                          'AA' : 1},
                                              'RenderSystem' : "Preferred"}})

def testReportErrorOnIncompleteArray1():
    s = "test = [1, 2, "
    with pytest.raises (Exception):
        sjson.loads (s)

def testReportErrorOnIncompleteArray2():
    s = "test = ["
    with pytest.raises (Exception):
        sjson.loads (s)

def testReportOnIncompleteMap1():
    s = "test = "
    with pytest.raises (Exception):
        sjson.loads (s)

def testReportOnIncompleteMap2():
    s = "test "
    with pytest.raises (Exception):
        sjson.loads (s)

def testBugDecodeFailsForFloats():
    s = "test = 1.0"
    r = sjson.loads(s)
    assert (r == {'test' : 1.0})

def testBugDecodeFailure2():
    s = """name = "FontTextureGenerator",
ui = 2"""
    r = sjson.loads(s)
    assert (r == {'name' : 'FontTextureGenerator', 'ui' : 2})

def testBugDecodeFailure3():
    s = """name = "FontTextureGenerator",
flags = ["UsesOpenMP"]"""
    r = sjson.loads(s)
    assert (r == {'name' : 'FontTextureGenerator', 'flags' : ['UsesOpenMP']})

def testBugDecodeFailsOnStringWithDot():
    s = 'name = "FontTexture.Generator"'
    r = sjson.loads(s)
    assert (r == {'name' : 'FontTexture.Generator'})

def testStringWithoutQuotesAsValueThrows():
    with pytest.raises (Exception):
        sjson.loads ("key = baz\n")

def testStringWithoutClosingQuotesThrows():
    with pytest.raises (Exception):
        sjson.loads ('key = "baz\n')

def testStringWithRawLiteral():
    r = sjson.loads ("""foo = [=[
    This is a raw literal
    string
    ]=]""")
    assert r['foo'] == """
    This is a raw literal
    string
    """

def testStringWithRawLiteralQuote():
    r = sjson.loads ("""foo = [=[I haz a " in here]=]""")
    assert r['foo'] == """I haz a " in here"""

def testStringWithRawLiteralNewline():
    r = sjson.loads ("""foo = [=[I haz a
 in here]=]""")
    assert r['foo'] == """I haz a\n in here"""

def testStringWithEmptyRawLiteral():
    r = sjson.loads ("""foo = [=[]=]""")
    assert r['foo'] == ""

def testStringWithIncorrectlyTerminatedRawLiteral():
    with pytest.raises (Exception):
        sjson.loads ("""foo = [=[=]""")
    with pytest.raises (Exception):
        sjson.loads ("""foo = [=[]]""")
    with pytest.raises (Exception):
        sjson.loads ("""foo = [=[]=""")

def testUndelimitedMapThrows():
    with pytest.raises (Exception):
        sjson.loads ('foo = { bar = "value", baz = { ui = "foo",')

def testInvalidRawQuotedStringStart():
    with pytest.raises (Exception):
        sjson.loads ("foo = [=? wrong ?=]")
    with pytest.raises (Exception):
        sjson.loads ("foo = [=] wrong [=]")

def testExceptionLocation():
    try:
        sjson.loads ("foo = true\nbar = fail")
    except sjson.ParseException as e:
        location = e.GetLocation()
        assert location.line == 1
        assert location.column == 6

def testDecodeFromStream():
    s = """name = "FontTextureGenerator",
flags = ["UsesOpenMP"]"""
    s = io.BytesIO (s.encode ('utf-8'))
    r = sjson.load(s)
    assert (r == {'name' : 'FontTextureGenerator', 'flags' : ['UsesOpenMP']})