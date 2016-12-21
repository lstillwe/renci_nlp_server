from ner.search_keyword import *
from stanford_corenlp_pywrapper import CoreNLP
import psycopg2
import psycopg2.extras
import logging
#proc = CoreNLP("coref", corenlp_jars=["./stanford-corenlp/*"])
proc = CoreNLP(configdict={"annotators":"tokenize, ssplit, pos, lemma, ner, parse"}, corenlp_jars=["./stanford-corenlp/*"])


def nlp_process_article(html_result):
    with open('./utils/titles.csv') as t, open('./utils/keyword.csv') as k:
        titles = [sp.join(line.strip().split()) for line in t.readlines()]
        keywords = {key: value for (key, value) in [line.strip().split(sp) for line in k.readlines()]}
    result = proc.parse_doc(html_result['content'])
    sen_num = len(result['sentences'])
    logging.info('STANFORD NLP PARSE {} SENTENCES IN TOTAL'.format(sen_num))
    ner_tags = []
    pos_tags = []
    lemmas = []
    words = []
    sentence_ids = []
    deps_ccs = []
    parse_trees = []
    for i in xrange(0,sen_num):
        ner_tags.append([ner.encode('utf-8') for ner in result['sentences'][i]['ner']])
        pos_tags.append([pos.encode('utf-8') for pos in result['sentences'][i]['pos']])
        lemmas.append([lem.encode('utf-8') for lem in result['sentences'][i]['lemmas']])
        words.append([token.encode('utf-8') for token in result['sentences'][i]['tokens']])
        sentence_ids.append('{}@{}'.format(html_result['news_id'], i))
        deps_ccs.append(['{}~^~{}~^~{}'.format(*deps) for deps in result['sentences'][i]['deps_cc']])
        parse_trees.append(result['sentences'][i]['parse'])

    search_multi_words(sentence_ids, words, ner_tags, pos_tags, titles, 'TITLE', companies=html_result['company'],
                       people=html_result['people'])
    search_existing_company(sentence_ids, words, ner_tags, pos_tags, companies=html_result['company'])
    search_people(words, ner_tags, people=html_result['people'])
    search_keyword(sentence_ids, words, ner_tags, pos_tags, keywords=keywords, companies=html_result['company'],
                   people=html_result['people'])
    search_company(sentence_ids, words, ner_tags, pos_tags, companies=html_result['company'],
                   people=html_result['people'])
    #result = {'ner_tag': ner_tags, 'pos_tag': pos_tags, 'lemma': lemmas, 'word': words, 'sentence_id': sentence_ids,
              #'parse_tree': parse_trees, 'deps_cc': deps_ccs, 'entity': result['entities'], 'news_id': html_result['news_id']}
    result = {'ner_tag': ner_tags, 'pos_tag': pos_tags, 'lemma': lemmas, 'word': words, 'sentence_id': sentence_ids,
              'parse_tree': parse_trees, 'deps_cc': deps_ccs, 'news_id': html_result['news_id']}
    return result


def update_ner_db(r, db_name, username, pwd, host):
    con = None
    try:
        con = psycopg2.connect(database=db_name, user=username, password=pwd, host=host)
        cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
        sen_num = len(r['word'])
        # [u'parse', u'deps_basic', u'lemmas', u'deps_cc', u'pos', u'tokens', u'entitymentions', u'char_offsets', u'normner', u'ner']
        logging.info('Update NLP data at DB')
        for i in xrange(sen_num):
            sql = 'INSERT INTO sentences(document_id, sentence, words, lemma, pos_tags, dependencies, ner_tags, parse_tree, sentence_offset, sentence_id) \
                  VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
            cur.execute(sql, (r['news_id'], ' '.join(r['word'][i]), r['word'][i], r['lemma'][i], r['pos_tag'][i], r['deps_cc'][i], r['ner_tag'][i], r['parse_tree'][i], i, r['sentence_id'][i]))
            con.commit()

        #coref_count = 0
        #for mention in r['entity']:
            #coref_pairs = []
            #cur = con.cursor()
            #if len(mention['mentions']) > 1:
                #for entity in mention['mentions']:
                    #coref_pairs.append('{}@{}@{}'.format(entity['sentence'], *entity['tokspan_in_sentence']))
                #coref_id = '{}@{}'.format(r['news_id'], coref_count)
                #sql = 'INSERT INTO doc_coreference (document_id, coreferences, coref_offset, coref_id) \
                            #VALUES(%s, %s, %s, %s);'
                #cur.execute(sql, (r['news_id'], coref_pairs, coref_count, coref_id))
                #coref_count += 1

        con.commit()
        logging.info('DOCUMENT {} , SENTENCE {} IN TOTAL'.format(r['news_id'], sen_num))
    except psycopg2.DatabaseError, e:
        logging.debug( 'Error %s' % e)
    finally:
        if con:
            con.close()


def get_ner_by_id(news_id, db_name, username, pwd, host):
    con = None
    try:
        con = psycopg2.connect(database=db_name, user=username, password=pwd, host=host)
        cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
        sql = 'SELECT words, ner_tags FROM sentences WHERE document_id = %s ORDER BY sentence_offset;'
        cur.execute(sql, (news_id, ))
        sql_results = cur.fetchall()
        con.commit()
        ner_tags = [r['ner_tags'] for r in sql_results]
        words = [r['words'] for r in sql_results]
        logging.info( 'DOCUMENT {} , SENTENCE {} IN TOTAL'.format(news_id, len(sql_results)))
        return {'word': words, 'ner_tag': ner_tags}
    except psycopg2.DatabaseError, e:
        logging.debug('Error %s' % e)
    finally:
        if con:
            con.close()
