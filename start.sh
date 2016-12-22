#/bin/bash

su -l postgres -c 'nohup /usr/pgsql-9.4/bin/pg_ctl start -s -l /var/lib/pgsql/9.4/pgsql.log -D /var/lib/pgsql/9.4/data &  >>start.log 2>&1'
sleep 5
su -l postgres -c 'psql -a -f /renci_nlp_server/create_db.sql >>start.log 2>&1'
su -l postgres -c 'psql -d nlp -a -f /renci_nlp_server/setup_db.sql >>start.log 2>&1'

source /renci_nlp_server/bin/activate

# do stuff here to run client to feed html input from CyVerse to the renci_nlp_server
python /renci_nlp_server/nlp_client.py
