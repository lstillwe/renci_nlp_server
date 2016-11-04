from search_keyword import *
import psycopg2
import psycopg2.extras
import sys
keyword_file = r'./keywords.csv'
title_file = r'./titles.csv'
doc_num = 100
keywords, titles = None,None
with open(keyword_file) as k, \
    open(title_file) as t:
        keywords = {key:value for (key,value) in [line.strip().split(sp) for line in k.readlines()]}
        titles = [sp.join(line.strip().split())for line in t.readlines()]

con = None
try:
    con = psycopg2.connect(database='master_thesis', user='yiqiwang')
    cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
    for doc_id in xrange(1,doc_num+1):
        sql = '''SELECT sentence_id,words,lemma,pos_tags,ner_tags FROM sentences WHERE document_id = %s ORDER BY sentence_offset;'''
        # news_id, url, news_title, news_text, news_time, mentioned_org, mentioned_people
        cur.execute(sql,(doc_id,))
        sql_results = cur.fetchall()
        ner_tags = [r['ner_tags'] for r in sql_results]
        pos_tags = [r['pos_tags'] for r in sql_results]
        lemmas = [r['lemma'] for r in sql_results]
        words = [r['words'] for r in sql_results]
        sentence_ids = [r['sentence_id'] for r in sql_results]
        
        cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
        sql = '''SELECT mentioned_org,mentioned_people FROM raw_news WHERE news_id = %s'''
        cur.execute(sql,(doc_id,))
        sql_results = cur.fetchone()
        if sql_results == None:
            continue
        companies = {str(doc_id) : sql_results['mentioned_org']}
        people = {str(doc_id) :sql_results['mentioned_people']}
        search_multi_words(sentence_ids, words, ner_tags, pos_tags, titles, 'TITLE', companies=companies, people=people)
        search_existing_company(sentence_ids, words, ner_tags, pos_tags, companies=companies)
        search_people(str(doc_id), words, ner_tags, people=people)
        search_keyword(sentence_ids, words, ner_tags, pos_tags, keywords=keywords, companies=companies, people=people)
        search_company(sentence_ids, words, ner_tags, pos_tags, companies=companies, people=people)
        sql = '''UPDATE sentences SET ner_tags= %s WHERE sentence_id = %s '''
        sen_num = len(sentence_ids)
        for i in xrange(0,sen_num):
            sentence_id = sentence_ids[i]
            ner_tag = ner_tags[i]
            cur.execute(sql,(ner_tag,sentence_id))
    con.commit()
except psycopg2.DatabaseError, e:
    print 'Error %s' % e
finally:
    if con:
        con.close()
