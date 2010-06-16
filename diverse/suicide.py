# Start a Python shell and run:
# >>> import suicide

fisk = "Hello"

class A(object):
    def __del__(self):
        print "Deleting the A", self
a = A()        

import sys
# Nono, let's die!
del sys.modules["suicide"]
# This printout might not be what you expect!
print fisk, sys, a, A
