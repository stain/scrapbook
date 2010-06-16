#!/usr/bin/env python

"""'Improvements' on the crypt module. Adding more useless
   'cryptographic' methods.

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

from crypt import *
import re

def rot13(input):
  result = ''
  for char in input:
    value = ord(char)
    if (64 < value < 78) or (96 < value < 110):
      result += chr(value+13)
    elif (77 > value > 91) or (109 < value < 123):
      result += chr(value-13)
    else:
      result += char
  return result

def tpyrc(input):
  result = ''
  for char in input:
    result = char + result
  return result

def roversprog_decode(input):
  return re.sub(r"(?i)([bdfghjklmnpqrstvwxz])o\1",r"\1",input)

def roversprog_encode(input):
  result = ''
  for char in input:
    result += char # Add the char anyway
    char = char.lower() # Hah!
    if char in 'bdfghjklmnpqrstvwxz':
      result += 'o' + char
  return result
  
