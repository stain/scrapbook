#!/usr/bin/env python
# *-* encoding: utf8
# 
# Copyright (c) 2005 Stian Soiland
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
# URL: http://soiland.no/i/src/pickledb/
# License: MIT
#
"""Tests for pickledb.py

"""

import unittest
import pickledb
import tempfile
import os
import gc
import pickle
import glob
import time

class OpenCloseTests(unittest.TestCase):
    
    def setUp(self):
        self.gc = gc.isenabled()
        # Force deletions to happen right away
        # (neccessary for testAutoClose)
        gc.disable()  
        self.fname = tempfile.mktemp()
        # Might be fucked up by testAutoCloseOnShutdown()
        assert hasattr(pickledb, "os")
            
    def tearDown(self):
        if self.gc:
            # Restore gc status
            gc.enable()
        # Delete tempfile and any lock files etc    
        for file in glob.glob(self.fname + "*"):
            try:
                os.remove(file)     
            except OSError:
                pass
    
    def testOpenCreates(self):
        self.assert_(not os.path.exists(self.fname))
        db = pickledb.open(self.fname)
        self.assert_(os.path.exists(self.fname))
        db.close()
        # Might sound stupid, but don't delete the database on close!
        self.assert_(os.path.exists(self.fname))
  
    def testDoubleOpenFailsLock(self):
        db = pickledb.open(self.fname)
        self.assertRaises(pickledb.LockError, pickledb.open, self.fname)
    
    def testReOpenBeforeClose(self):
        db = pickledb.open(self.fname)
        self.assertRaises(pickledb.AlreadyOpenError, db.open)    
    
    def testOpenCloseOpen(self):
        db = pickledb.open(self.fname)
        db.close()
        # should work even if db still referenced
        db2 = pickledb.open(self.fname)

    def testAutoClose(self):
        db = pickledb.open(self.fname)
        del db # Dereference should close
        db = pickledb.open(self.fname)

    def testAutoCloseOnShutdown(self):
        db = pickledb.open(self.fname)
        # Hard task here, try to delete pickledb.os since __del__
        # calls on shutdown are not done in any particular order,
        # and the os module might be unavailable as a global variable
        del pickledb.os
        del db
        # Get back mr. os
        reload(pickledb)
        db = pickledb.open(self.fname)
        
  
    def testOpenLockfile(self):
        db = pickledb.open(self.fname)
        self.assert_(os.path.exists(self.fname + ".lock"))
        # temp file should not be present after locking
        self.assertEqual(len(glob.glob(self.fname + "*")), 2)
        db.close()
        self.assert_(not os.path.exists(self.fname + ".lock"))
   

class ObjSaveTests(unittest.TestCase):
    """Test object saving. 

    Note that this is white box testing, as _obj, _read() and _write are
    accessed directly, in addition to checking saved content by using
    pickle, bypassing the official interface and locking mechanism.

    We do this on temporary databases, so it's ok =)
    """
    def setUp(self):
        self.fname = tempfile.mktemp()
        self.db = pickledb.open(self.fname)

    def tearDown(self):
        try:
            self.db.close()
        except pickledb.ClosedError:
            pass    
        # Delete tempfile and any lock files etc    
        for file in glob.glob(self.fname + "*"):
            try:
                os.remove(file)     
            except OSError:
                pass
  
    def testCloseDisablesObj(self):
        self.assert_(hasattr(self.db, "_obj"))
        self.db.close()
        self.assert_(not hasattr(self.db, "_obj"))
        self.assertRaises(pickledb.ClosedError, self.db.close)
        self.assertRaises(pickledb.ClosedError, self.db.get, "somekey")

    def testObjIsEmptyDict(self):
        self.assertEqual(self.db._obj, {})
    
    def testSaveChanges(self):
        self.assertEqual(pickle.load(open(self.fname)), {})
        self.db._obj["test"] = 1337
        id_before = id(self.db._obj)
        self.db._write()
        self.assertEqual(pickle.load(open(self.fname)), {"test": 1337})
        self.db._read()
        id_after = id(self.db._obj)
        # Should be a reloaded instance    
        self.assertNotEqual(id_before, id_after)
        self.assertEqual(self.db._obj, {"test": 1337})

        # What about subsequent writes? 
        self.db._obj["knott"] = 76
        self.assertEqual(self.db._obj, {"test": 1337, "knott": 76})
        self.db._write()
        self.db._obj["knott"] = 42
        self.db._write()
        self.db._read()
        self.assertEqual(self.db._obj, {"test": 1337, "knott": 42})
    
    def testCloseAndOpen(self):
        self.db._obj["fish"] = 31337      
        self.db.close()
        self.assertEqual(pickle.load(open(self.fname)), {"fish": 31337})
        self.db = pickledb.open(self.fname)
        self.assertEqual(pickle.load(open(self.fname)), {"fish": 31337})
        self.assertEqual(self.db._obj, {"fish": 31337})
    
    def testTruncate(self):
        for x in range(10):
            self.db[x] = x
        large = os.stat(self.fname).st_size  
        self.db.clear()
        # Should shrink the file size
        small = os.stat(self.fname).st_size    
        self.assert_(small < large)
        

class DictTests(unittest.TestCase):
    def setUp(self):
        self.fname = tempfile.mktemp()
        self.db = pickledb.open(self.fname)

    def tearDown(self):
        try:
            self.db.close()
        except pickledb.ClosedError:
            pass    
        # Delete tempfile and any lock files etc    
        for file in glob.glob(self.fname + "*"):
            try:
                os.remove(file)     
            except OSError:
                pass

    def testEmpty(self):
        self.assertEqual(self.db, {}) 
        self.assertEqual(str(self.db), "{}")
        self.assertEqual(repr(self.db), "{}")
        self.assertEqual(len(self.db), 0)    
    
    def testEverything(self):
        """Test lots of dict operations"""
        self.db["hei"] = 256
        # Should save right away
        self.assertEqual(pickle.load(open(self.fname)), {"hei": 256})
        self.assertEqual(self.db, {"hei": 256})
        self.assertEqual(self.db["hei"], 256)
        self.assert_("hei" in self.db)
        for elem in self.db:
            self.assertEqual(elem, "hei")
        self.assertEqual(elem, "hei")

        self.assertEqual([(x,y) for x,y in self.db.items()], 
                         [("hei", 256)])
        self.assertEqual([(x,y) for x,y in self.db.iteritems()], 
                         [("hei", 256)])
        self.assertEqual([x for x in self.db.values()], 
                         [256])
        self.assertEqual([x for x in self.db.itervalues()], 
                         [256])
        self.assertEqual([x for x in self.db.keys()], 
                         ["hei"])
        self.assertEqual([x for x in self.db.iterkeys()], 
                         ["hei"])
        self.assert_(self.db > {})
        self.assert_(self.db <= {"hei": 1337})
        del self.db["hei"]
        self.assertEqual(pickle.load(open(self.fname)), {})
        self.assertEqual(self.db, {})
        self.assert_(self.db < {"hei": 1337})
        self.assert_(self.db <= {})
        self.assertEqual(self.db.setdefault("knott", 56), 56)
        self.assertEqual(pickle.load(open(self.fname)), {"knott":56})
        self.assertEqual(self.db["knott"], 56)
        self.assertEqual(self.db.setdefault("knott", 1337), 56)
        self.assertEqual(self.db.pop("knott"), 56)
        self.assertEqual(pickle.load(open(self.fname)), {})
        self.assertEqual(self.db, {})
        self.db["fish"] = 988
        self.db["knott"] = 0
        self.assertEqual(len(self.db), 2)
        self.db.update({"fish": 9765, "cod": 1337})
        self.assertEqual(pickle.load(open(self.fname)), 
                        {"fish": 9765, "cod": 1337, "knott": 0})
        self.assertEqual(self.db.copy(), 
                        {"fish": 9765, "cod": 1337, "knott": 0})
        self.assertNotEqual(id(self.db._obj), id(self.db))
        self.assertNotEqual(id(self.db._obj), id(self.db.copy()))
        self.db.clear()
        self.assertEqual(pickle.load(open(self.fname)), 
                         {})
        self.db["knott"] = 98
        self.assertEqual(self.db.get("fish"), None)
        self.assert_("fish" not in self.db)
        self.assert_(not self.db.has_key("fish")) 
        self.assertEqual(self.db.get("knott"), 98)
        self.assert_(self.db.has_key("knott")) 
        self.assertEqual(self.db.popitem(), ("knott", 98))
        self.assertEqual(self.db, {})
        self.assertEqual(pickle.load(open(self.fname)), 
                         {})

class WriteTests(unittest.TestCase):
    def setUp(self):
        self.fname = tempfile.mktemp()

    def tearDown(self):
        # Delete tempfile and any lock files etc    
        for file in glob.glob(self.fname + "*"):
            try:
                os.remove(file)     
            except OSError:
                pass

    def testAlwaysWrite(self):
        db = pickledb.open(self.fname)
        start = time.time()
        for x in xrange(500):
            # Insertions are slow because _write() is called for
            # every insert, writing out all elements
            db[x] = x
        used = time.time() - start
        self.assert_(used < 30.0)
        # If it's too fast, something is wrong! =))
        self.assert_(used > 0.2)
        db.close()
    
    def testThreadedWrite(self): 
        try:
            db = pickledb.open(self.fname, write="thread")
            start = time.time()
            # NOTE: 20x the loop in testAlwaysWrite
            for x in xrange(10000):
                # Insertions are slow because _write() is called for
                # every insert, writing out all elements
                db[x] = x
            used = time.time() - start
            # Should be really fast as we are only doing inserts
            self.assert_(used < 1.0)
            # And the write thread should not have written anything yet
            self.assertEqual(pickle.load(open(self.fname)), 
                             {})
            time.sleep(2)
            # Thread sleeps 1 second between writing, and so we should wait
            # at most 2 seconds and be sure that content is in file
            self.assertEqual(len(pickle.load(open(self.fname))), 
                             10000)

            # Make sure thread only writes on change
            stat = os.stat(self.fname)
            time.sleep(2)
            stat2 = os.stat(self.fname)
            # Should not have rewritten since no changes have been
            # made in these two seconds
            self.assertEqual(stat, stat2)
            db.clear()
            try:
                self.assertEqual(len(pickle.load(open(self.fname))), 
                                 10000)
            except EOFError:    
                # The test might fail now and then because we might
                # not be fast enough to do the load-test before the
                # writing thread does it work. For instance, 
                # EOFError might be raised because the other thread
                # has started writing.
                pass

            # Make sure a sync really flushes out without
            # any delays. Contrary to the previous code, the code below
            # should NEVER fail.
            db.sync()
            self.assertEqual(pickle.load(open(self.fname)), 
                             {})
            db["fish"] = 1337
            db.close()
            self.assertEqual(pickle.load(open(self.fname)), 
                             {"fish": 1337})
        finally:
            try:
                # To make sure thread finishes if one of the 
                # tests above fails
                db.close()         
            except:
                pass    
        
    def testThreadedReopen(self): 
        try:
            db = pickledb.open(self.fname, write="thread")
            db["fish"] = 150279
            db.close()
            # Re-open of threaded database should start new 
            # writer thread
            db.open()
            self.assertEqual(db["fish"], 150279)
            db["fish"] = 98
            db.close()
            self.assertEqual(pickle.load(open(self.fname)), 
                             {"fish": 98})
        finally:
            try:
                db.close()
            except:
                pass        
        
class AdvancedPicklingTest(unittest.TestCase):
    def setUp(self):
        self.fname = tempfile.mktemp()
        self.db = pickledb.open(self.fname)

    def tearDown(self):
        try:
            self.db.close()
        except pickledb.ClosedError:
            pass    
        # Delete tempfile and any lock files etc    
        for file in glob.glob(self.fname + "*"):
            try:
                os.remove(file)     
            except OSError:
                pass
    
    def testDeepDict(self):
        self.db["a"] = {}            
        self.assertEqual(pickle.load(open(self.fname)), 
                         {"a": {}})
        self.db["a"]["b"] = "mutable"
        # No way that PickleDB can know that db["a"] has been
        # updated
        self.assertEqual(pickle.load(open(self.fname)), 
                         {"a": {}})
        # But after a sync it should be visible
        self.db.sync()
        self.assertEqual(pickle.load(open(self.fname)), 
                         {"a": {"b": "mutable"}})
    
    def testObject(self):
        x = Mutable()
        # Override b value to make sure constructor
        # is not run on reload
        x.b = 15
        self.assertEqual(x.res(), 29)
        self.db["x"] = x
        self.db.close()
        self.db.open()
        # as __eq__ is undefined in Mutable, should
        # be new instance
        self.assertNotEqual(self.db["x"], x)
        # But the internals should work   
        self.assertEqual(self.db["x"].res(), 29)
 
    def testKeys(self):
        # All the keys allowed for dictionaries are
        # allowed
        self.db[14] = "hei"
        self.db["hello"] = None
        self.db[1,2] = "tuple"
        self.assertEqual(pickle.load(open(self.fname)), 
                         {14: "hei",
                          "hello": None,
                          (1,2): "tuple"})

        self.db.clear()
        x = Mutable()
        self.assertEqual(x.res(), 14)
        self.db[x] = x
        self.db.close()
        self.db.open()
        # Since the "x" key inside the db has been pickled and
        # unpickled, it will no longer match our x since
        # we have not defined __hash__ and __eq__
        self.assertRaises(KeyError, lambda: self.db[x])
        # But we can fetch it anyway
        key,value = self.db.popitem()
        # And this should be the very same object 
        self.assertEqual(key, value)
        # With the expected behavour
        self.assertEqual(key.res(), 14)
        self.assertNotEqual(key, x)
        self.assertNotEqual(id(key), id(x))
         
        # But with a hashable object, this should work:
        y = Hashable()
        self.assertEqual(x, Hashable())
        self.db[y] = None
        self.db.close()
        self.db.open()
        self.assertEqual(self.db[y], None)
        # If we mutate our before-pickle version, it should no longer
        # match
        y.a = 15
        self.assertRaises(KeyError, lambda: self.db[y])
        

class Mutable:
    def __init__(self):
        self.a = 14        
        self.b = 0
    def res(self):
        return self.a + self.b

class Hashable:        
    def __init__(self):
        self.a = 14
    def __hash__(self):
        return hash(self.a)    
    def __eq__(self, other):
        return hasattr(other, "a") and self.a == other.a
        

# FIXME: Check dictionary interface

if __name__ == "__main__":
    unittest.main()            

