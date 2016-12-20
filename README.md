Basic required environment:
- Python 2.7 installed
- pip installed
- virtualenv installed
- postgresql 9.4 installed

Steps to Delopy Server:\
Environment Setting
- Using virtualenv to create a wrapped vitural env and activate it
- cd to the directory where requirements.txt is located.
- run: pip install -r requirements.txt in your shell to install required libraries.
- go to https://github.com/brendano/stanford_corenlp_pywrapper and follow the instruction to install the stanford-corenlp-pywrapper as well
- copy the files under the vituralenv wrapper folder, the structure of the files should looks simliar to the following structure
    - virtualenv_warpper
        - bin (virtualenv)
        - include (virtualenv)
        - lib (virtualenv)
        - app.py (server main function here)
        - config.ini (configuration for database and server setting)
        - coref_rsl (co-reference resolution code here)
        - event (event detection code here)
        - html_parser (html parser code here)
        - ner (nlp and ner improvement code here)
        - stanford-corenlp (stanford core nlp.jars files here)
        - utils (some common used functions or files here)
        - setup_db.sql (just used for db init)
        - test_files (not required for server, just for test)

Database setup
- Create a postgre database, update the database info in config.ini
- import db_setup.sql to create the schema of the database

Start the server
- run: python app.py (make sure you activate the vituralenv first before trying start the server)
- server setting can be changed in config.ini, including debug mode, host and port

Other things to notice:\
-Directory '/test_files' is just some simple tests to validate the server work properly. \
-If you want to use test file, you need to install 'Request' library first. Run: pip install requests in your shell.  

Added capability to Dockerize
-Should change passwords in create_db.sql and config.ini to correspond
