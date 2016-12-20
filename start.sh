#/bin/bash

su -l postgres -c 'nohup /usr/pgsql-9.4/bin/pg_ctl start -s -l /var/lib/pgsql/9.4/pgsql.log -D /var/lib/pgsql/9.4/data'
psql -a -f renci_nlp_server/create_db.sql
psql -d nlp -a -f renci_nlp_server/setup_db.sql
