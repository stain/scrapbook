##
# Base class for messages
# (c) Stian Soiland 2000 <stain@nvg.org>
#
# Distributed under GNU Public Licence (GPL).
#
# Last changes:
# $Log: message.py,v $
# Revision 1.4  2001/10/21 00:35:03  stain
# Lots of new things
#
# Revision 1.4  2001/10/03 14:05:45  stain
# Flyttet til CVSROOT/lfc/python/ (Linpro Foundation classes)
#
# Revision 1.3  2000/11/22 22:10:10  stain
# Aner ikke
#
# Revision 1.2  2000/10/26 17:06:23  stain
# Støtte for melding.copy() og sånt. Gøy. (Kaller bare tilsvarende
# metoder i foldern)
#
# Revision 1.1  2000/10/23 23:32:45  stain
# Dagens endringer.
#
# Revision 1.1  2000/10/11 01:44:15  stain
# Blaha
#
#
##

import UserDict

class Message():
    def __init__(self, parent=None, source=None, size=None):
        self._parent = parent # Folder the message belongs to
        self._source = source # identifier in folder
		self.size = size
		self._headers = {}
		self._data = None
        self._status = []
    def read(self):
		"""Returns a rfc822.Message-object"""
        return rfc822.Message(self.open())
    def open(self):
        """Return file (possibly file-like) object
		containing the message with headers"""
        pass
    def isSaved(self):
		"""Does this message belong in a folder, or is
		it simply blowing in the wind?"""
        if(self._parent and self._source):
            return 1
        else:
            return 0
    def delete(self):
		"""Remove this message"""
		if(isSaved()):
			self._parent.delete(self)
		else:
			raise 
    def move(self, folder):
		"""Move the message to this folder,
		possibly faster than copy and delete"""
		if(isSaved()):
			self._parent.move(self, folder)
		else:
			self.copy(folder)
    def copy(self, folder):
        folder.save(self)



