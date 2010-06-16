: stain@shrek ~;cat /etc/cron.d/mysql-backup 
# Make sure this is run before the backup of /
36 2 * * * root /usr/local/bin/mysqlbackup
: stain@shrek ~;cat /usr/local/bin/mysqlbackup 
#!/bin/bash

cd /var/adm/backup/mysql || exit 1
rm *sql

databases=$(mysql --batch --exec 'SHOW DATABASES;' | tail +2)

for db in $databases ; do 
    mysqldump --all --extended-insert \
              --databases $db > $db.sql
done

