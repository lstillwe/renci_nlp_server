#/bin/bash

# get postgres running and load database and tables for nlp server
su -l postgres -c 'nohup /usr/pgsql-9.4/bin/pg_ctl start -s -l /var/lib/pgsql/9.4/pgsql.log -D /var/lib/pgsql/9.4/data &  >>start.log 2>&1'
sleep 5
su -l postgres -c 'psql -a -f /renci_nlp_server/create_db.sql >>start.log 2>&1'
su -l postgres -c 'psql -d nlp -a -f /renci_nlp_server/setup_db.sql >>start.log 2>&1'

# activate virtual env for nlp server
source /renci_nlp_server/bin/activate

# do stuff here to run server & client to feed html input from CyVerse to the renci_nlp_server
python /renci_nlp_server/app.py &
sleep 10
python /renci_nlp_server/nlp_client.py
