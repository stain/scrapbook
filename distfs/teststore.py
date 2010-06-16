#!/usr/bin/env python

import unittest
import shutil
import tempfile
import os
import sha
import time

import store

class CreateDirMixin(object):
    def setUp(self):
        """Create a directory for our store"""
        self.dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Remove the temporary directory"""
        shutil.rmtree(self.dir)   


class TestBlockStoreConstructor(CreateDirMixin, unittest.TestCase):

    def testExistingEmpty(self):
        """Test creation in existing, empty directory"""
        b = store.BlockStore(self.dir)
        meta = os.path.join(self.dir, "distfs.meta")
        self.failUnless(os.path.isfile(meta))
    
    def testNonExisting(self):
        """Test creation of non-existing directory"""
        # Neither 1337 or deep exists!
        sub = os.path.join(self.dir, "1337", "deep")
        self.failIf(os.path.exists(os.path.join(self.dir, "1337")))

        b = store.BlockStore(sub)    
        self.failUnless(os.path.isdir(sub))
        self.assertEqual(b.directory, sub)

        meta = os.path.join(sub, "distfs.meta")
        self.failUnless(os.path.isfile(meta))

    def testFailsExist(self):
        """Make sure construction fails on an existing non-distfs
        non-empty directory"""
        file = os.path.join(self.dir, "1337")
        self.failIf(os.path.exists(file))
        # Make a file so self.dir is not empty
        open(file, "w").close()
        self.failUnless(os.path.exists(file))

        self.assertRaises(store.NotAFilestore, 
                          store.BlockStore, self.dir)
        # And shouldn't have made any meta file either
        meta = os.path.join(self.dir, "distfs.meta")
        self.failIf(os.path.exists(meta))
    
    def testMeta(self):
        """Test that metafile is created correctly"""
        b = store.BlockStore(self.dir)
        meta = os.path.join(self.dir, "distfs.meta")
        self.failUnless(os.path.isfile(meta))
        meta_content = open(meta, "rb").read()
        # This will fail in later versions, to notify us that we might
        # have to do something for backwards or forward compatability
        self.assertEqual(meta_content, "distfs blockstore v0.2\n")
                
    def testFailWrongMeta(self):
        """Test that construction fails on unknown meta file"""              
        meta = os.path.join(self.dir, "distfs.meta")
        f = open(meta, "w")
        f.write("Not a metafile\n")
        f.close()
        self.assertEqual(open(meta).read(), "Not a metafile\n")
        self.assertRaises(store.FilestoreUnknownVersion,
                          store.BlockStore, self.dir)
        # And that he didn't change the meta file
        self.assertEqual(open(meta).read(), "Not a metafile\n")
    

class TestStoreMixin(object):
    """Test external API of storing.
    
    This is an abstract class to be implemented by test classes for
    different backends.
    """
    DATA = [
        "Fish",
        "Other",
        "Storage",
        "1337",
        "fish",
        "soup",
    ]
    
    def testStoreRetrieveString(self):
        id = self.store.store(self.DATA[0])
        self.assertEqual(self.store.retrieve(id), 
               self.DATA[0])
    
    def testStoreOtherID(self):
        id = self.store.store(self.DATA[1], "1337")
        self.assertEqual(id, "1337")
        self.assertEqual(self.store.retrieve("1337"), 
                         self.DATA[1])
        # Should fail
        self.assertRaises(store.NotFoundError, 
                self.store.retrieve, 
                 sha.sha(self.DATA[1]).hexdigest())
        
    def testExists(self):
        id = self.store.store(self.DATA[2])
        self.assert_(self.store.exists(id))    
        self.assert_(not self.store.exists("1337"))
      

    def testRemove(self):
        id = self.store.store(self.DATA[3])
        self.store.retrieve(id)
        self.store.remove(id)
        self.assertRaises(store.NotFoundError, 
                self.store.retrieve, id)
        self.assertRaises(store.NotFoundError, 
                self.store.remove, id)
  
    def testStoreTwiceWithSameID(self):    
        id = "1234-56-789"
        fish = self.store.store(self.DATA[4], id)
        # Tries to store a different value with same id
        self.assertRaises(store.AlreadyExistsError,
                    self.store.store, self.DATA[5], id)
        # Behaviour of self.store.store("fish", id) is undefined,
        # it could or could not raise an error

    
class CreateStoreMixin(CreateDirMixin):
    def setUp(self):
        super(CreateStoreMixin, self).setUp()
        self.store = store.BlockStore(self.dir)
        meta = os.path.join(self.dir, "distfs.meta")
        self.failUnless(os.path.isfile(meta))

class TestBlockStoreBlack(CreateStoreMixin, TestStoreMixin, 
                          unittest.TestCase):
    def testGeneratedIdIsSha1(self):
        id = self.store.store("HashMe")
        self.assertEqual(id, sha.sha("HashMe").hexdigest())
    
    def testStoreTwice(self):
        id = self.store.store("First time")      
        # Store the same again, calculated hash
        other = self.store.store("First time")
        # Should work, and return the same hash. The backend is free to
        # actually store it again or not
        self.assertEqual(id, other)
    
    def testStoreOtherInstance(self):
        # Should be able to retrieve both files stored
        # before and after creating a new BlockStore instance
        before_id = self.store.store("before")    
        other = store.BlockStore(self.dir)
        after_id = self.store.store("after")    
        self.assertEqual(other.retrieve(before_id),
                         "before")
        self.assertEqual(other.retrieve(after_id),
                         "after")
        # And if stored from the other, should be visible
        # even if other is deleted
        other_id = other.store("other")
        del other
        time.sleep(0.5)
        self.assertEqual(self.store.retrieve(other_id),
                         "other")
    

class TestBlockStoreWhite(CreateStoreMixin, unittest.TestCase):
    def testEmpty(self):
        self.assertEqual(["distfs.meta"],
                         os.listdir(self.dir))
    def testStoreSimple(self):
        id = self.store.store("Fish\n")
        dir = id[:2]
        self.assertEqual(set((dir, "distfs.meta")),
                         set(os.listdir(self.dir)))
        self.assertEqual([id], 
             os.listdir(os.path.join(self.dir, dir)))

        path = os.path.join(self.dir, dir, id)
        # Should be the exact content, and not \r\n 
        self.assertEqual(open(path, "rb").read(), 
                         "Fish\n")

class LargeStoreMixin(CreateStoreMixin):
    def setUp(self):    
        super(LargeStoreMixin, self).setUp()
        self.block_store = self.store
        self.store = store.LargeStore(self.block_store)


class TestLargeStoreSmallData(LargeStoreMixin, TestStoreMixin,
                          unittest.TestCase):
    pass

class TestLargeStoreLargeData(TestLargeStoreSmallData):
    DATA = [data * 130000 for data in TestLargeStoreSmallData.DATA]

class TestLargeStoreVeryLargeData(TestLargeStoreLargeData):
    def setUp(self):
        super(TestLargeStoreVeryLargeData, self).setUp()
        self.store = store.LargeStore(self.block_store, blocksize=1024)

    

if __name__ == "__main__":
    unittest.main()

