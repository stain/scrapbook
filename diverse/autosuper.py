#!/usr/bin/env python

"""An improvement on Pythons super() allowing direct access.

Ever been irritated on the highly verbose
super(CurrentClass,self).method() syntax? Writing CurrentClass wrong
because you changed the name? Forgetting if self is first or second? Why
can't we just write super.method()? Well, now you can! By the way of
uglier than the ugliest hack, inspecting the call stack and the relevant
name spaces, anything is possible.

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


import inspect
import unittest
import types
import __builtin__
import sys
        
# save the REAL super function.        
real_super = __builtin__.super
        
class Super(object):
    """An improvement on Pythons super() allowing direct access.

    Example::
        from autosuper import super
        class A(object):
            def method(self):
                return 42
        class B(A):
            def method(self):
                return super.method() + 1        
        b = B()
        print b.method()
    
    Would print 43.
    
    This super works by inspecting the call stack and looking up
    "self" and then finding which method the attribute lookup was called
    from. 

    In other, more special cases, the old style 
        super(B, self).method()
    could still be used if needed.
    
    super.method works even for class methods and 'classic' classes.
    """            


    def __call__(self, *args, **kwargs):
        """Allow 'old-style' super()-calls."""
        return real_super(*args, **kwargs)
    def __getattr__(self, key):
        """Retrieves attribute as in super(Class, self)."""
        # Time to get dirty. 
        # Find out who's calling us
        stack = inspect.stack()
        # He's above us in the stack. 
        # The first part of the frame-tuple is the frame object
        frame = stack[1][0]

        (args, varargs, varkw, values) = inspect.getargvalues(frame)
        if not args and varargs:
            # If anyone is stupid enough to do something like:
            # class X:
            #     def f(*args):
            #         self = args[0]
            args = varargs

        # The first parameter is usually named "self" or or "cls" - but
        # we just pick the first parameter anyway to support other weird
        # people. 
        _self = args[0]
        obj = values[_self]
        if inspect.isclass(obj):
            # Assume this is a class method, so obj is the class to
            # search. This of course won't work within metaclasses..
            # FIXME!
            objcls = obj
        else:    
            objcls = obj.__class__
        
        # Problem: Finding the class of our current running function
        code = frame.f_code
        name = code.co_name
        
        # Stolen from
        # http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/286195

        # Find the method we're currently running by scanning the MRO
        # and comparing the code objects - when we find a match, that's
        # the class whose method we're currently executing.

        cls = None
        mro = inspect.getmro(objcls)
        # include search in metaclasses
        if hasattr(objcls, "__class__"):
            mro = mro + inspect.getmro(objcls.__class__)
        for c in mro:
            try:
                m = getattr(c, name)
            except AttributeError:
                continue

            if m.func_code is code:
                # We found it! But let's continue further down the
                # MRO in case our parent really owns it
                cls = c

        if not cls:          
            raise TypeError("Only use %s inside methods" % 
                            self.__class__.__name__)
        
        
        if type(cls) == types.ClassType:
            # Old-Style class doesn't support super(), we'll do it
            # manually.
            mro = iter(inspect.getmro(objcls))
            for c in mro:
                if c is cls:
                    break
            # OK, we've passed cls, now let's look for our
            # attribute among cls' parents (the rest of the iterator)
            for c in mro:
                try:
                    value = getattr(c, key)
                except AttributeError:
                    continue
                if (type(value) == types.MethodType and 
                    # im_self is None if it's unbound
                    value.im_self is None):
                    # We'll wrap it to include "self"
                    # Do it dirty, baby!
                    return lambda *args, **kwargs: \
                                 value(obj, *args, **kwargs)
                        
                return value    

        else:
            # OK, now we've got both obj and cls, let's create that
            # super object and get on with it!
            _super = super(cls, obj) 
            
            # Finally - try to retrieve the super method/whatever 
            return getattr(_super, key)
            

# So users of this module can do:
#     from autosuper import super                        

super = Super()



#  Unit tests

class TestBasics:
    def testSimple(self):
        self.assertEqual(self.parent.method(), "parent")
        self.assertEqual(self.stupidchild.method(), "parent")
                
    def testSuper(self):
        self.assertEqual(self.smarterchild.method(),
                         "parent smarterchild")            
        
    def testGrandChild(self):
        self.assertEqual(self.grandchild.method(), 
                         "parent smarterchild")
    
    def testSmartGrandChild(self):    
        self.assertEqual(self.smartgrandchild.method(),
                         "parent smarterchild smartgrandchild")

class TestNewstyle(TestBasics, unittest.TestCase):
    def setUp(self):
        class Parent(object):
            def method(self):
                return "parent"
        
        class StupidChild(Parent):
            pass
            
        class SmarterChild(Parent):
            def method(self):
                return super.method() + " smarterchild"

        class GrandChild(SmarterChild):
            pass            

        class SmartGrandChild(SmarterChild):
            def method(self):
                return super.method() + " smartgrandchild"    
        
        self.parent = Parent()
        self.stupidchild = StupidChild()
        self.smarterchild = SmarterChild()
        self.grandchild = GrandChild()
        self.smartgrandchild = SmartGrandChild()
    
class TestOldStyle(TestBasics, unittest.TestCase):
    def setUp(self):
        class Parent:
            def method(self):
                return "parent"
        
        class StupidChild(Parent):
            pass
            
        class SmarterChild(Parent):
            def method(self):
                return super.method() + " smarterchild"

        class GrandChild(SmarterChild):
            pass            

        class SmartGrandChild(SmarterChild):
            def method(self):
                return super.method() + " smartgrandchild"    
        
        self.parent = Parent()
        self.stupidchild = StupidChild()
        self.smarterchild = SmarterChild()
        self.grandchild = GrandChild()
        self.smartgrandchild = SmartGrandChild()
    
    
class TestClassmethodsNewStyle(TestBasics, unittest.TestCase):
    def setUp(self):
        class Parent(object):
            def method(cls):
                return "parent"
            method = classmethod(method)    
        
        class StupidChild(Parent):
            pass
            
        class SmarterChild(Parent):
            def method(cls):
                return super.method() + " smarterchild"
            method = classmethod(method)    

        class GrandChild(SmarterChild):
            pass            

        class SmartGrandChild(SmarterChild):
            def method(cls):
                return super.method() + " smartgrandchild"    
            method = classmethod(method)    
        
        # Does NOT instanciate  
        self.parent = Parent
        self.stupidchild = StupidChild
        self.smarterchild = SmarterChild
        self.grandchild = GrandChild
        self.smartgrandchild = SmartGrandChild

class TestClassmethodsOldStyle(TestBasics, unittest.TestCase):
    def setUp(self):
        class Parent:
            def method(cls):
                return "parent"
            method = classmethod(method)    
        
        class StupidChild(Parent):
            pass
            
        class SmarterChild(Parent):
            def method(self):
                return super.method() + " smarterchild"
            method = classmethod(method)    

        class GrandChild(SmarterChild):
            pass            

        class SmartGrandChild(SmarterChild):
            def method(self):
                return super.method() + " smartgrandchild"    
            method = classmethod(method)    
        
        self.parent = Parent
        self.stupidchild = StupidChild
        self.smarterchild = SmarterChild
        self.grandchild = GrandChild
        self.smartgrandchild = SmartGrandChild

class TestAttributes(unittest.TestCase):
    def setUp(self):
        class Parent:
            x = "parent"
            def get_x(self):
                return self.x
        
        class Child(Parent):
            x = "child"
            def get_x(self):
                return super.x + " " + self.x
        self.parent = Parent()
        self.child = Child()
    def testAttribute(self):
        self.assertEqual(self.parent.get_x(), "parent")                
        self.assertEqual(self.child.get_x(), "parent child")

class TestMetaclass(unittest.TestCase):
 
    def testMetaclass(self):
        class Parent(type):
            def method(self):
                return "parent"
                
        class Child(Parent):                
            def method(self):
                return super.method() + " " + "child"
        
        class PClient(object):
            __metaclass__ = Parent
            def client(self):
                return "pclient"

        class CClient(object):
            __metaclass__ = Child
            def client(self):
                return "cclient"
                        
        #Trivial                
        self.assertEqual(PClient.method(), "parent")                    
        self.assertEqual(CClient().client(), "cclient")
        # This is the real test
        self.assertEqual(CClient.method(), "parent child")

if __name__ == "__main__":
    unittest.main()
