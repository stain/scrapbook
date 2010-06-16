BUFFERSIZE = 8192
SEPERATOR = '\nFrom '

# Constants for sourceStatus
NOT_OPEN = 0
OPEN_READ = 1
OPEN_WRITE = 2

import string,os,fcntl,stat
import lockfile,message,errors,folder
from errors import *

class ReadLockError(SourceReadingError):
	"Can't lock for reading (shared lock)"

class WriteLockError(SourceReadingError):
	"Can't lock for writing (exclusive lock)"

class Message(message.Message):
	def open(self):
		self._data = self._parent.getRaw(self._source)
		
class Mbox(folder.MessageFolder):
    def __init__(self,filename=None):
        self.filename = filename        
        self.positions = []
		self.sourceStat = (0,0)
		self.sourceStatus = NOT_OPEN # Not opened
		self.deleted = [] # Initially no changes to box
		self.added = [] # And of course nothing added yet
		self.fd = None
		self.lock = threading.RLock()

	def getSourceStat(self):
		"""Data to use to check for any changes on source file"""
		statdata = os.stat(self.filename)
		size = statdata[stat.ST_SIZE]
		date = statdata[stat.ST_MTIME]
		return (size, date)

	def openRead(self, count=0):		
		"""Opens the mbox for reading. Uses shared fcntl-locking."""
		self.lock.acquire()
		self.close()
		try:
			try:
				self.fd = lockfile.openRead(self.filename)
			except lockfile.LockError:			
				raise ReadLockError
			else:
				self.sourceStat = self.getSourceStat()
				self.sourceStatus = OPEN_READ
		finally:
			self.lock.release()
			
	def openWrite(self, count=0):
		"""Opens the mbox for writing. Uses both exclusive
		fcntl-locking and dot-locking. Remember to sync first."""
		self.lock.acquire()
		self.close()
		try:
			try:
				self.fd = lockfile.openUpdate(self.filename)
			except lockfile.LockError:			
				raise WriteLockError
			else:
				self.sourceStat = self.getSourceStat()
				self.sourceStatus = OPEN_WRITE
		finally:
			self.lock.release()

	def _createSource(self, source):
		if(os.exists(source)):
			raise SourceCreateError, "%s already exists." % source
		tempfile = os.tempnam(os.path.dirname(os.path.abspath(source)),
							  os.path.basename(source))
		open(tempfile,'w') # Create (and.. uhu.. possibly overwrite)
		try:
			try:
				os.link(tempfile, source) # Will fail if exists
			except Exception, exception:
				raise SourceCreateError, exception
		finally:
			os.unlink(tempfile)

	def _save(self, message):
		self.added.append(message)

	def _load(self):
		self.lock.acquire()
		positions = self.readSome()
		self._children = positions
		self.lock.release()

	def _sync(self):
		self.lock.acquire()
		self.deleted.sort()
		self.openWrite()
		tempfile = os.tempnam(os.path.dirname(os.path.abspath(source)),
							  os.path.basename(source))
		temp = open(tempfile,'w') # Create (and.. uhu.. possibly overwrite)
		for deletePosition in self.deleted:
			while(deletePosition > self.fd.tell() + BUFFERSIZE):
				data = self.fd.read(BUFFERSIZE)
				temp.write(data)
			else:
				# This will work even if two concequentlies messages
				# are deleted, read(0) == ''
				# and write('') works nice.
				data = self.fd.read(self.fd.tell() - deletePosition)
				temp.write(data)

			# Skip the deleted message
			index = self._children.index(deletePosition)
			self.fd.search(self._children[index+1])

		temp.write(self.fd.read()) # the rest, if any

		for message in self.added:
			thisPosition = temp.tell() # My new position
			context = message.read()
			(date, sender) = ('', '')
			date = context.getdate('Date')
			if(not date):
				date = time.gmtime()
			date = time.strftime("%a %m %d %H:%M:%S %Y", date)
			sender = context.getaddr('From')[1]
			if(not sender):
				sender = 'unknown@localhost'
			fromline = SEPERATOR + sender + ' ' + date + '\n'
			temp.write(fromline)
			rfcMessage = message.read()
			for line in rfcMessage.headers:
				temp.write(line)
			temp.write("\n") # Here comes the body
			temp.write(rfcMessage.fp.read())
			self._children.append(thisPosition)
			self.added.delete(message)

		self.lock.release()

	def close(self):		
		"""Closes the mbox-file, removes any locking.
		Please use sync first to check for changes!!"""
		self.lock.acquire()
		try:
			if(self.modified or
			   self.sourceStat <> self.getSourceStat()):
				raise FolderNotSyncedError

			self.fd.flush()
			self.fd.close()		
			try:
				fcntl.lockf(self.fd.fileno(), fcntl.LOCK_UN)
				if(self.sourceStatus == OPEN_WRITE):
					unlink(self.filename + '.lock') # remove any possibly dot lock
			except:
				pass # Don't care!
			self.sourceStatus = NOT_OPEN
			self.fd = None
		finally:
			self.lock.release()

    def readSome(self):
		"""Index the mailbox by reading BUFFERSIZE bytes at a time"""

		# This is a bit dirtyer code, and might be
		# slower on small mailboxes. However, this method
		# does not read everything into RAM at once.

		self.openRead()
		self.lock.acquire() # We don't want anyone else to read me
		try:
			self.fd.seek(0)
			positions = [0] # We won't find the first one. This is a hack.

			buffer1 = ''
			buffer1Start = 0 # In what position in the file does
			                   # buffer_1 begin?
		    offset = 0         # How far in the buffer have we searched?
			while(1):
				found = string.find(buffer_1,SEPERATOR,offset)
				if(found==-1):
					rest = buffer1[-(len(SEPERATOR)-1):]
					# ie. if the end of the buffer_1 might be some
					# part of "\nFrom ", we save it and find it next time

					buffer1Start = len(buffer_1) - len(rest) + buffer1Start
					buffer1 = rest + self.fd.read(BUFFERSIZE)
					if(len(buffer1) == len(rest)):
						break         # End of file
					offset = 0
				else:
					positions.append(found+buffer1Start+1)
					# The trailing \n is not needed, so we +1
					offset = found + len(SEPERATOR)
		finally:
			self.lock.release() # We're thru with file stuff
        return positions

    def readAll(self):
		"""Read the whole mailbox to RAM before indexing"""
		self.lock.acquire()
		try:
			self.fd.seek(0)
			data = self.fd.read()
		finally:
			self.fd.release() # That's all file stuff
        result = 0
        positions = []
        offset = 0
        while(result>-1):
            positions.append(result+1)
            result = data.find(SEPERATOR,offset)
            offset = result + len(SEPERATOR)
        return positions

    def getRaw(self,number):
		self.lock.acquire()
		try:
			self.fd.seek(self.positions[number])
			try:
				till = self.positions[number+1] - self.positions[number]
			except IndexError:
				till = -1
				return self.fd.read(till)[:-1] # Strip the final \n
		finally:
			self.lock.release()

	def _getMessage(self, messageId):
		next = self._children.index[messageId] + 1
		try:
			# The difference between positions is this message's
			# total size (including «From ..»-line)
			size = self._children[next] - messageId
		except IndexError:
			# last message, calculate from max file size
			size = self.sourceStat[0] - messageId
			
		message = Message(self, messageId, size=size)
		return message
