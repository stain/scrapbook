#!/usr/bin/env python

import unittest

"""Abstract method decorator. 

Using Python 2.4's @decorator syntax, doing "abstract methods" in Python
can be elegant, even if the whole concept of abstract methods is broken.
Really, you don't need this. Python people don't do abstract classes or
methods. But have a look at how decorators can be elegant for this
approach, being both simple and self-explaining. Also check out my blog
on this on http://soiland.no/blog/py/abstract

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

def abstract(f):
    """Decorator for tagging a method as abstract. """
    f.abstract = True
    f.__doc__ = (f.__doc__ or "") + "\nNOTE: Abstract method"
    return f

class Abstract(object):
    """Base class for classes with abstract methods. 
    Raises a TypeError on instantiation if an abstract
    method is not implemented.
    
    Example::

        class AbstractSomething(Abstract):
            def working_method(self):
                return "This method works"

            @abstract    
            def future_work(self):
                '''Implement this method later'''    
        
        class Something(AbstractSomething):
            def future_work(self):
                return "Finally implemented"
    
    Instantiating AbstractSomething will raise an TypeError,
    even if future_work isn't called. Instantiating 
    Something will work, as it's overriding method future_work
    isn't tagged by the @abstract decorator.
               
    Note that decorator syntax is new in Python 2.4. For earlier
    versions, abstract will have to be applied like this::
    
        class AbstractSomething(Abstract):
            def future_work(self):
                '''Implemented later'''
            future_work = abstract(future_work)               

    or::
    
        class AbstractSomething(Abstract):
            def future_work(self):
                '''Implemented later'''
            future_work.abstract = True    
    """
    def __init__(self):
        for methodname in dir(self):
            method = getattr(self, methodname, None)
            if not callable(method): 
                continue
            if hasattr(method, "abstract"):
                raise TypeError, ("Abstract method %s not implemented" %
                      method)    
    
class TestAbstract(unittest.TestCase):    
    def setUp(self):
        class AbstractSomething(Abstract):
            def working_method(self):
                return "This method works"

            @abstract    
            def future_work(self):
                '''Do nice future work'''    
        
        class DoesntFixAbstract(AbstractSomething):
            def some_other(self):
                return "Some other method"        
        
        class Something(AbstractSomething):
            def future_work(self):
                return "Finally implemented"
        
        self.AbstractSomething = AbstractSomething
        self.DoesntFixAbstract = DoesntFixAbstract
        self.Something = Something

    def testRaisesError(self):
        self.assertRaises(TypeError, self.AbstractSomething)        
        self.assertRaises(TypeError, self.DoesntFixAbstract)
     
    def testImplementedOK(self):
        s = self.Something()
        self.assertEqual(s.future_work(), "Finally implemented")
    
    def testDocString(self):
        self.assertEqual(self.AbstractSomething.future_work.__doc__,
                         "Do nice future work\nNOTE: Abstract method")    
                 
if __name__ == "__main__":
    unittest.main()                    
