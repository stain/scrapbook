#!/usr/bin/python

import os
import random
import time

# KONSTANTER

LOGFILE = "/usr/local/mailman/var/logs/sync_mailinglists_log.txt"
LOG = open(LOGFILE, "a")
LOG.write("===== Run %s.\n" % (time.asctime(time.localtime())) )

GET_DB = 'mysql -h mysql.stud.ntnu.no -u admin_group_ro -B -e "select * from Mailinglists;" admin_groups'
WRITE_DB = 'mysql -h mysql.stud.ntnu.no -u admin_group_rw -passord admin_groups'
MYSQL_CMDS = "/usr/local/mailman/var/logs/mysql_cmds.txt"
MYSQL_OUTPUT = "/usr/local/mailman/var/logs/mysql_output.txt"
LIST_LISTS = "/usr/local/mailman/bin/list_lists"
NEWLIST = "/usr/local/mailman/bin/newlist"
RMLIST = "/usr/local/mailman/bin/rmlist"

# Bokstaver passordet kan bestå av; a-z og 0-9
PWCHARS = [chr(n) for n in range(97,123)] + map(str, range(10))
# Antall bokstaver i passordet
PWLEN = 6


# FUNKSJONER

def makepw():
        "Lager et tilfeldig passord"
        pw = ""
        for i in range(PWLEN):
                pw += random.choice(PWCHARS)
        return pw


# PROGRAMMET

# Lagre hele databasen Mailinglists som et 2d-array i db.
db = [(a.split()).lower() for a in os.popen(GET_DB).readlines()]
db.pop(0) #overskrifter

# Lagre alle eksisterende mailinglister som et array existing.
existing = [(a.split()[0]).lower() for a in os.popen(LIST_LISTS).readlines()]
existing.pop(0) #overskrifter


new = [a for a in db if a[1] not in existing and a[3] == 0]
# print new
for (studorg, list, owner, delete) in new:
	# Opprett lista og sjekk for returverdi.
	retval = os.system("echo |%s %s %s %s" % (NEWLIST, list, "%s@stud.ntnu.no" % (owner), makepw()))
	if retval != 0:
		LOG.write("Noe skar seg ved oppretting av lista %s.\n" % (list))
	else:
		LOG.write("Opprettet liste: %s\n" % (list))


cmds = open(MYSQL_CMDS, "w")
deleted = [a[1] for a in db if a[3] == "1"]
for list in deleted:

	if not list in existing:
		LOG.write("Jeg skulle slette lista %s, men så fantes den ikke!\n" % (list))
		cmds.write('delete from Mailinglists where list_name = "%s";\n' % (list))
		continue  # Start med neste liste.

	retval = os.system("%s -a %s" % (RMLIST, list))
	if retval != 0:
		LOG.write("Noe skar seg ved sletting av lista %s.\n" % (list))
		cmds.write('update Mailinglists set deleted=0 where list_name="%s";\n' % (list))
	else:
		LOG.write("Slettet liste: %s\n" % (list))
		cmds.write('delete from Mailinglists where list_name = "%s";\n' % (list))

db_list_names = [a[1] for a in db]
not_in_db = [a for a in existing if not a in db_list_names]
for list in not_in_db:
	parts = list.split("-")
	if len(parts[0]) > 8:
		continue
	LOG.write("Legger til lista %s i databasen.\n" % (list))
	cmds.write('insert into Mailinglists set group_name="%s", list_name="%s", owner="root", deleted=0;\n' % (parts[0], list))

cmds.close()
retval = os.system("%s < %s > %s" % (WRITE_DB, MYSQL_CMDS, MYSQL_OUTPUT))
if retval != 0:
	LOG.write("Errors occured while executing MySQL commands:\n")
	LOG.write(open(MYSQL_OUTPUT).read())
		
LOG.close()





