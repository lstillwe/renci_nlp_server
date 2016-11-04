from ConfigParser import ConfigParser
from coref_rsl.coref_detect import coref_rsl
from event.ipo.ipo_detect import ipo_detect
from event.layoff.layoff_detect import layoff_detect
from flask import Flask, request, Response, json
from html_parser.html_parsers import parser, update_news_db, get_news_by_url
from ner.CoreNLP import nlp_process_article, update_ner_db, get_ner_by_id

app = Flask(__name__)


@app.route('/nlp', methods=['GET', 'POST'])
def get_html():
    if request.method == 'POST':
        content = request.form['html']
        if content == '':
            return Response('Received data is Empty.', 400)
        # get db info from config.ini file
        config = ConfigParser()
        config.read('config.ini')
        db_name, username, host, pwd = config.get('DATABASE', 'db_name'), config.get('DATABASE', 'username'), config.get('DATABASE', 'host'), config.get('DATABASE', 'password')
        # Try to search if news is already in database
        news_id = get_news_by_url(request.form['url'], db_name, username, pwd, host)
        # if not, using parser to parse the html and store the result in the database
        if news_id is None:
            result = parser(content)
            if result is None:
                return Response('Received html is not compatible with our parsers.', 400)
            result['url'] = request.form['url']
            news_id = update_news_db(result, db_name, username, pwd, host)
            result['news_id'] = news_id
            ner_result = nlp_process_article(result)
            update_ner_db(ner_result, db_name, username, pwd, host)
            coref_rsl(news_id, db_name, username, pwd, host)
        else:
            ner_result = get_ner_by_id(news_id, db_name, username, pwd, host)
        # PROCESS THE EACH WORD IN A SENTENCE AND ITS NER
        # Flat the nested list to be one list
        ners = [ner if ner in ['ORGANIZATION', 'PERSON', 'TITLE', 'LOCATION'] else 'O' \
                for ner_tag in ner_result['ner_tag'] for ner in ner_tag]
        word_l = [y for x in ner_result['word'] for y in x]
        mydata = {"data": {'ner': ners, 'word': word_l}}

        # Find event Type
        if request.form['event'] == 'IPO':
            ipo_detector = ipo_detect(news_id, db_name, username, pwd, host)
            ipo_info = ipo_detector.detect_ipo()
            mydata['IPO'] = ipo_info
        elif request.form['event'] == 'Layoff':
            layoff_detector = layoff_detect(news_id, db_name, username, pwd, host)
            layoff_info = layoff_detector.detect_layoff()
            mydata['Layoff'] = layoff_info
        return Response(json.dumps(mydata), mimetype='application/json')

    return 'Hello World!'


if __name__ == '__main__':
    config = ConfigParser()
    config.read('config.ini')
    app.run(host=config.get('SEVER_SETTING', 'host'), port=config.getint('SEVER_SETTING', 'port'),
            debug=config.getboolean('SEVER_SETTING', 'debug_mode'))
