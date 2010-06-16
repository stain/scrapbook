#!/usr/bin/env python

"""Transparent pointer to any objects. Most useful for immutables.

Normally in Python, strings and integers etc. are socalled immutables, 
they cannot change. By using the dynamic namespaces of Python, we can 
make a wrapper object that allow the value to change by the use of 
the set() method.


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
License: MIT
URL: http://soiland.no/software
"""

import types


class pointer(object):

    def __new__(cls, value):
        """Wraps a value as a transparent pointer.
        """
        
        objtype = type(value)
        if objtype in (types.InstanceType, types.ClassType):
            raise ValueError, "Classic classes not supported"
        
        objtype = value.__class__

        # Make a convenient subclass of both pointer and the object type
        # (this is really only needed to make isinstance(x) work. Note
        # that it is not required for set() objects to be of the same
        # type. 
        class proxyclass(cls, objtype):
            pass
        
        o = objtype.__new__(proxyclass)
        o.set(value)
        return o
    
    def __init__(self, *args, **kwargs):
        # Don't run __init__ twice
        pass    

    def set(self, value):
        """Changes the current value of the integer.
           >>> a = pointer(23)
           >>> print a
           23
           >>> a + 2
           25
           >>> b = a
           >>> a.set(10)
           >>> b + 2 # affected b too
           12

           >>> c = pointer(10)
           >>> a.set(c)

           This makes a-->c-->10
           
           >>> print a
           10
           >>> c.set(12)
           >>> print c
           12
           >>> print a
           12

           This makes a-->c-->12

           >>> a.set(13)
           >>> print a
           13
           >>> print c
           12

           The set-method was not copied, and done locally on a.
        """   

        self._value = value
        # transfer all functions from new value
        for methodname in dir(value):
            method = getattr(self._value, methodname)
            if methodname in ('__getattribute__', '__setattr__', '__new__',
                              '__init__', '__class__', 'set', 'get'):
                # Don't transfer these important internal methods. In
                # addition, if the new value is a pointer itself, we
                # shouldn't take his get/set methods, that would remove
                # ours!
                continue

            if not callable(method):
                # HMm.. some value. What could it be?
                # We'll handle that in __getattribute__ anyway.
                continue

            # Define a closure to store the methodname
            #
            # (Why this is needed? otherwise 'methodname' would be
            # resolved from this namespace, and the value of
            # 'methodname' after this for-loop is then the last
            # one in dir(value) for all methods.. not good)
            def closure(methodname):
                def wrapmethod(self, *args, **kwargs):
                    method = getattr(self._value, methodname)
                    return method(*args, **kwargs)
                return wrapmethod
            # Since type(self) is the proxyclass made specifically
            # for this instance, they are unique, and it's safe
            # to store our wrapped methods there. 
            # 
            # Why are we doing this in the class instead of just
            # setattr(self, methodname, method)?  Well, it turns
            # out that those __internal__-methods, like __add__,
            # are resolved from the class, not the instance. If we
            # didn't do it this way,  pointer(5) + 1 wouldn't work.
            setattr(type(self), methodname, closure(methodname))
    
    def __getattribute__(self, key):
        try:
            return super(pointer, self).__getattribute__(key)
        except AttributeError:
            return getattr(self._value, key)    
            

    def get(self):
        """Retrieves the 'real' value hidden behind.
           >>> a = pointer(25)
           >>> print a
           25
           >>> print a.get()
           25
           >>> print type(a.get())
           <type 'int'>
           """
        return self._value

def _test():
    import doctest, pointer
    return doctest.testmod(pointer)

if __name__ == "__main__":
    _test()
    
