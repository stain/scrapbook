
from itertools import izip

def findall(pattern, text):
    for pos in xrange(len(text)):
        if pattern == text[pos:pos+len(pattern)]:
            yield pos
            
