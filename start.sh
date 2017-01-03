#!/bin/bash

usage() {
      echo ""
      echo "Usage : $0 [-e|--event <ipo|layoff>] [<input_html_file>]"
      echo ""
      exit 1
}

while getopts ":he:" opt; do
  case $opt in
    e)
      e=${OPTARG}
      [[ "$e" == "ipo" ]] || [[ "$e" == "IPO" ]] || [[ "$e" == "layoff" ]] || [[ "$e" == "Layoff" ]] || [[ "$e" == "LAYOFF" ]] || usage
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      exit 1
      ;;
    h | *)
      usage
      ;;
  esac
done
if [ -z "$e" ] 
then 
      usage
fi

# get postgres running and load database and tables for nlp server
su -l postgres -c 'nohup /usr/pgsql-9.4/bin/pg_ctl start -s -l /var/lib/pgsql/9.4/pgsql.log -D /var/lib/pgsql/9.4/data >nohup.out 2>&1 &'
sleep 5
su -l postgres -c 'psql -a -f /renci_nlp_server/create_db.sql >>start.log 2>&1'
su -l postgres -c 'psql -d nlp -a -f /renci_nlp_server/setup_db.sql >>start.log 2>&1'

# activate virtual env for nlp server
cd /renci_nlp_server
source bin/activate

# do stuff here to run server & client to feed html input from CyVerse to the renci_nlp_server
FILE_TO_WATCH=./nohup.out
SEARCH_PATTERN='INFO:CoreNLP_PyWrapper:Subprocess'
nohup python app.py >nohup.out 2>&1 &
sleep 5
timeout --signal=SIGINT 60 tail -f -n0 ${FILE_TO_WATCH} | grep -qe ${SEARCH_PATTERN}
if [ $? == 1 ]; then
    echo "ERROR: NLP Server failed to initialize"
    exit
fi
python nlp_client.py $e $3
