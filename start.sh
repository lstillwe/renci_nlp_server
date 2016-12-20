#/bin/bash

su -l postgres -c '/usr/pgsql-9.4/bin/pg_ctl start -s -l /var/lib/pgsql/9.4/pgsql.log -D /var/lib/pgsql/9.4/data'
sleep 5
su -l postgres -c 'psql -a -f /renci_nlp_server/create_db.sql'
su -l postgres -c 'psql -d nlp -a -f /renci_nlp_server/setup_db.sql'
