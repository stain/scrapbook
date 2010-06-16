#!/usr/bin/env python
# -*- coding: iso8859-1 -*-

# 
# Copyright (c) 2004-2006 Stian Søiland, Magnus Nordseth
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
# Authors: Stian Soiland <stian@soiland.no>
#          Magnus Nordseth <magnus@nordseth.net>
#          Lasse Karstensen <lkarsten@samfundet.no>
#
# License: MIT
#

"""Manages VIP interfaces according to keepalived.conf.
Parses keepalived.conf to find active VIP (virtual_server) addresses
that should be active for a real_server (RIP).

Activates current VIPs on dummy interface, and disactivates
no longer active IPs.

See http://soiland.no/software/vip_manager/ or README.txt for
documentation.

USAGE: vip_manager.py [-d] [real_ip]
    -d       Show debug messages
    real_ip  Manually set real_server IP
             (default: resolve from hostname)
"""

__version__ = "0.2.2006-04-10"

(True, False) = (1==1, 0==1)

# Revision history
# ================
#
# 0.1-2004-05-04
#    First release
#
# 0.2-2006-04-10
#    Added support for Linux 2.6 by Lasse Karstensen
#    Default keepalived.conf path is now /etc/keepalived/keepalived.conf


import re
import socket
import sys
import os
from sets import Set
from systemArgs import systemArgs, ErrorcodeException

# Which dummy device to add/remove IP addresses to
DUMMY="dummy0"
# Our keepalived-conf ready for parsing
CONF="/etc/keepalived/keepalived.conf"
# Whether to print debug
DEBUG = False
# Our own IP to match for as real_server
REAL_IP = None


class VipManagerException(Exception):
    pass

def _message(args):
    """Stringify a list of arguments, join with space"""
    args = [str(arg) for arg in args]
    return " ".join(args)

def _debug(*args):
    if not DEBUG:
        return    
    """Prints debug"""
    print _message(args)
    

def _warning(*args):
    """Prints warning"""
    print >>sys.stderr, _message(args)
    

def _error(errorcode, *args):
    """Prints error exits with errorcode"""
    if __name__ == "__main__":
        # Only abort if we're run as a program
        _warning(*args)
        _warning("Aborting.")
        sys.exit(errorcode)
    else:
        raise VipManagerException, (errorcode, _message(args))


def get_all_servers(conf=None):
    """Reads keepalived.conf and finds defined virtual_servers and their
       matching real_servers. 
       Returns a dictionary, the keys are virtual_server IPs, and
       the values are sets of 0 or more real_server IPs.
    """   
    conf = conf or CONF
    try:
        config = open(conf)
    except IOError, e:
        _error(4, "Could not read config file", conf, e)
    virtualservers = {}
    realservers = None
    line_nr = 0
    for line in config.readlines():
        line_nr += 1
        vmatch = re.search(r"^\s*virtual_server\s+([\d.]+)", line)
        if vmatch:
            vserver = vmatch.group(1)
            # Add new list to virtualservers  if non-existing
            realservers = virtualservers.setdefault(vserver, Set())
        rmatch = re.search(r"^\s*real_server\s+([\d.]+)", line)            
        if rmatch:
            rserver = rmatch.group(1)
            if realservers is None:
                _error(1, "Parse error: found real_server", rserver, "for",
                      "unknown virtual_server on line", line_nr)
            realservers.add(rserver)
    sanity_check(virtualservers)            
    return virtualservers                


def sanity_check(virtualservers):
    """Make sure the virtualservers list seems reasonable"""
    if not virtualservers:
        _error(2, "No virtual servers defined, probably misconfiguration")
    # Check if any of the virtual servers actually has a real_server    
    any_real = [realservers for realservers in 
                     virtualservers.values() if realservers]
    if not any_real:
        _error(3, "No real servers defined, probably misconfiguration")


def get_my_virtualservers(real_ip=None, conf=None):
    """Gets a list over VIP addresses served by real_ip.
    If real_ip is not supplied, current hostname is used
    to resolve it.
    conf may specify the path to keepalived.conf. 
    """
    virtualservers = get_all_servers(conf)
    # get my real address 
    my_real = real_ip or REAL_IP
    if not my_real:
        try:
            my_real = socket.gethostbyname(socket.getfqdn())
        except socket.error, e:
            _error(5, "Could not resolve real_server IP", e)    
    if not my_real[:1].isdigit():
        # this might happen with /store/bin/python (!) 
        # (gethostbyname simply returns the same name) 
        _error(6, "Invalid IP, got", my_real)
    
    my_servers = [vserv for (vserv, realservers) in virtualservers.items()
                  if my_real in realservers]
    # my_servers.sort()                  
    return Set(my_servers)


def get_current_interfaces(dummy=None):
    """Retrieves current IPs active for given/default dummy interface"""
    dummy = dummy or DUMMY
    try:
        ip_output = systemArgs('ip', 'addr') 
    except ErrorcodeException, e:
        _error(7, "Could not run 'ip addr', error", *e)
    interfaces = Set()
    for line in ip_output.split("\n"):
        inetmatch = re.search(r"^\s+inet ([\d.]+)/32.*%s$" % dummy, line)
        if inetmatch:
            interfaces.add(inetmatch.group(1))
    return interfaces          

def update_interfaces(dummy=None, real_ip=None, conf=None):
    """Removes inactive IPs and adds new IPs to dummy interface"""
    dummy = dummy or DUMMY
    should_have = get_my_virtualservers(real_ip=real_ip, conf=conf)
    has_already = get_current_interfaces(dummy)
    # must_delete = filter(lambda x:x not in should_have, has_already)
    # must_delete = [ip for ip in has_already if ip not in should_have]
    # Using sets is a lot more sexy.... :)
    must_delete = has_already - should_have
    must_add = should_have - has_already
    _debug("Deleting", must_delete)
    for ip in must_delete:
        try:
            systemArgs('ip', 'addr', 'del', ip, 'dev', dummy)
        except ErrorcodeException, e:
            # The error code if 'ip addr del' says 
            # "RTNETLINK answers: Cannot assign requested address"
            if e[0] == 2: 
                _warning("Ignoring already removed ip", ip)
            else:    
                _error(10, "Could not remove", ip)
    _debug("Adding", must_add)
    for ip in must_add:
        try:
            systemArgs('ip', 'addr', 'add', ip, 'dev', dummy)
        except ErrorcodeException, e:
            # The error code if 'ip addr add' says 
            # "RTNETLINK answers: File exists"
            if e[0] == 2: 
                _warning("Ignoring already added ip", ip)
            else:    
                _error(11, "Could not add", ip)
    if should_have:            
        # make interface hidden if we have any active IPs 
        # (if no IPv4-addresses are on interface, hide_interface()
        # won't work) 
        hide_interface(dummy)

def activate_interface(dummy=None):
    """Turns the dummy interface 'up'"""
    dummy = dummy or DUMMY
    try:    
        systemArgs('ifconfig', dummy, 'up')
    except ErrorcodeException, e:
        _error(9, "Could not activate interface", dummy, *e)

def hide_interface(dummy=None): 
    """Makes the dummy interface 'hidden' to avoid ARP responses and
       related problems."""
    dummy = dummy or DUMMY
    try:
        if os.uname()[2].startswith('2.4'):
            open("/proc/sys/net/ipv4/conf/%s/hidden" % dummy, "w").write("1\n")
            # This global setting is also needed
            open("/proc/sys/net/ipv4/conf/all/hidden", "w").write("1\n")
        else:
            # Assume 2.6 or later
            # Linux 2.6 does things slightly more verbose
            open("/proc/sys/net/ipv4/conf/%s/arp_announce" % dummy, "w").write("2\n")
            open("/proc/sys/net/ipv4/conf/%s/arp_ignore"   % dummy, "w").write("1\n")
            # This global setting is also needed
            open("/proc/sys/net/ipv4/conf/all/arp_announce", "w").write("2\n")
            open("/proc/sys/net/ipv4/conf/all/arp_ignore"  , "w").write("1\n")
    except IOError, e:
        # Turning off interface since we can't hide it
        try: 
            systemArgs('ifconfig', dummy, 'down')
        except ErrorcodeException: 
            pass
        _error(8, "Could not set interface", dummy, "hidden", *e)   

def main():
    activate_interface()
    update_interfaces()

if __name__ == "__main__":
    # This is dirty, but small code
    args = sys.argv[1:]
    if "-h" in args:
        print __doc__
        sys.exit(0)
    if "-d" in args:
        DEBUG=True
        args.remove("-d")
    if args:
        REAL_IP = args[0]        
    main()
