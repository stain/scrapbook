#!/usr/bin/env python
# *-* encoding: utf8
# 
# Copyright (c) 2006 Stian Soiland
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# Author: Stian Soiland <stian@soiland.no>
# URL: http://soiland.no/i/src/
# License: MIT
#

"""Split iterable into sub-iterators.

Use instead of itertools.izip(*iterable) when you want to have an
iterator for each index, for instance to save memory. 

Note that you should iterate over all the return sub-iterators to avoid
a large buffer building up for the unfetched values.
"""


from itertools import tee, chain

def isplit(iterable, n=None):
    """Split iterable into indexing sub-iterators.

    Opposite of itertools.izip() - split an iterable to n sub-iterators,
    where n is the length of the first item of the iterable.
    The items should be indexable, and each sub-iterator will yield
    items from a particular index. 

    If any of the items from iterable don't have the required index, it
    will be skipped. 

    If parameter n is supplied, this many index-subiterators will be
    returned, and the iterable's first element will not be inspected.

    Examples:

        >>> coords = [(1,2), (3,4), (5,6), (7,8)]
        >>> it_x, it_y = isplit(coords)
        >>> print list(it_x)
        [1, 3, 5, 7]
        >>> for y in it_y: 
        ...     print y,
        2 4 6 8
        >>> import itertools
        >>> ranges = itertools.izip(range(10), range(5,15), range(10,20))
        >>> ranges.next()
        (0, 5, 10)
        >>> x,y,z = isplit(ranges)
        >>> x.next()
        1
        >>> y.next() 
        6
        >>> for elem in z:
        ...    print elem,
        11 12 13 14 15 16 17 18 19
        >>> y.next()
        7
        >>> mess = [(0,1), (2,3), (4,5,6), (7,), (), (8,9,10,11)]
        >>> mess = iter(mess)
        >>> x,y,z = isplit(mess, n=3)
        >>> # Not affected yet, since we have specified n=3
        >>> mess.next() 
        (0, 1)
        >>> x.next()  # The 0 was eaten by mess.next()
        2
        >>> x.next()
        4
        >>> list(y)
        [3, 5, 9]
        >>> list(z)  # Missing elements are skipped
        [6, 10]
    """
    iterable = iter(iterable)
    if n is None:
        # Find length by inspecting first item
        first = iterable.next()
        n = len(first)
        # Re-insert the item into the iterable
        iterable = chain([first], iterable)

    # Generate len(first) independant (tee-ed) iterators
    sub_iters = tee(iterable, n)
    for i,sub_iter in enumerate(sub_iters):
        # Closure for keeping i and sub_iter 
        def closure(i=i, sub_iter=sub_iter):
            for elem in sub_iter:
                try:
                    yield elem[i]
                except IndexError:
                    continue    
        # Yield our generator    
        yield closure()    
            

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()

