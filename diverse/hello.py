#!/usr/bin/env python
"""A somewhat non-trivial hello world program
   
   (c) Stian Soiland <stain@nvg.org> 2002-03-05

   Licensed under GPL. See the file "LICENSE" for details.

   Last changes:
   $Log$
"""

import random,types,sys,os,getopt


VERSION="0.4"
COPYRIGHT="Stian Soiland <stain@nvg.org> 2002-03-05"
PROGRAM=""
try:
  PROGRAM=os.path.basename(sys.argv[0])
except:
  pass
if(PROGRAM==""):
  PROGRAM="hello"

class Word:
  """Class representing a word"""
  def __init__(self, word=''):
    """Initiates the word with the given value."""
    self.word=word
  def rotate(self):
    """Rotates the word. Ie. 'Per' is translated to 'reP'"""
    a = list(self.word) # Convert to list
    a.reverse() # flip flap!
    self.word = ''.join(a) # Who said you can't write ugly Python code?
  def randomCase(self):
    newWord = ''
    for character in self.word:
      newWord += random.choice((character.lower(), character.upper()))
    self.word = newWord
  def output(self):
    print self.word,

def help():
  print """Extended Hello World v.%s (c) %s

Greets the user with a friendly hello message.

Usage: %s [OPTIONS] [MESSAGE]
  -h   --help          Displays this help message
  -r   --reverse       Reverse the ordering of the words
  -R   --rotate        Rotate the words
  -c   --random-case   Randomize the casing
""" % (VERSION, COPYRIGHT, PROGRAM)

def main():
  try:
    (opts, args) = getopt.getopt(sys.argv[1:], 
                               "hrRc",
                               ["help", "reverse", 
                                "rotate", "random-case"])
  except getopt.GetoptError:
    help()
    sys.exit(2)

  
  words = []
  if(args):
    for word in args:
      words.append(Word(word))
  else:
    # Present the default message
    words.append(Word('Hello'))
    words.append(Word('World'))


  for (option, argument) in opts:
    if(option=='-h' or option == '--help'):
      help()
      sys.exit()
    elif(option=='-r' or option=='--reverse'):
      words.reverse()
    elif(option=='-R' or option=='--rotate'):
      for word in words:
        word.rotate()
    elif(option=='-c' or option=='--random-case'):
      for word in words:
        word.randomCase()

  for word in words:
    word.output()
  print "\n",

if(__name__ == "__main__"):
  main()

