#!/usr/bin/env python3
# coding=utf8
# @author: Matthäus G. Chajdas
# @license: 3-clause BSD

import unittest
import encode, decode
from collections import OrderedDict

class Test(unittest.TestCase):
    def testSimpleEncodeList(self):
        r = encode.dumps([1,2,3])
        self.assertEqual("[1, 2, 3]", r)

    def testSimpleDictEncode(self):
        r = encode.dumps(OrderedDict([('a',23), ('b',False)]))
        self.assertEqual("a = 23\nb = false\n", r)

    def testNestedDictEncode(self):
        r = encode.dumps({'n': OrderedDict([('a',1), ('b',2)])})
        self.assertEqual('n = {\na = 1\nb = 2\n}\n', r)

    def testSimpleDictDecode(self):
        r = decode.loads('n={a=1 b=2}')
        self.assertDictEqual(r, {'n':{'a':1, 'b':2}})

    def testBugDecodeFailure1(self):
        s = """Application = {
        Window = {
                Width = 1280
                Height = 720
                sRGB = true
                AA = 1
        }
        RenderSystem = "Preferred"
}"""
        r = decode.loads(s)
        self.assertDictEqual(r, {'Application' : {'Window' : {'Width' : 1280,
                                                              'Height' : 720,
                                                              'sRGB' : True,
                                                              'AA' : 1},
                                                  'RenderSystem' : "Preferred"}})

    def testDecodeFailsForFloats(self):
        s = "test = 1.0"
        r = decode.loads(s)
        self.assertDictEqual(r, {'test' : 1.0})

    def testBugDecodeFailure2(self):
        s = """name = "FontTextureGenerator",
ui = 2"""
        r = decode.loads(s)
        self.assertDictEqual(r, {'name' : 'FontTextureGenerator', 'ui' : 2})

    def testBugDecodeFailure3(self):
        s = """name = "FontTextureGenerator",
flags = ["UsesOpenMP"]"""
        r = decode.loads(s)
        self.assertDictEqual(r, {'name' : 'FontTextureGenerator', 'flags' : ['UsesOpenMP']})

    def testBugDecodeFailsOnStringWithDot(self):
        s = 'name = "FontTexture.Generator"'
        r = decode.loads(s)
        self.assertDictEqual(r, {'name' : 'FontTexture.Generator'})
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
