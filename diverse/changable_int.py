#!/usr/bin/env python
"""
Normally in Python, strings and integers etc. are socalled imutables,
they cannot change.
  
By using the dynamic namespaces of Python, we can make a wrapper object
that allow the number to change by the use of the set() method.  This
can further be used to have several "pointers" to the same number, even
if it changes.
"""

class changable_int(int):
    def __new__(cls, number):
        o = int.__new__(cls)
        o.set(number)
        return o
    def set(self, number):
        """Changes the current value of the integer.
           >>> a = changable_int(23)
           >>> print a
           23
           >>> a + 2
           25
           >>> b = a
           >>> a.set(10)
           >>> b + 2 # affected b too
           12

           >>> c = changable_int(10)
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

        self._number = number
        # transfer all functions from _number 
        for key in dir(self._number):
            value = getattr(self._number, key)
            if not callable(value) or \
                key in ('__getattribute__', '__setattr__', '__new__',
                        'set', 'get'):
                continue
            try:
                setattr(self.__class__, key, 
                        (lambda key, f: 
                          lambda self, *args, **kwargs: 
                            getattr(self._number, key)(*args,
                            **kwargs))(key, value))
            except:
                pass
    def get(self):
        """Retrieves the 'real' integer hidden behind.
           >>> a = changable_int(25)
           >>> print a
           25
           >>> print a.get()
           25
           >>> print type(a.get())
           <type 'int'>
           """
        return self._number

def _test():
    import doctest, changable_int
    return doctest.testmod(changable_int)

if __name__ == "__main__":
    _test()
    
