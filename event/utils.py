def coref_rsl(doc_coref, article):
    '''
    :param doc_coref: 2 dimension array, representing a coresponding referent for each word
                    FORMAT: a. non-referent: 'O' ,
                            b. referent: 'sentence_id@start_index@end_index',
                            c. special_referent: 'topic_company*'
    :param article: 2 dimension array, each row representing a sentence and each element in a row representing a word
    :return: None
    '''
    for j in xrange(0, len(article)):
        for ii in xrange(0, len(doc_coref[j])):
            if doc_coref[j][ii] != 'O':
                # if * in the coref means coref_detect.py
                # consider the pronoun to be topic company
                # which not have specific index
                if '*' in doc_coref[j][ii]:
                    doc_coref[j][ii] = doc_coref[j][ii].strip('*')
                else:
                    (f, ref_i) = doc_coref[j][ii].split('-')
                    sen_i, s_i, e_i = [int(tmp) for tmp in ref_i.split('@')]
                    doc_coref[j][ii] = f + '-' + ' '.join(article[sen_i][s_i:e_i])

def load_data(cur, doc_id):
    '''
    :param cur:  DB cursor
    :param doc_id: document id for sql query
    :return: news title, news time and NLP data of this article
    '''
    sql = '''SELECT sentence_id,words,lemma,pos_tags,ner_tags,dependencies,parse_tree \
        FROM sentences WHERE document_id = %s ORDER BY sentence_offset;'''
    cur.execute(sql, (doc_id,))
    sql_results = cur.fetchall()
    ner_tags = [r['ner_tags'] for r in sql_results]
    pos_tags = [r['pos_tags'] for r in sql_results]
    lemmas = [r['lemma'] for r in sql_results]
    words = [r['words'] for r in sql_results]
    sentence_ids = [r['sentence_id'] for r in sql_results]
    # dependencies = [word_depen(depen_str) for depen_str in r['dependencies']]
    # sen_tree =[r['parse_tree'] for r in sql_results]
    sql = '''SELECT news_title,news_time FROM raw_news WHERE news_id = %s;'''
    cur.execute(sql, (doc_id,))
    sql_result = cur.fetchone()
    if sql_result == None:
        news_time,news_title = None,None
    else:
        news_time = sql_result['news_time'].strftime("%Y-%m-%d")
        news_title = sql_result['news_title']
    sql = '''SELECT sen_coref FROM doc_coref WHERE document_id = %s ORDER BY sentence_offset;'''
    cur.execute(sql, (doc_id,))
    sql_results = cur.fetchall()
    doc_corefs = [r['sen_coref'] for r in sql_results]
    coref_rsl(doc_corefs, words)
    nlp_info = {'word': words, 'lemma': lemmas, 'ner': ner_tags, 'pos': pos_tags, 'sen_id': sentence_ids,
                'entity': doc_corefs}
    return news_title, news_time, nlp_info