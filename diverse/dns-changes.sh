#!/bin/bash

# dns-changes
# Copyright (c) 2005-2006 Stian Soiland
# Inspired by serialdiff (c) 2004 Lasse Karstensen
# 
# Checks for changes in DNS zones served by $SERVER.
# Finds subzones recursively as long as $AUTH is
# authorative. Reports changes in a diff-kind of format.
# Intended to be run from a crontab to monitor changes
# done to DNS zones.
#
# USAGE
#   - Edit this file to set parameters SERVER, AUTH, ZONES and VAR
#   - Create the subdirectory as specified by VAR
#   - Run the program for the first time to do the initial
#     dumps. "New zone X" should appear. 
#   - Run the program again. No output should appear although this may 
#     take a while. 
#   - Make a small, non-important DNS change, such as adding a CNAME. 
#   - Run the program again. You should get output such as:
#     > ldap.itea.ntnu.no.    3600    IN      CNAME   at.ntnu.no. 
#   - Set up a mailing list for people who want to receive dns-changes,
#     for instance dnschanges@mycompany.com. Make sure the cron user
#     is allowed to post here.
#   - Set up a crontab as a user who has write-access to VAR:
#     MAILTO=dnschanges@mycompany.com
#     */30 * * * *  $HOME/dns-changes/dns-changes.sh
#   - Do another non-important change and wait for an email 
#     reporting the changes.
# 
# TIPS
# 
# Active Directory zones will constantly be updated with non-important
# data by AD clients. It is therefore usually not interesting to do
# dns-changes to AD zones. To avoid AD zones, set AUTH to your
# non-AD authorative server.
# 
# The VAR directory (var/) will contains copies of all transfered zones,
# including the version from a previous run. If you have forgotten to
# add revision control to your zone repository (such as RCS), you might
# undo a destructive DNS change by picking up the old version
# from var/. Note that these files will not look like your existing zone
# files, since they use a "full" format such as:
# fish.company.no.    3600    IN      CNAME   some.fish.company.no.

# 
# 
# REQUIREMENTS
# 
# dig and diff must be installed and in PATH
# 
# Remember that the server you intend to run dns-changes.sh on must have
# AXFR rights for the domains.  For BIND, this is set up like this
# in named.conf:
#
#     acl "internal" {
#             127.0.0.1;
#             10.0.0.0/24;
#     };
#     zone "0.10.in-addr.arpa" {
#             allow-transfer { internal; };
#             #(..)
#     };


# DNS-server to connect to. Should be the externally used dns server.
SERVER="ludvig.ntnu.no."

# Require this authorative server to be in the SOA record.  Usually this
# is the same as $SERVER, but if you have a hidden master, you can
# override this. If you don't want to limit the recursion to servers
# hosted by $AUTH, set this to ""
AUTH=$SERVER

# Root of zones to check. dns-changes will recurse down by following
# NS records and process subdomains if $AUTH matches the SOA records.
ZONES="ntnu.no. 241.129.in-addr.arpa. 240.10.in-addr.arpa."

# Keep our zone dumps here. The default is a subdirectory
# var/ of the program. You can also set this to for 
# instance /var/lib/dns-changes - remember to create the directory first
VAR=$(dirname $0)/var

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

# Keep our zone dumps here
cd $VAR || exit 1


function check_zone () {
    zone=$1;
#    echo "Checking $zone"
    dig +tcp +noall +answer @$SERVER $zone AXFR > $zone.$$  || {
        echo "ERROR: Could not transfer zone $zone from $SERVER"
        cat $zone.$$
        echo "----"
        return
    }
    cat $zone.$$ | grep -q "SOA.*$AUTH" || {
        # echo "Skipping zone $zone not managed by $AUTH"
        rm $zone.$$
        return
    }
    # Remove SOA so we don't trigger on new serials, and
    # sort it so it is diff-able. (IMPORTANT: LC_ALL=C sort to 
    # avoid different outputs depending on user settings)
    cat $zone.$$ | grep -v 'SOA' | LC_ALL=C sort > $zone.new
    rm $zone.$$
    if [ -f $zone ] ; then
        # grep away stupid 29d84 output
        diff $zone $zone.new | grep -v '^[0-9,]*.[0-9,]*$' > $zone.diff.$$
        cat $zone.diff.$$
        # Keep $zone.diff.$$ if you want to debug
        rm $zone.diff.$$
        # for debugging, keep old zone 
        mv $zone $zone.old
    else
        echo "New zone $zone"
    fi
    mv $zone.new $zone

    # Check any subzones
    subzones=$(grep "NS.*$SERVER" $zone | grep -v "^$zone" | cut -f 1 | cut -f 1 -d " ")
    # Notes:
    #  a) Grep out NS lines with our SERVER
    #  b) grep -v ^$zone to avoid checking our self again
    #  c) two cuts since arpa sones use space instead of tab (!??)
    for subzone in $subzones; do
        check_zone $subzone
    done
}

for zone in $ZONES; do
    check_zone $zone
done
