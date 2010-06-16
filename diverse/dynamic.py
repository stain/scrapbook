#!/usr/bin/env python
"""Dynamic programming by wrapping function calls and caching results.

Dynamic programming means simply to remember old calculated values. If
the calculation is done by a function, it's pretty simple to write a
wrapper that caches results based on the parameters passed by. This
version even handles keyword and default parameters by inspecting the
function signature.

Copyright (c) 2002 Stian Soiland

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


import inspect,sys

class DynamicFunction:
    def __init__(self, function):
        self.cache = {}
        self.function = function
        argspec = inspect.getargspec(self.function)
        self.parameters = argspec[0]

        # Store the defaults in a dictionary instead
        defaults = argspec[3]
        self.defaults = {}
        if(defaults):
            for position in range(-len(defaults), 0): # negative!
                name = self.parameters[position]
                value = defaults[position]
                self.defaults[name] = value
        
    def __call__(self, *args, **kwargs):
        parameters = self.defaults.copy() # At first we only have the defaults

        # And all keyword entries, including those not defined
        parameters.update(kwargs) 
        
        # And finally we add the positional parameters. Note that we
        # this way introduces the possibility that a parameter is given
        # both in keyword form and positional form, normally not allowed
        # by Python. This behaviour is not specified any further, you cannot
        # be certain of whether the positional or the keyword argument
        # will survive, however, in this particular version, it is the
        # positional that survives.
        
        if (len(args) > len(self.parameters)):
            params = len(self.parameters)
        else:
            params = len(args)
        for param in range(params):
            name = self.parameters[param]
            value = args[param]
            parameters[name] = value

        # Usually [], but otherwice stuff that would be placed in *args
        # in the final function call
        args = args[len(self.parameters):] 
        

        # Make it hashable!
        try:
            ourCall = hash( (tuple(args), tuple(parameters.items()) ) )
        except KeyError:
            print "Cannot cache unhashable", args, "and", parameters
            return self.function(*args, **parameters)

        try:
            # Woo! We cached it!
            result = self.cache[ourCall]
            # print "Cached", args, parameters, "result is", result
        except KeyError:
            # Call the original function!
            result = self.function(*args, **parameters)
            # And put it into the cache!
            # print "Caching", args, parameters, "result is", result
            self.cache[ourCall] = result
        return result    


def fibonacci(n):
    """Simple recursive fibonacci function""" 
    if(n < 2):
        return long(n)
    else:
        return fibonacci(n-2) + fibonacci(n-1)

# Wraps the fibonacci function as a dynamic one. 
# Note that this will actually make the internal
# fibonacci()-calls use the caching too

fibonacci = DynamicFunction(fibonacci)

def testFibonacci(max=10000):
    """Test the cache by calling fibonacci(max) in 
    smaller steps, to avoid overusing the stack. """
    for a in range(1,max,sys.getrecursionlimit()-100):
        b = fibonacci(a)
    b = fibonacci(max)    
