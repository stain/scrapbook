#!/usr/bin/env python

import sets

class ListSet(sets.Set):
    def __sub__(self, rhs):
        """Substract also an iterable, returns new set.
        >>> a = ListSet(("fish", "soup", "bowl"))
        >>> b = ["fish", "baby", "bowl", "fish"]
        >>> a - b
        ListSet(['soup'])
        >>> c = ListSet(("meat", "fish"))
        >>> c - a
        ListSet(['meat'])
        """
        return sets.Set.__sub__(self, sets.Set(rhs))    
        
    def __rsub__(self, lhs):
        """Substract also from a iterable, returns list of items not in set.

        >>> a = ListSet(("fish", "soup"))
        >>> b = "Hello there my fish baby".split()
        >>> b - a
        ['Hello', 'there', 'my', 'baby']
        >>> c = ListSet(("soup", "chips"))
        >>> c - a
        ListSet(['chips'])
        """
        try:
            return sets.Set.__sub__(lhs, self)
        except TypeError:
            return [x for x in lhs if x not in self]

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()
    
