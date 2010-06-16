
import os
from sha import sha
import tempfile
import uuid

UUID_SIZE = len(uuid.uuid_str())
 
class error(Exception):
    """BlockStore error"""

class FilestoreError(error):    
    """File store error"""

class NotAFilestore(FilestoreError):
    """Not a file store"""

class FilestoreUnknownVersion(FilestoreError):
    """Unknown version of file store"""

class FileIOError(FilestoreError):
    """Could not read/write"""

class NotFoundError(KeyError, error):
    """Block not found"""

class AlreadyExistsError(KeyError, error):
    """Block with explicit id already exist"""    


class Store(object):
    def __init__(self):
        raise TypeError, "Abstract class"

    def store(self, data, id=None):
        """Persistantly store a string using a given unique string id.

        The data can later be retrieved using self.retrieve(id).

        The id should be globally unique, like an uuid or a hash of the
        data. If id is not provided, one will be calculated using
        self._hash(), and returned by this method.
        
        If there is already a string saved for the explicit id, an
        AlreadyExistsError will be thrown. For implicit ids calculated
        by hashing, the identifier will be returned immediately without
        re-storing the (assumed equal) data.
        """
        if id:
            real_id = id
        else:    
            real_id = self._hash(data)
        return real_id    
        
    def retrieve(self, id):
        """Retrieve data stored with the given identifier. 

        If the identifier is unknown, a NotFoundError is thrown.
        """
        pass

    def remove(self, id):
        """Remove data stored with the given identifier.

        Removal is not guaranteed and could be delayed.
        If the identifier is unknown, a NotFoundError is thrown.
        """
        pass
    
    def exists(self, id):
        """Check if data with identifier is in store.

        Return True if identifier exists in store, otherwise False. 
        
        Note that this is not thread-safe, as by the time the caller
        check the result of the exists() call, another thread, process
        or server might have added or removed that identifier.
        """
        pass 


class BlockStore(Store):
    """A directory/file based backend that stores data as files.

    The filenames are derived from the identifier. 
    """

    METAFILE="distfs.meta"
    HEADER="distfs blockstore v0.2"

    def __init__(self, directory):
        self.directory = directory
        self.meta = os.path.join(self.directory, self.METAFILE)
        if not os.path.isdir(directory):
            os.makedirs(directory)
        # If it is an empty directory, we have to create
        # the meta file. If it is non-empty, the meta file
        # must already exist later on.
        if not os.listdir(directory):
            meta = open(self.meta, "wb")
            meta.write(self.HEADER + "\n")
            meta.close()
        if not os.path.isfile(self.meta):
            raise NotAFilestore, directory   
        header = open(self.meta).readline()    
        if not header.startswith(self.HEADER):
            raise FilestoreUnknownVersion, header
    
    def _id_dir(self, id):
        dir = os.path.join(self.directory, id[:2])
        if not os.path.exists(dir):
            os.makedirs(dir)
        return dir    
   
    def _hash(self, data):
        return sha(data).hexdigest()
    
    def exists(self, id):
        dir = self._id_dir(id)
        path = os.path.join(dir, id)    
        return os.path.isfile(path)
            
    def store(self, data, id=None):
        real_id = super(BlockStore, self).store(data, id)

        dir = self._id_dir(real_id)
        path = os.path.join(dir, real_id)    
        if os.path.exists(path):     
            if id:
                # Can't assume anything for explicit IDs
                raise AlreadyExistsError, id
            try:    
                fsize = os.stat(path).st_size
            except OSError, e:
                if e.errno == 2:
                    # Oh no, it was deleted! Store it then.
                    pass    
                else:
                    #unexpected
                    raise e
            else:        
                assert fsize == len(data)
                return real_id
                    
        # Can't use NamedTemporaryFile because it deletes when finished!
        (temp_fd, temp_name) = tempfile.mkstemp(dir=dir, 
                        prefix=real_id+"-", suffix=".tmp")
        temp = os.fdopen(temp_fd, "wb")
        temp.write(data)
        temp.flush() 
        temp.close() 
        try:
            # Can't do link, as Windows only support rename
            os.rename(temp_name, path)
        except OSError, e:
            raise e 
        return real_id      

    def retrieve(self, id):
        dir = self._id_dir(id) 
        path = os.path.join(dir, id)    
        try:
            file = open(path, "rb")
        except IOError, e:
            if e.errno == 2:
                # notfound
                raise NotFoundError, id
            raise FileIOError(e, id)
        return file.read()
    
    def remove(self, id):
        dir = self._id_dir(id)
        path = os.path.join(dir, id)
        try:
            os.remove(path)
        except OSError, e:
            if e.errno == 2:
                # notfound
                raise NotFoundError, id
            raise FileIOError(e, id)


class LargeStore(Store):
    """Storage of large data by splitting it into smaller blocks. 

    Parameter 'backend' is the backend store for the large data, for
    example an BlockStore instance.

    If parameter 'blocksize' is given, that is the maximum blocksize in
    bytes that will be used when storing to the backend. Otherwise, the
    default is given by class attribute BLOCKSIZE.
    """

    BLOCKSIZE=65536
    HEADER="distfs largestore v0.1"
    NEXT=" next "
    SINGLE=" single"

    def __init__(self, backend=None, blocksize=None):
        self.backend = backend
        self.blocksize = blocksize or self.BLOCKSIZE
    
    def _store_blocks(self, data):
        """Store data by block sizes, yield identifiers.
        """ 
        pos = 0
        while pos < len(data):
            block = data[pos : pos+self.blocksize] 
            pos += self.blocksize
            yield self.backend.store(block)
                         
    def store(self, data, id=None):
        # This is our master identifier. We are not going
        # to hash these large datas
        id = id or uuid.uuid_str()

        # HEADER + "\n"
        MAX_SIZE_LAST = self.blocksize - len(self.HEADER) - 1
        # HEADER + " single" + "\n"
        MAX_SIZE_SINGLE = MAX_SIZE_LAST - len(self.SINGLE)
        # HEADER + " next " + uuid + "\n"
        MAX_SIZE = MAX_SIZE_LAST - len(self.NEXT) - UUID_SIZE 

        # Special case, if the data fits in a single block, 
        # we'll pop it in there.
        if len(data) <= MAX_SIZE_SINGLE:
            block = "%s%s\n%s" % (self.HEADER, self.SINGLE, data)
            return self.backend.store(block, id)
            
         
        # Store the block list, we'll have to make sure the
        # block list itself is also split by blocksize
        block = ""
        block_id = id
        for next_id in self._store_blocks(data):
            if len(next_id)+len(block) > MAX_SIZE:
                # We can't include it, we have to store now
                next_block = uuid.uuid_str()
                # Note, block already starts with \n
                block = "%s%s%s%s" % (self.HEADER, self.NEXT, next_block, block)
                assert len(block) <= self.blocksize
                self.backend.store(block, block_id)     
                block = ""
                block_id = next_block
            block += "\n" + next_id
        
        if block:
            block = "%s%s" % (self.HEADER, block)              
            self.backend.store(block, block_id)

        # Return the master identifier
        return id      
    
    def retrieve(self, id):
        block = self.backend.retrieve(id)    
        if not block.startswith(self.HEADER):
            raise FilestoreUnknownVersion, repr(block[:len(HEADER)])
        header, rest = block.split("\n", 1)
        if self.SINGLE in header:
            return rest
        result = ""
        blocks = rest.split("\n")
        for block in blocks:
            result += self.backend.retrieve(block)
        
        if not self.NEXT in header:
            return result

        next_block = header.split(self.NEXT, 1)[1]
        return result + self.retrieve(next_block)
    
    def _metablocks(self, id):
        """Retrieve all the blocks containing identifiers to data
        blocks for given id, excluding the given identifier.
        """
        block = self.backend.retrieve(id)
        if not block.startswith(self.HEADER):
            raise FilestoreUnknownVersion, repr(block[:len(HEADER)])
        while id:
            header, rest = block.split("\n", 1)
            if self.SINGLE in header:
                return
            if not self.NEXT in header:
                return
            id = header.split(self.NEXT, 1)[1]
            block = self.backend.retrieve(id)
            if not block.startswith(self.HEADER):
                raise FilestoreUnknownVersion, repr(block[:len(HEADER)])
            yield id

    
    def _blocks(self, id):
        """Retrieve all the blocks containing data for given id.

        Return a generator of identifiers.
        """              
        block = self.backend.retrieve(id)
        if not block.startswith(self.HEADER):
            raise FilestoreUnknownVersion, repr(block[:len(HEADER)])

        header, rest = block.split("\n", 1)

        if self.SINGLE in header:
            return

        blocks = rest.split("\n")
        for block in blocks:
            yield block
         
        if not self.NEXT in header:
            return

        next_block = header.split(self.NEXT, 1)[1]
        for block in self._blocks(next_block):
            yield block

    
    def exists(self, id):
        # Naive, should check if all parts of the data exists
        return self.backend.exists(id)          
    
    def remove(self, id):
        for block in self._blocks(id):
            try:
                self.backend.remove(block)
            except NotFoundError:
                # Several blocks could have same hash
                pass    
        for block in self._metablocks(id):
            self.backend.remove(block)
        self.backend.remove(id)

