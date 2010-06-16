#!/usr/bin/env python

"""Perform access checks on methods and attributes

Perform access checks on methods and attributes by catching attribute
access in metaclass and by means of __getattribute__. UNFINISHED. Do not
release.

Copyright (c) 2004 Stian Soiland 2004

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

#BUGS:
#  - class methods and class attributes fails.
#    (see test results)

import unittest

class _Accessor(object):
    """Base class for doing access checks 
       on attribute/method retrieval from a class.

       To be useful, this class must be subclassed and 
       _pre_* and/or _post_* must be imlemented
       to do any real checks.

       Then two subclasses are needed to combine metaclass
       functionality (access checks on both class methods and normal
       methods).


    """   

    def __getattribute__(self, key):
        # Skip everything that starts with _. This makes
        # self._pre_get() actually work without calling self._pre_get on
        # the retrieval of self._pre_get recursive to infinity.
        if key[0] == "_":
            internal = True    
        else:
            internal = False    
            self._pre_get(key)
        value = super(_Accessor, self).__getattribute__(key)
        if not internal:
            value = self._post_get(key, value)
        return value
        
    def __setattr__(self, key, value):    
        value = self._pre_set(key, value)
        super(_Accessor, self).__setattr__(key, value)
        self._post_set(key, value)

    def __delattr__(self, key):    
        self._pre_del(key)
        super(_Accessor, self).__delattr__(key)
        self._post_del(key)

    def _pre_get(self, key):
        """Checks or logs access to an attribute before it is retrieved. 
           Should raise an AttributeError if access is denied.
        """
        #print "Should get", key, "from", self
        pass    
        
    def _post_get(self, key, value):
        """Do any post-checks on an attribute before it is returned.
           The fetched value is passed on for additional checks, and
           must be returned  unaltered or wrapped, unless an
           AttributeError is raised."""
        #print "Returning value of", key, "from", self, ", it's", value
        return value       

    def _pre_set(self, key, value):
        """Checks or logs access to an attribute before it is set.
           The value must be returned unaltered or wrapped, 
           unless an AttributeError is raised."""
        #print "Should get", key, "from", self
        return value
        
    def _post_set(self, key, value):
        """Do any post-checks on an attribute after it has been set.
           You shouldn't raise AttributeError for access denied here,
           since it is too late.  Useful stuff to do here is logging or
           updating of sub-values.
        """
        pass
    
    def _pre_del(self, key):
        """Checks or logs access to an attribute before it is deleted. 
           Should raise an AttributeError if access is denied.
        """
        pass

    def _post_del(self, key):
        """Do any post-checks on an attribute after it has been deleted.
           You shouldn't raise AttributeError for access denied here,
           since it is too late.  Useful stuff to do here is logging or
           updating of sub-values.
        """
        pass


class SecurityCheck(unittest.TestCase):
    def setUp(self):
        class _SecurityChecker(_Accessor):
            def _pre_get(self, key):
                if key == "date":
                    raise AttributeError, "Access denied"

            def _post_get(self, key, value):
                #print "Retrieved", key, "with value", value
                if key == "name":
                    value = value.upper()
                return value    
            
            def _pre_set(self, key, value):
                if key == "thing":
                    raise AttributeError, "Access denied"        
                return value    
                    
            def _pre_del(self, key):
                self.backup = getattr(self, key)
        
        class securitychecker(_SecurityChecker, type):
            pass
        
        # Base class that implements checks both on
        # object level and class level 
        class SecurityChecker(_SecurityChecker):
            __metaclass__ = securitychecker
               
        class SecureClass(SecurityChecker):
            date = "2004-10-31"
            thing = "heja"
            def __init__(self):
                self.name = "Stian Soiland"
            
            def method(self, a,b):
                print "Method with", a, b    
                return a+b
        self.SecureClass = SecureClass             

    def testClassRead(self):
        SecureClass = self.SecureClass
        self.assertEqual(SecureClass.thing, "heja")
        def getter():
            return SecureClass.date
        self.assertRaises(AttributeError, getter)
    
    def testClassSet(self):
        SecureClass = self.SecureClass
        SecureClass.date = "2005-01-29"
        def setter():
            SecureClass.thing = "Nej"
        self.assertRaises(AttributeError, setter)
        # unchanged 
        self.assertEqual(SecureClass.thing, "heja")

    def testClassDelete(self):
        SecureClass = self.SecureClass
        SecureClass.fisk = "hei"
        # SecureClass.backup does not exist
        self.assertEqual(hasattr(SecureClass, "backup"), False)
        self.assertEqual(SecureClass.fisk, "hei")
        self.assertEqual(hasattr(SecureClass, "fisk"), True)
        del SecureClass.fisk
        # SecureClass.fisk should now be removed
        self.assertEqual(hasattr(SecureClass, "fisk"), False)
        self.assertEqual(SecureClass.backup, "hei")
        
    def testObjRead(self):
        obj = self.SecureClass()
        self.assertEqual(obj.thing, "heja")
        def getter():
            return obj.date
        self.assertRaises(AttributeError, getter)
        # uppercased  
        self.assertEqual(obj.name, "STIAN SOILAND")
    
    def testObjWrite(self):
        obj = self.SecureClass()
        obj.date = "2005-01-29"
        def setter():
            obj.thing = "Nej"
        self.assertRaises(AttributeError, setter)
        # unchanged 
        self.assertEqual(obj.thing, "heja")
    
    def testObjDelete(self):
        obj = self.SecureClass()
        obj.fisk = "hei"
        # obj.backup does not exist
        self.assertEqual(hasattr(obj, "backup"), False)
        self.assertEqual(obj.fisk, "hei")
        self.assertEqual(hasattr(obj, "fisk"), True)
        del obj.fisk
        # obj.fisk should now be removed
        self.assertEqual(hasattr(obj, "fisk"), False)
        self.assertEqual(obj.backup, "hei")
    
if __name__ == "__main__":
    unittest.main()
 
