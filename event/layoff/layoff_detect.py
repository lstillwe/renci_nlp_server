import psycopg2
from event.utils import load_data
from event.layoff.search_layoff_info import Layoff_Search
from utils.help_func import get_topic_company


def layoff_detect(doc_id, db_name, username, pwd, host):
    con = None
    try:
        con = psycopg2.connect(database=db_name, user=username, password=pwd, host=host)
        cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
        news_title, news_time, nlp_info = load_data(cur, doc_id)
        (topic_company, mentioned_comps, comp_pairs) = get_topic_company(nlp_info['word'], nlp_info['ner'], news_title,
                                                                         all_comps=True, comp_pairs=True)
        layoff_detector = Layoff_Search(doc_id, nlp_info, news_title, news_time, topic_company, mentioned_comps)
        # layoff_info = layoff_detector.detect_layoff()
        # print layoff_detector.layoff_sens
        # return layoff_info
        return layoff_detector
    except psycopg2.DatabaseError, e:
        print 'Error %s' % e
    finally:
        if con:
            con.close()


