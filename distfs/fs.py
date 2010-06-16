
import uuid
import datetime
from StringIO import StringIO

class Resource(object):
    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent
        self.creationdate = datetime.datetime.now()
        self.lastmodified = self.creationdate
        self.identifier = uuid.uuid_str()
        if parent:
            parent.add(name, self)

    def _updated(self):          
        self.lastmodified = datetime.datetime.now()
    
    def path(self):
        if self.parent:
           return self.parent.path() + "/" + self.name
        return self.name   
    
    def root(self):
        if not self.parent:
            return self    
        return self.parent.root()    

    # Ignore the rest of the path by default
    def get(self, path):
        return self
   
    def __str__(self):
        return self.path() or "/"
    
    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self)    

        

class Directory(Resource):
    contenttype = "httpd/unix-directory"
    def __init__(self, name, parent=None):
        super(Directory, self).__init__(name, parent) 
        self.children = {}
    
    def add(self, name, resource):
        # FIXME: Make thread safe
        if name in self.children:
            # FIXME> Real exceptions
            raise AttributeError, "Already exist %s" % name
        self.children[name] = resource     
        self._updated()
    
    def remove(self, name):
        # FIXME: Make thread safe
        obj = self.children[name]
        if obj.parent == self:
            obj.parent == None
        del self.children[name]   
        self._updated()
                
    def get(self, path):
        if "/" in path:
            child, rest = path.split("/", 1)    
        else:
            child = path    
            rest = None
        if not child or child == ".":
            dir = self
        elif child == "..":
            dir = self.parent or self
        else:
            dir = self.children[child]      
        if not rest:    
            return dir
        return dir.get(rest)    
            

class File(Resource):
    def __init__(self, name, parent=None):
        super(File, self).__init__(name, parent) 
        self.contenttype = "text/plain"
        self.data = StringIO()
        
    def open(self, mode="r"):
        # FIXME> NOT THREAD SAFE!!
        self.data.seek(0)
        return self.data
    
    @property
    def size(self):
        return self.data.len    
        

def dummies():
    root = Directory("")
    pub = Directory("pub", root) 
    etc = Directory("etc", root) 
    File("passwd", etc)
    hello = File("hello.txt", pub)
    hello.open("w").write("Hello world\n")
    return root 

import unittest
import fs
class TestGet(unittest.TestCase):
    def setUp(self):
        self.root = fs.dummies()

    def testGetDir(self):
        pub = self.root.get("pub")
        self.assertEqual("/pub", pub.path())
        pub = self.root.get("pub/")
        self.assertEqual("/pub", pub.path())
        pub = self.root.get("pub//")
        self.assertEqual("/pub", pub.path())
        pub = self.root.get("/pub//")
        self.assertEqual("/pub", pub.path())
        pub = self.root.get("/pub/.")
        self.assertEqual("/pub", pub.path())
        pub = self.root.get("/pub/./")
        self.assertEqual("/pub", pub.path())
        pub = self.root.get("/pub/..")
        self.assertEqual("", pub.path())
        
    def testGetRelative(self):
        passwd = self.root.get("pub/../etc/./../../etc/././passwd/../../pub")
        self.assertEqual("/etc/passwd", passwd.path())
        

if __name__ == "__main__":
    unittest.main()
