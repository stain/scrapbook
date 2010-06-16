## http://www.cs.usyd.edu.au/~piers/python/getpass.py

"""
getpass - password aquisition
getuser - login name aquisition
"""


def getpass(prompt = 'Password'):
	""" password = getpass(prompt = 'Password')

		Get a password with echo turned off
		- restore terminal settings at end.
	"""

	import sys

	if not sys.stdin.isatty():
		passwd = sys.stdin.read()
		while len(passwd) > 0 and passwd[-1] in ('\r', '\n'):
			passwd = passwd[:-1]
		return passwd

	import termios
	if not hasattr(termios, 'ECHO'):
		import TERMIOS		# Old module for termios constants
	else:
		TERMIOS = termios	# Now included

	fd = sys.stdin.fileno()
	old = termios.tcgetattr(fd)	# a copy to save
	new = old[:]			# a copy to modify

	new[3] = new[3] & ~TERMIOS.ECHO	# 3 == 'lflags'
	try:
		termios.tcsetattr(fd, TERMIOS.TCSADRAIN, new)
		try: passwd = raw_input(prompt+': ')
		except (KeyboardInterrupt, EOFError): passwd = None
	finally:
		termios.tcsetattr(fd, TERMIOS.TCSADRAIN, old)

	sys.stdout.write('\n')
	sys.stdout.flush()
	return passwd


def getuser():
	""" login = getuser()

		Return invoker's login id.
	"""

	import os

	for name in ('LOGNAME', 'USER', 'LNAME'):
		if os.environ.has_key(name):
			return os.environ[name]

	import pwd

	try:
		return pwd.getpwuid(os.getuid())[0]
	except:
		raise 'Who are you?'
