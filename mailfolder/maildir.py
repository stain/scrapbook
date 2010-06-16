"""Handling maildirs. Maildirs are a more reliable way to store
e-mails than mbox. See http://www.qmail.org/, maildir(5)
and http://pobox.com/~djb/proto/maildir.html
for more information."""

##
# Maildir support
# (c) Stian Soiland 2000 <stain@nvg.org>
#
# Distributed under GNU Public Licence (GPL).
#
# Last changes:
# $Log: maildir.py,v $
# Revision 1.5  2001/10/21 00:35:03  stain
# Lots of new things
#
# Revision 1.5  2001/10/03 14:05:45  stain
# Flyttet til CVSROOT/lfc/python/ (Linpro Foundation classes)
#
# Revision 1.4  2001/05/04 18:57:37  stain
# A little bit closer to a working mbox
#
# Revision 1.3  2000/11/22 22:10:10  stain
# Aner ikke
#
# Revision 1.2  2000/11/08 01:37:53  stain
# Maildir-støtte
#
# Revision 1.1  2000/10/11 01:44:15  stain
# Blaha
#
#
##

import folder,rfc822,os,message

from errors import *

class Message(message.Message): 
    def open(self): 
        return open(os.path.join(self._parent._source, self._source))

def isMaildir(pathname): 
    if(not os.path.isdir(pathname)):
		return 0
	for elem in ('cur','new','tmp'):
		if(not os.path.isdir(os.path.join(pathname,elem))):
			return 0
		# A maildir containing messages must have all these
		# three directories.
	return 1

class SubFolder(folder.SubFolder): 
    def _checkSource(self, source): 
        return os.path.isdir(source)
    def _load(self): 
        try:
            self._children = []
            for test in os.listdir(self._source):
                if(os.path.isdir(test)):
                    self._children.append(test)
        except:
            raise SourceReadingError
    def _getFolder(self, foldername): 
        pathname = os.path.join(self._source, foldername)
		if(isMaildir(pathname)):
			return MessageFolder(pathname)
		else:
			return SubFolder(pathname)
    def _createSource(self, foldername): 
        try:
            os.mkdir(foldername)
        except:
            raise SourceWritingError

class MessageFolder(folder.MessageFolder): 
    def _checkSource(self, source): 
        pathname = os.path.join(self._source, source)
        return isMaildir(pathname)
    def _load(self): 
        try:
            self._children = []
            for subdir in ('cur','new'):
                for elem in os.listdir(path):
					if(elem[0] <> '.'): # Ignore hidden files
						messageID = os.path.join(subdir, elem)
						if(os.path.isfile(os.path.join(self._source,
													   messageID))):
                            self._children.append(messageID)
        except Exception, exception:
            raise SourceReadingError, exception
    def _createSource(self, foldername): 
        try:
            os.mkdir(foldername)
            for elem in ('cur','new','tmp'):
                os.mkdir(os.path.join(foldername,elem))
        except:
            raise SourceWritingError
    def _getMessage(self, messageId): 
        message = Message(self, messageId)
		os.path.join(self._source, messageId)
        return message

	def _save(self, message):
		
