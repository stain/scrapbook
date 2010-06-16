#!/bin/sh

# Copyright (c) 2006 Stian Soiland
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
# URL: http://soiland.no/i/src/
# License: MIT
#

# Re-export typical variables to screen for reattaching with a new
# ssh/X11 session. This will make things like SSH auth agent forwarding,
# X11 programs etc. work in all *new* screen windows within an existing
# screen.



#export AUDIODEV=`utaudio`
for var in AUDIODEV PATH SSH_AGENT_PID SSH_AUTH_SOCK SSH_TTY DISPLAY; do
  screen -x $1 -X unsetenv $var
  screen -x $1 -X setenv $var "${!var}"
done
screen -x $1 -X chdir
