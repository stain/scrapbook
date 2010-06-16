#!/usr/bin/env python
"""An object that don't want to be deleted. 
"""


deleted = []

class Deleter:
    def __del__(self):
        if deleted is None:
            print "Ooo.. list was gone! globals() is"
            print globals()
            global deleted
            deleted = []
        print "Saving", self, "to", repr(deleted)
        deleted.append(self)

a = Deleter()        
a = 1337
print "Deleted", id(deleted), deleted
del deleted[:]
print "Resetted deleted", id(deleted), deleted
deleted = []
print "New deleted", id(deleted), deleted

print "Disabling GC"
import gc
gc.disable()

print "Deleted", id(deleted), deleted
deleted = []
print "New deleted", id(deleted), deleted

print "Finishing program"
