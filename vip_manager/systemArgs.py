# -*- coding: iso8859-1 -*-

# 
# Copyright (c) 2002-2004 Stian Søiland
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
# Author: Stian Søiland <stian@soiland.no>
#
# License: MIT
#

import popen2,os

class ErrorcodeException(Exception):
    pass

def systemArgs(*args, **kwargs):
    """Executes a program, returns STDOUT as a string.

    Calls the program given as the first parameter with the
    rest of the parameters as arguments. Wait until the program
    is done, and then return a string containg the program's
    output.

    If the program path given is not absolute or relative
    (ie. 'ls' instead of './ls' or '/bin/ls'), the
    environmental PATH will be searched.

    Keyword parameters:

      joinStdErr -- if true, both STDOUT and STDERR-output will
         be joined together in result. 

      returnTuple -- if true, the return value of this function will
        be a tuple (errorcode, stdout, stderr), ie. two strings.
        Note: If joinStdErr is true, stderr in return will be None.
       
        if returnTuple is false, an exception is raised if the
        command failed (ie. returned a positive errorcode)    

      Note that all of these MUST be given as keyword arguments 
      if used, to seperate them from command arguments.

    If neither returnTuple or joinStdErr are set, STDERR is just
    passed on to the normal stderr.


    Usage:

      myDate = systemArgs('date')
      systemArgs('touch', '/tmp/filename with spaces') # ignore result
      (errorcode, result, errors) = systemArgs('/bin/ls',
                                               unthrusted_variable,
                                               '/tmp', returnTuple=1)    

      The first argument is the program you want to call. This is
      used as with os.execvp. The total argument list will be used as
      args for os.execvp, ie. you don't need to worry about arg[0].

    This function is much safer than os.system(), as you don't have
    to worry about escaping bad characters in the arguments.
    This is highly usefull when building commands from unsafe
    variables (ie. from the web).

    Example of bad os.system-calls:

      filename = '/dev/null ; cat /etc/passwd'
      os.system("/bin/cp /tmp/pupp " + filename)
                  # Will run the command after ;

      use instead:
      systemArgs('/bin/cp', '/tmp/pupp', filename)


      filename = 'Kari er kul'
      os.system("touch " + filename)
      # Will touch the files 'Kari', 'er' and 'kul'

      use instead:
      systemArgs('touch', filename)

    Other examples might include characters like |, $, ``, \, !

    None of these problem would exist with systemArgs.

    Note: This function does not in any way secure the
    variables to avoid 'dangerous' paths. If you allow a
    free filename to be added, and with the given rights,
    /etc/passwd and simular could still be available
    for malicious users."""

    joinStdErr = kwargs.get("joinStdErr")
    returnTuple = kwargs.get("returnTuple")
    raiseException = kwargs.get("raiseException")

    if(joinStdErr):
        process = popen2.Popen4(args)
        error = None # We lose this one from returnTuple
    else:
        # only capture stderr if returnTuple 
        capturestderr = returnTuple
        process = popen2.Popen3(args, capturestderr)
    errorcode = process.wait()
    result = process.fromchild.read()
    error = result
    if(returnTuple and not joinStdErr):
        error = process.childerr.read()
    if(returnTuple):
        return (errorcode, result, error)
    else:
        if errorcode:
            raise ErrorcodeException, (errorcode, error)
        return result

