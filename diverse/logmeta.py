#!/usr/bin/env python

"""Metaclass for logging method calls

By using a metaclass, it is possible to wrap all the functions defined
in a class so that they will log entry and exit, among with parameters,
to stdout.

Copyright (c) 2004 Stian Soiland

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Author: Stian Soiland <stian@soiland.no>
URL: http://soiland.no/software
License: MIT
"""

import unittest
import StringIO
import sys

# wraps a function
def logger(f, name=None):
    # Closure to remember our name and function objects
    if name is None:
        name = f.func_name
    def wrapped(*args, **kwargs):
        print "Calling", name, args, kwargs
        result = f(*args, **kwargs)
        print "Called", name, args, kwargs, "returned", repr(result)
        return result
    wrapped.__doc__ = f.__doc__    
    return wrapped    

class TestStdout(unittest.TestCase):
    """Captures stdout to self.stdout"""
    def setUp(self):
        self.STDOUT = sys.stdout
        sys.stdout = StringIO.StringIO()
    def tearDown(self):
        sys.stdout = self.STDOUT
        del self.STDOUT
    def stdout(self):
        return sys.stdout.getvalue()
    stdout = property(stdout)        
    def testStdoutCatcher(self):       
        print "Hei"
        self.assertEqual(sys.stdout.getvalue(), "Hei\n")
        self.assertEqual(self.stdout, "Hei\n")


class TestLogger(TestStdout):
    def testReturns(self):
        def dummy(a,b):
            return a+b
        self.assertEqual(dummy(2,3), 5)
        dummy_log = logger(dummy)
        self.assertEqual(dummy_log(2,3), 5)
    def testSimple(self):
        def dummy():
            pass
        dummy_log = logger(dummy)
        dummy_log()
        self.assertEqual(self.stdout, 
            "Calling dummy () {}\nCalled dummy () {} returned None\n")
    def testAdvanced(self):
        def dummy(a,b,c=29):
            return a+b+c
        dummy_log = logger(dummy)
        dummy_log("hei", "paa", c="deg")
        self.assertEqual(self.stdout, 
            "Calling dummy ('hei', 'paa') {'c': 'deg'}\n"
            "Called dummy ('hei', 'paa') {'c': 'deg'} returned 'heipaadeg'\n")

class logmeta(type):
    """Logs all calls to method defined in this class"""
    def __new__(cls, name, bases, dict):
        # Wrap all functions
        for (key, value) in dict.items():
            if key == "__metaclass__":
                continue
            if callable(value):
                dict[key] = logger(value)
        return type.__new__(cls,name, bases, dict)

class TestLogMeta(TestStdout):
    def testMetaWrapper(self):
        class A:
            __metaclass__ = logmeta
            def method(self):
                pass 
        a = A()
        self.assertEqual(self.stdout, "")              
        a.method()
        objrepr = repr(a)
        expected = ("Calling method (%s,) {}\n"
                    "Called method (%s,) {} returned None\n" % (objrepr, objrepr))
        self.assertEqual(self.stdout, expected)

if __name__ == '__main__':
    unittest.main()
