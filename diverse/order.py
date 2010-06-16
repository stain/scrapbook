#!/usr/bin/env python

import itertools

class trackable(object):
    _counter = itertools.count()

    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls, *args, **kwargs)
        cls.register(obj)
        return obj

    @classmethod   
    def register(cls, object):
        object._creation_number = cls._counter.next()
        

class subtrackable(trackable):
    pass    

class MetaTracker(object):
    class __metaclass__(type):
        def __new__(cls, name, bases, attrs):
            my_order = []
            for (attrName,track) in attrs.items():
                try:
                    my_order.append((track._creation_number, attrName))
                except AttributeError:
                    continue    
            my_order.sort()
            order = []
            #for Class in bases:
            #    try:
            #        order.extend(Class._order)      
            #    except AttributeError:
            #        continue
            order.extend([attrName for (creation, attrName) in my_order])
            attrs["_order"] = order 
            newClass = type.__new__(cls, name, bases, attrs)
            trackable.register(newClass)
            return newClass


class A(MetaTracker):
    a = trackable()
    b = subtrackable()
    c = trackable()
    

print A._order    
#['a', 'b', 'c']

class B(A):
    d = trackable()
    e = subtrackable()
    class Fish(A):
        f = trackable()
        g = trackable()
    h = trackable()     

print B._order    
#['d', 'e', 'Fish', 'h']
print B.Fish._order
#['f', 'g']
