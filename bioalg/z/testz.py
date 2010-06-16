#!/usr/bin/env python

import unittest
import random
import itertools

import z
import bruteforce

class TestZ(unittest.TestCase):
    def testFindZs(self):
        # From Gusfield 1.3 p7
        s = "aabcaabxaaz"
        Z = z.Z(s)
        # Note: Z[4] instead of [3], we are zero-based
        self.assertEquals(3, Z[4])
        self.assertEquals(1, Z[5])
        self.assertEquals(0, Z[6])
        self.assertEquals(0, Z[7])
        self.assertEquals(2, Z[8])
   
    def testFindZDeep(self):
        s = "aabcaabxaaz"
        Z = z.Z(s)
        for k,length in Z.z.items():
            should_be = s[:length]
            but_is = s[k:k+length]
            #print k, length, should_be, but_is
            self.assertEquals(should_be, but_is)
             
    def testFindPinT(self):
        SIZE=1000
        HITS=5
        p, t = makeString(size=SIZE, hits=HITS)
        self.assertEquals(SIZE, len(t))        
        self.assertEquals(HITS, t.count(p))

        hits = list(z.findall(p, t))
        self.assertEquals(HITS, len(hits))

        for hit in hits:
            self.assertEquals(p, t[hit: hit+len(p)])


class TestBruteForce(unittest.TestCase):
    def testFindPinT(self):
        p, t = makeString()
        for hit in bruteforce.findall(p, t): 
            self.assertEquals(p, t[hit: hit+len(p)])

class TestBoth(unittest.TestCase):
    def testFindPinT(self):
        p, t = makeString()
        z_hits = z.findall(p, t)
        brute_hits = bruteforce.findall(p, t)
        for z_hit, brute_hit in itertools.izip(z_hits, brute_hits):
            self.assertEquals(z_hit, brute_hit)
            

def makeString(pattern=30, size=1000, hits=5, alphabet="aB "):
    p = "".join(random.choice(alphabet) for n in range(pattern))
    rand_t_len = size - pattern*hits
    if rand_t_len < 1:
        raise ValueError, "Too small size: %s" % size
    t = "".join(random.choice(alphabet) for n in range(rand_t_len))
    for insertion in sorted(
        (random.randint(0, rand_t_len) for n in range(hits)),
        reverse=True):
           t = t[:insertion] + p + t[insertion:]
    return p, t         
         
         
         

if __name__ == "__main__":
    unittest.main()
