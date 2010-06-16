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
"""A dictionary-like object that stores its content in a file.

"""


try:
    import cPickle as pickle
except ImportError:
    import pickle    

import tempfile    
import os
from doc_exception import DocstringException
import time
    
class Error(DocstringException):
    """General pickledb error"""

class FileError(Error):
    """General read/write file error"""

class LockError(FileError):
    """Database file locked by other user"""

class ClosedError(Error):
    """Database file closed, no further access possible"""

class AlreadyOpenError(Error):
    """Database file is already open, cannot reload"""

class UnknownWriteModeError(Error):
    """Write mode must be 'sync' or 'thread'"""


class _dict_wrapper(type):
    """Metaclass for adding dictionary wrapper methods"""
    # methods that don't modify the dict
    read = ['__cmp__', '__contains__', '__eq__', '__ge__',
            '__getitem__', '__gt__', '__iter__', '__le__',
            '__len__', '__lt__', '__ne__', '__repr__', '__str__',
            'copy', 'fromkeys', 'get', 'has_key', 'items', 'iteritems',
            'iterkeys', 'itervalues', 'keys', 'values']
    
    # methods that modify the dict
    write = ['__delitem__', '__setitem__', 'clear', 'pop', 'popitem',
             'setdefault', 'update']
    
    # All methods 
    methods = read + write         
    
    def _gen_method(cls, methodname):
        def wrapper(self, *args, **kwargs):
            """Wrapper for dictionary access %s""" % methodname
            if not hasattr(self, "_obj"):
                raise ClosedError 
            method = getattr(self._obj, methodname)
            if methodname in cls.write:
                # Tag as updated
                self._before_update()
            try:
                res = method(*args, **kwargs)
            finally:    
                if methodname in cls.write:
                    # Make sure locks are released,etc even if an error
                    # occured in method()
                    self._after_update()
            return res
        return wrapper     
    _gen_method = classmethod(_gen_method)
    
    def __new__(cls, name, bases, dict):
        # Add wrappers for dict methods
        for methodname in cls.methods:
            dict[methodname] = cls._gen_method(methodname)
        return type.__new__(cls, name, bases, dict)


class PickleDB(object):
    """A dictionary-like object that stores its content in a file.

    The object can be initiated either by pickledb.PickleDB()
    or pickledb.open(), the latter method is for duck-typing shelve/dbm
    modules.

    If the given file does not exists, it will be created.
    
    The argument write can be "sync" or "thread", defining when
    changes are written to disk:

      sync    Changes written to file immediately on updating.
              This is slow for many updates, but makes sure that all
              changes are commited immediately. This is the default
              setting.
      
      thread  Changes are written to file in the background every 
              second by a seperate thread. close() will however 
              still be syncronized and not return before 
              all changes are written to disk. In fact, close() 
              *have* to be called to make sure writer thread
              finishes.
              
              This option requires threading support. To change the
              delay between writes, modify the attribute write_every, or
              call sync() when a sync is really needed.


    This object can be used as the shelve module, but does not
    require or use dbm for storage. Instead, this module uses pickle
    for storing and loading the file. Note that all data are
    kept in memory and written to disk, and PickleDB can therefore not
    be used for larger amounts of data.

    Unlike shelve/dbm, since the whole dictionary is pickled, all keys
    valid for a normal dictionary can be used. Note however that using
    user defined objects without __hash__/__eq__ methods is not
    recommended, since the depickled object key will be unique, and
    can only be fetched from keys().

    A lock file ensures that a database is only open by one process
    at a time. This is also a limitation compared to shelve/dbm, but
    it also ensures that you don't get a corrupted database file,
    something you have likely experienced with dbm and the main
    inspiration for writing this module.

    Use close() to close the database and release the lock file. After
    closing you might however reopen the database with open().

    By default, changes are written to disk every time the dictionary is
    updated directly, ie. on insert/update/delete. To make sure
    changes in mutable values are stored, sync() or close() must
    be called manually. 
    
    If the write mode is set to "thread", dictionary changes are written 
    in the background every self.write_every seconds, by default 1.0
    seconds. To make sure changes in mutable values are stored, sync() 
    must be used here as well. In threaded mode, close() *must* be
    called to finish the writer thread.
    """

    __metaclass__ = _dict_wrapper
    def __init__(self, filename, write="sync"):
        self._updated = False
        self.filename = filename
        self.writemode = write
        if self.writemode == "thread":
            # Will write every 1.0 second (can be changed by the user
            # afterwards
            self.write_every = 1.0
        self.open()
   
    def open(self):
        """Reopen database file.
        
        This method is only callable after calling close(), 
        and might throw LockError.
        """
        # Note: Also callable from constructor

        if hasattr(self, "_obj"):
            raise AlreadyOpenError
        self._file = self._lock_open(self.filename)
        # Check end of file
        self._file.seek(0, 2)
        if self._file.tell() == 0:
            # File is empty, start with empty dict
            self._obj = {}
            self._write()
        else:    
            self._read()
        if self.writemode == "thread":
            import threading
            self._write_lock = threading.Lock()
            self._writer = threading.Thread(target=self._write_thread)
            self._writer.loop = True
            self._writer.start()
    
    def _write_thread(self):
        """Continous write thread"""
        while self._writer.loop:
            time.sleep(self.write_every)
            self.sync(only_updated=True)

    def sync(self, only_updated=False):        
        """Makes sure that all changes have been written to file.
        
        If the parameter only_updated is set, changes are only
        written if the dictionary has been updated directly. Note that
        changes in mutable values are not neccessarily written if
        only_updated is set.
        """
        try:
            if self.writemode == "thread":
                self._write_lock.acquire()
            if not only_updated or self._updated:
                self._write()
                self._updated = False
        finally:    
            if self.writemode == "thread":
                self._write_lock.release()
    
    def _read(self):
        """Reads from open file, throws away old self._obj"""
        self._file.seek(0)
        self._obj = pickle.load(self._file)
    
    def _write(self, obj=None):
        """Stores to object file, overwites existing data on file.

        If obj is not given, self._obj will be saved. 
        """
        # We allow this obj-parameter to make close() delete self._obj
        # before calling _write()
        if obj is None:
            obj = self._obj
        self._file.seek(0)
        # FIXME: Should use temporary file and link
        pickle.dump(obj, self._file)
        # Make sure written out
        self._file.flush()
        # Frees any previously used space
        self._file.truncate()
    
    def _before_update(self):
        """Called by metaclass before the dictionary is updated"""
        if self.writemode == "thread":
            # To avoid changing self._obj while we are pickle-dumping
            self._write_lock.acquire()

    def _after_update(self):
        """Called by metaclass after the dictionary is updated"""
        self._updated = True    
        if self.writemode == "sync":
            self.sync(only_updated=True)
        elif self.writemode == "thread":
            self._write_lock.release()
        else:
            raise UnknownWriteModeError
    
    def __del__(self):
        """Destructor that closes database.
        
        Note that it is not guaranteed that this method will run. 

        For instance, in "thread" writer mode, the writer thread
        will always keep an reference to self, and thereby
        prevent the destructor to run.

        To be sure, always call close() manually.
        """
        if hasattr(self, "_obj"):
            self.close()

    def close(self):    
        """Close the database and release lock.
        
        Pending updates are written to file.  No further operations will
        be possible after calling close(), unless you call open() to
        reopen the database.

        In threaded mode, this method will wait for the writer thread
        to finish before returning, and might therefore take
        self.write_every seconds to return.
        """
        if not hasattr(self, "_obj"):
            raise ClosedError 
        if self.writemode == "thread":
            self._writer.loop = False
            # Let writer thread finish first
            self._writer.join()
        # disable any futher use as we from this point on
        # can't guarantee that changes from other threads 
        # gets saved, or that lookups are from locked file
        obj = self._obj
        del self._obj 
        self._write(obj)
        # Free lock
        self._lock_close()
        del self._file

    def _lock_open(self, filename):    
        """Open the file using the .lock method in r+ mode.
        
        The file will be created if it does not exist.
        
        All programs that access the given filename must use the
        same locking protocol, namely:

        1. Create a temporary file that will always be deleted
           afterwards.
        2. Try to os.link() temporary file to filename.lock
        3. If link succeeded, you have the lock, and may
           open the actual file for exclusive read/write access.
        4. After closing the actual file, the filename.lock file is
           removed.

        To close the returned file, use _lock_close().
        """
        # Store away the unlink function in case 
        # the os module is deleted before us and we
        # still need to remove our lock file
        self.__unlink = os.unlink
        
        lockfile = filename + ".lock"
        dir = os.path.dirname(lockfile)
        prefix = os.path.basename(lockfile)
        tmplock = tempfile.NamedTemporaryFile(prefix=prefix, dir=dir)
        try:
            try:
                os.link(tmplock.name, lockfile)
            except OSError:
                raise LockError
        finally:
            tmplock.close()
        # open() shadowed by module level open()
        # Create if needed first    
        file(filename, "a")
        # And return in r+-mode for read/write
        # (no, mode "a" won't work for subsequent pickling)
        return file(filename, "r+")       

    def _lock_close(self):
        """Close the open file and remove lock.
        """
        lockfile = self._file.name + ".lock"
        self._file.close()
        self.__unlink(lockfile)


# open function is the same as PickleDB constructor
open = PickleDB
