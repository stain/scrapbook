##
# Errors for mailfolders
# (c) Stian Soiland 2000 <stain@nvg.org>
#
# Distributed under GNU Public Licence (GPL).
#
# Last changes:
# $Log: errors.py,v $
# Revision 1.3  2001/10/21 00:35:03  stain
# Lots of new things
#
# Revision 1.3  2001/10/03 14:05:45  stain
# Flyttet til CVSROOT/lfc/python/ (Linpro Foundation classes)
#
# Revision 1.2  2001/05/02 13:41:06  stain
# nå mye tøffere.
#
# Revision 1.1  2000/11/08 01:37:22  stain
# Error classes
#
#
##

class FolderError(exceptions.Exception):
    "General folder error"
    def __str__(self):
        args = exceptions.Exception.__str__(self) # Get our arguments
        return self.__doc__ + ': ' + args

class SourceNotSetError(FolderError):
    "No source set! Use set_source()"
class SourceAlreadySetError(FolderError):
    "You can't set the source twice!"

class SourceError(FolderError):
    "General source error"
class SourceNotFoundError(SourceError):
    "Source not found"
class SourceCreateError(SourceError):
    "Error creating source"
class SourceWritingError(SourceError):
    "Error writing to source"
class SourceReadingError(SourceError):
    "Error reading from source"

class FolderNotSyncedError(FolderError):
    "Folder not synced with source"
class FolderNotFoundError(FolderError):
    "Folder not found"

class MessageNotFoundError(FolderError):
    "Message not found"



