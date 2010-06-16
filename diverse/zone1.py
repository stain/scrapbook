#!/usr/bin/env python2.4

import sys
import os
# Rest of imports delayed until after --daemon

# URL that should not redirect somewhere else.
TEST_URL="http://soiland.no/"

# FORM POST to log in
LOGIN_URL="https://zone1.cwg.its.manchester.ac.uk/login.cgi"
# String that should be in login result if successfull
LOGIN_RESULT="Access Granted"

# To log out
LOGOUT_URL="https://zone1.cwg.its.manchester.ac.uk/logout.cgi"

# device in ifconfig -a that is wireless network
WLAN_DEV="en1"
# grep for this network
WLAN_NET="130.88"

def login():
    """Log in"""
    pwline = open(os.path.join(os.environ["HOME"], ".zone1-auth")).readline()
    username, password = pwline.split()
    result = urllib2.urlopen(LOGIN_URL, 
        urllib.urlencode(dict(username=username, 
                              password=password,
                              # Acceptable Use Policy checkbox
                              aup="yes")))
    return LOGIN_RESULT in result.read()

def logout():
    """Log out"""    
    urllib2.urlopen(LOGOUT_URL)

def on_wlan():
    """Check if we are on the correct wireless network"""
    cmd = '/sbin/ifconfig %s|grep -q "inet %s"' % (WLAN_DEV, WLAN_NET)
    retcode = subprocess.call(cmd, shell=True)
    return not retcode

def login_required():
    """Check if we need to log in"""
    test_page = urllib2.urlopen(TEST_URL)
    # Did we redirect?
    return not TEST_URL in test_page.url

def main():
    if "--help" in sys.argv or "-h" in sys.argv:
        print """zone1.py [--logout]
Log in to portal protected wlan if needed.

Arguments:
    -h --help    This screen
       --logout  Log out from wlan
       --daemon  Run in background
"""
        sys.exit(3)
        
    if "--logout" in sys.argv:
        if on_wlan():
            logout()
            print "Logged out wlan"
            sys.exit(0)
        else:    
            print "Not on correct wlan"
            sys.exit(2)
    if on_wlan() and login_required():
        if login():
            print "Logged in to wlan"
            sys.exit(0)
        else:
            print >>sys.stderr, "Could not log in to wlan!"    
            sys.exit(1)
    
if __name__ == "__main__":
    if "--daemon" in sys.argv:
        if os.fork():
            os._exit(0)
    
    # Delayed imports
    import urllib
    import urllib2
    import subprocess
    main()

