#!/usr/bin/env python

"""Interval

Useful for specifing a valid interval of floating point numbers
(or similar) that could later be used for testing if elements 
are member of the interval or not.

Example::

    valid_interval = Interval(-1.0, 1.0)
    value = 0.5
    if value not in valid_interval:
        value = valid_interval.min

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
"""

import unittest
import StringIO
import sys

class Infinity(object):
    """Representation of infinity. This is even more infinite than
       a floating point infinity, as this object is ALWAYS larger
       than anything. 
       
       The negative of Infinity() is always smaller than everything.

       Note that inf != inf, as two infinities are not equal. They
       are both the same object, though, as this is really a singleton
       class. The constant "inf" should be exported from this module.
       """
#    __metaclass__ = logmeta
    def __new__(cls, negative=False):
        # Make it always return the same two infinities
        if negative:
            if not hasattr(cls, "_neg"):
                cls._neg = object.__new__(cls, negative)
            return cls._neg
        else:
            if not hasattr(cls, "_pos"):
                cls._pos = object.__new__(cls, negative)
            return cls._pos    

    def __init__(self, negative=False):
        self.negative = negative

    def __neg__(self):
        return self.__class__(not self.negative)
    
    # self < other
    def __lt__(self, other):
        # Never smaller, unless we are negative
        return self is not other and self.negative            
    __le__ = __lt__    

    # self > other
    def __gt__(self, other):
        # Always larger, unless we are negative
        return self is not other and not self.negative            
    __ge__ = __gt__    

    def __eq__(self, other):
        return False
    def __ne__(self, other):
        return True    

inf = Infinity()        
class Interval:
    """A interval of values. Supports any comparable type.
       Example::

           valid_interval = Interval(-1.0, 1.0)
           value = 0.5
           if value not in valid_interval:
               value = valid_interval.min
    """               
    def __init__(self, min=-inf, max=inf, inclusive='none'):
        """Creates a new Interval. min and max are the lower and upper
           bounds of the numeric interval. 

           inclusive should be one of the strings none, left, right, both:
              'none'     <min,max>    min and max not included (open)
              'left'     [min,max>    min included
              'right'    <min,max]    max included
              'both'     [min,max]    both included (closed)

           Defaults:
              min        -inf         No lower limit
              max        inf          No maximum limit
              inclusive  'none'       Not inclusive
        """
        assert min <= max
        self.min = min
        self.max = max
        if not inclusive in ('none', 'left', 'right', 'both'):
            raise TypeError, "inclusive must be left, right, both or none" 
        self.inclusive = inclusive    
 
    def __contains__(self, value):
        """Checks if value is a part of the interval"""
        if value==self.min and self.inclusive in ('left', 'both'):
            return True
        if value==self.max and self.inclusive in ('right', 'both'):
            return True
        return value > self.min and value < self.max


class TestInfinity(unittest.TestCase):
    def testPositive(self):
        assert inf > -222982
        assert inf > 982
        assert inf > "Hei"
        assert inf > object()
        # And vice versa
        assert 982 < inf
        assert "Hei" < inf
        assert object() < inf
        assert -2 < inf > 2
        assert not (inf < inf)
        assert not (inf > inf)

    def testPositiveEquals(self):
        assert inf >= -222982
        assert inf >= 982
        assert inf >= "Hei"
        assert inf >= object()
        # And vice versa
        assert 982 <= inf
        assert "Hei" <= inf
        assert object() <= inf
        assert -2 <= inf >= 2
        assert not (inf <= inf)
        assert not (inf >= inf)
    
    def testNegative(self):
        neginf = -inf
        neginf2 = Infinity(negative=True)
        assert neginf is neginf2
        assert neginf < -222982
        assert neginf < 982
        assert neginf < "Hei"
        assert neginf < object()
        # And vice versa
        assert 982 > neginf
        assert "Hei" > neginf
        assert object() > neginf
        assert -2 > neginf < 2
        assert not (neginf < neginf)
        assert not (neginf > neginf)
    
    def testEquals(self):
        assert inf is Infinity()
        assert not (inf == -222982)
        assert not (inf == 982)
        assert not (inf == "Hei")
        assert not (inf == object())
        # And vice versa)
        assert not (982 == inf)
        assert not ("Hei" == inf)
        assert not (object() == inf)
        assert not (-2 == inf == 2)
        # no, they are not even equal to them selves 
        assert not (inf == inf)

    def testNotEquals(self):
        assert (inf != -222982)
        assert (inf != 982)
        assert (inf != "Hei")
        assert (inf != object())
        # And vice versa)
        assert (982 != inf)
        assert ("Hei" != inf)
        assert (object() != inf)
        assert (-2 != inf != 2)
        assert (inf != inf)

    def testSingleton(self):
        inf1 = Infinity()
        inf2 = Infinity()
        assert inf1 is inf2
        assert id(inf1) == id(inf2) 
        neginf1 = Infinity(negative=True)
        neginf2 = Infinity(negative=92)
        assert neginf1 is neginf2
        assert id(neginf1) == id(neginf2) 
        assert neginf1 is not inf1
        assert id(neginf1) != id(inf1)
        
class TestConstructor(unittest.TestCase):
    def testIllegalEntries(self):
        Interval(1,5)
        Interval(5,5)
        Interval(0,0)
        self.assertRaises(AssertionError, Interval, 2, 1)

    def testInclusive(self):
        Interval(1,5,'none')       
        Interval(1,5,'left')
        Interval(1,5,'right')       
        Interval(1,5,'both')       
        self.assertRaises(TypeError, Interval, 1, 5, 'unknown')
        self.assertRaises(TypeError, Interval, 1, 5, None)
        self.assertRaises(TypeError, Interval, 1, 5, 'None')
        self.assertRaises(TypeError, Interval, 1, 5, 'Left')
        self.assertRaises(TypeError, Interval, 1, 5, 'Right')
        self.assertRaises(TypeError, Interval, 1, 5, 'Both')
    
    def testAttributes(self):
        r = Interval(1,5)
        self.assertEqual(r.min, 1)     
        self.assertEqual(r.max, 5)
        self.assertEqual(r.inclusive, 'none')
        r = Interval(1,5, 'both')
        self.assertEqual(r.inclusive, 'both')


class TestContains(unittest.TestCase):
    def testSimple(self):
        r = Interval(1,5)
        assert 0 not in r
        assert 3 in r
        assert -2 not in r

    def testInclusiveNone(self):
        r = Interval(1,5,'none')
        assert 0 not in r
        assert 1 not in r
        assert 3 in r
        assert 5 not in r
        assert 6 not in r
        
    def testInclusiveLeft(self):
        r = Interval(1,5,'left')
        assert 0 not in r
        assert 1 in r
        assert 3 in r
        assert 5 not in r
        assert 6 not in r
        
    def testInclusiveRight(self):
        r = Interval(1,5,'right')
        assert 0 not in r
        assert 1 not in r
        assert 3 in r
        assert 5 in r
        assert 6 not in r

    def testInclusiveBoth(self):
        r = Interval(1,5,'both')
        assert 0 not in r
        assert 1 in r
        assert 3 in r
        assert 5 in r
        assert 6 not in r
        
    def testInfinity(self):
        r = Interval(0, inf)
        assert -1292 not in r
        assert 1337 in r
        assert 2L**65 in r
        assert inf not in r
        assert -inf not in r

        # Now, by definition a interval that ends in infinity is open,
        # not closed, but the code shouldn't differ
        r = Interval(0, inf, "both")
        assert 0 in r
        assert inf not in r

        r = Interval(-inf, 0)
        assert 1292 not in r
        assert -1337 in r
        assert -2L**65 in r
        assert inf not in r
        assert -inf not in r

        r = Interval(-inf, inf)
        assert 1292 in r
        assert -1337 in r
        assert -2L**65 in r
        assert 2L**65 in r
        assert inf not in r
        assert -inf not in r

        r = Interval(-inf, 0, "both")
        assert 0 in r
        assert -inf not in r

if __name__ == '__main__':
    unittest.main()

