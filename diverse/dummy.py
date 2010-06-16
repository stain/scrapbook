"""A dummy object that can do anything

Copyright (c) 2004 Stian Soiland, Magnus Nordseth

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

Authors: Stian Soiland <stian@soiland.no>
         Magnus Nordseth <magnus@nordseth.net>

License: MIT
"""

class Dummy(object):
    """An object that can do anything in the world"""
    def __call__(self, *args, **kwargs):
        """Can be called with any kind of parameters, returns
           a new Dummy."""
        return Dummy()
    def __getattribute__(self, key):
        """Any attribute created and stored on demand. All
           attributes are new Dummys."""
        try:
            value = object.__getattribute__(self, key)
        except AttributeError:
            value = self()
            # remember it to next time! =)
            setattr(self, key, value)
        return value
