from search_ipo_info import IPO_Search
from utils.help_func import get_topic_company
import psycopg2
import psycopg2.extras
from event.utils import load_data
import logging

def ipo_detect(doc_id, db_name, username, pwd, host):
    con = None
    try:
        con = psycopg2.connect(database=db_name, user=username, password=pwd, host=host)
        cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
        news_title, news_time, nlp_info = load_data(cur, doc_id)
        (topic_company, mentioned_comps, comp_pairs) = get_topic_company(nlp_info['word'], nlp_info['ner'], news_title,
                                                                         all_comps=True, comp_pairs=True)

        ipo_detector = IPO_Search(doc_id, topic_company, nlp_info, news_title, news_time)
        # ipo_info = ipo_detector.detect_ipo()
        # return ipo_info
        return ipo_detector
    except psycopg2.DatabaseError, e:
        logging.debug('Error %s' % e)
    finally:
        if con:
            con.close()