# coding=utf8
# @author: Matthäus G. Chajdas
# @license: 3-clause BSD

import sjson
import pytest

from collections import OrderedDict

def testSimpleEncodeList():
    r = sjson.dumps([1,2,3])
    assert ("[1, 2, 3]" == r)

def testSimpleDictEncode():
    r = sjson.dumps(OrderedDict([('a',23), ('b',False)]))
    assert ("a = 23\nb = false\n" == r)

def testNestedDictEncode():
    r = sjson.dumps({'n': OrderedDict([('a',1), ('b',2)])})
    assert ('n = {\na = 1\nb = 2\n}\n' == r)

def testSimpleDictDecode():
    r = sjson.loads('n={a=1 b=2}')
    assert (r == {'n':{'a':1, 'b':2}})

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
