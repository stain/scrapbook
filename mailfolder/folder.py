##
# Base classes for mail folders
# (c) Stian Soiland 2000 <stain@nvg.org>
#
# Distributed under GNU Public Licence (GPL).
#
# Last changes:
# $Log: folder.py,v $
# Revision 1.8  2001/10/21 00:35:03  stain
# Lots of new things
#
# Revision 1.8  2001/10/03 14:05:45  stain
# Flyttet til CVSROOT/lfc/python/ (Linpro Foundation classes)
#
# Revision 1.7  2001/05/02 13:41:06  stain
# nå mye tøffere.
#
# Revision 1.6  2001/04/30 10:20:11  stain
# *** empty log message ***
#
# Revision 1.5  2000/11/22 22:10:10  stain
# Aner ikke
#
# Revision 1.4  2000/11/08 01:37:10  stain
# Error classes moved to errors.py
#
# Revision 1.3  2000/10/26 17:06:23  stain
# Støtte for melding.copy() og sånt. Gøy. (Kaller bare tilsvarende
# metoder i foldern)
#
# Revision 1.2  2000/10/23 23:32:45  stain
# Dagens endringer.
#
# Revision 1.1  2000/10/11 01:44:15  stain
# Blaha
#
#
##


import rfc822,errors

from errors import *

class Folder: 
    """Base class for folders"""

    def __init__(self, source=None): 
	# Note: set_source() or create() must be called if source not given
        self._source = None
        self._modified = None
        if(source):
            # Even creates the source if it does not exist.
            # If this is not what you want, use set_source()
            try:
                self.setSource(source)
            except SourceCreateError:
                self.createSource(source)

    def setSource(self, source): 
        if(self._source<>None):
            raise SourceAlreadySetError
        if(_check_source(source)):
            self._source = source
            self._modified = 0 # We don't need to sync first time :)
            self._load()
        else:
            raise SourceNotFoundError
    def _checkSource(self, source): 
        """Implementation of source checking"""
        ## Check if source exists
        return 1

    def createSource(self, source): 
        if(self._source<>None):
            raise SourceAlreadySetError
        self._createSource(self, source) # Call implementation
        self.setSource(source)

    def _createSource(self, source): 
        """Implementation of source creation"""
        ## Make source on media
        ## Might raise SourceCreateError
        pass

    def getSource(self): 
        if(self._source <> None):
            return self._source
        else:
            raise SourceNotSetError

    def check(self): 
        """Checks that the object is OK :=)"""
        self.getSource()

    def load(self): 
        self.check()
        if(self._modified):
            raise FolderNotSyncedError
        source = self.get_source()
        self._load()

    def _load(self): 
        """Implementation of load"""
        ## open source and read
        self._children = []
        pass

    def sync(self): 
        self.check()
        self._sync()
        self._modified = 0
        self._load()

    def _sync(self): 
        """Implementation of sync"""
        ## Save to source. Remember to check for any changes first
        ## in stupid formats like mbox
        pass

class SubFolder(Folder): 
    """Base class for folders containing folders"""

    def getFolder(self, foldername): 
        self.check()
        if(foldername in self._children):
            return self._get_folder(foldername)
        else:
            raise FolderNotFoundError, foldername
    def _getFolder(self, foldername): 
        """Implement getFolder"""
        ## Check whether subfolder is a SubFolder or MessageFolder
        ## and return such an instance
        return MessageFolder('full source specification')

    def folderList(self): 
        self.check()
        return self._children


class MessageFolder(Folder): 
    """Base class for folders containing messages"""

    def messageList(self): 
        self.check()
        return self._children

    def getMessage(self, messageId): 
		"""Get the message with the given id"""
        self.check()
        if(messageId in self._children):
            return self._getMessage(message)
		else:
			raise MessageNotFoundError, messageId

    def _getMessage(self, messageId): 
        """Implementation of getMessage"""
        pass

    def delete(self, message): 
		"""Delete this message"""
        self.check()
        self._delete(message)
        self._children.remove(message)

    def _delete(self, message): 
        """Implementation of delete"""
        # might postpone actuall deletion, set
        # self._modified=1 and delete in self._sync()
        # May raise SourceErrors
        pass

    def save(self, message): 
        self.check()
        if(message._parent.__class__ == self.__class__):
            self._save(message)
            self._children.append(message)
        else:
            # It's a folder of another type than our self,
            # we need to export it
            pass

    def _save(self, message): 
        """Implementation of save"""
        # might postpone actuall saving, set
        # self._modified=1 and save in self._sync()
        # May raise SourceErrors
        pass

    def move(self, message, folder): 
        self.check()
        if(hasattr(self, '_move') and
          (self.__class__ == message._parent.__class__)):
            self._move(message, folder) # it's one of us
        else:
            folder.save(message) # We need to export it and such
            self.delete(message)

    ## def _move(self, message, folder): 
    ##     # _move() may implement a quicker way to move than move()
    ##     # might postpone actuall saving, set
    ##     # self._modified=1 and save in self._sync()
    ##     # May raise SourceErrors
    ##     pass


