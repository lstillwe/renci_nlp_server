import psycopg2
import psycopg2.extras
from entity_coref_rsl import CR
from utils.help_func import get_topic_company
import logging
sp = '~^~'


def convert_dep(dep_l):
    deps = []
    for dep in dep_l:
        if '~^~' in dep:
            (tag, head_index, dep_index) = dep.split('~^~')
            deps.append((tag, int(head_index), int(dep_index)))
    return deps


# Person Pipline to Filter Stanford Coref
def person_pip(coref_sessions, article, ner):
    person_prn = ['he', 'she', 'his', 'her', 'him', 'himself', 'herself', 'I', 'my', 'me', 'myself', 'we', 'our', 'us',
                  'ourselves', 'they', 'their', 'themselves']
    for coref_id in coref_sessions:
        coref_session = coref_sessions[coref_id]
        person_count = 0
        for corf in coref_session:
            (sen_id, start_index, end_index) = [int(tmp) for tmp in corf.split('@')]
            word = ' '.join(article[sen_id][start_index:end_index])
            w_ner = ' '.join(ner[sen_id][start_index:end_index])
            if word.lower() in person_prn or 'PERSON' in w_ner:
                person_count += 1
        if person_count != 0:
            yield coref_id


# Organization Pipline to Filter Stanford Coref
# Not used in this file now
def org_pip(coref_sessions, article, ner):
    logging.info('In organization_pipeline')
    org_prn = ['it', 'its']
    # org_noun = ['company', 'firm', 'business', 'group']
    for coref_id in coref_sessions:
        coref_session = coref_sessions[coref_id]
        org_count = 0
        for corf in coref_session:
            (sen_id, start_index, end_index) = [int(tmp) for tmp in corf.split('@')]
            word = ' '.join(article[sen_id][start_index:end_index])
            w_ner = ' '.join(ner[sen_id][start_index:end_index])
            if 'ORGANIZATION' in w_ner and 'PERSON' not in w_ner:
                org_count += 1
            if word.lower() in org_prn:
                org_count += 1
            if word.lower().startswith('the'):
                org_count += 1
        if org_count != 0:
            yield coref_id


# Validate if Coref Session is valid
def validate_coref(coref_session, article):
    person_prn = ['he', 'she', 'her', 'him', 'himself', 'herself', 'I', 'me', 'myself', 'we', 'us', 'ourselves', 'they',
                  'themselves']
    possessive_adj = ['his', 'her', 'my', 'our', 'their', 'its']
    entity_prn = ['it']
    # Validate coref session using two rule: not all words are the same, not all words are pronouns
    prn_count = len(coref_session)
    referent_sum = set()
    for corf in coref_session:
        (sen_id, start_index, end_index) = [int(tmp) for tmp in corf.split('@')]
        word = ' '.join(article[sen_id][start_index:end_index])
        for adj in possessive_adj:
            if word.lower().startswith(adj):
                prn_count -= 1
        if word.lower().startswith('the') or word.lower() in person_prn + entity_prn + possessive_adj:
            prn_count -= 1
        referent_sum.add(word.lower().strip(' \'s').strip(' \''))
    if len(referent_sum) == 1:
        return 0
    elif prn_count == 0:
        return 0.5
    else:
        return 1


# Get candidate referent index(sen_id,start_index,end_index),
# if strict = True, referent cannot be any pronoun unless the coref_session only has pronoun
def get_referent(coref_session, article, strict=False):
    person_prn = ['he', 'she', 'her', 'him', 'himself', 'herself', 'I', 'me', 'myself', 'we', 'us', 'ourselves', 'they',
                  'themselves']
    possessive_adj = ['his', 'her', 'my', 'our', 'their', 'its']
    entity_prn = ['it']
    ref_index = None
    if strict:
        # Using the first phrase which is not pronoun as default referent
        for i in xrange(len(coref_session)):
            (id, s_index, e_index) = [int(tmp) for tmp in coref_session[i].split('@')]
            coref_word = ' '.join(article[id][s_index:e_index])
            if coref_word not in person_prn + possessive_adj + entity_prn:
                ref_index = (id, s_index, e_index)
                break
    if ref_index == None:
        ref_index = [int(tmp) for tmp in coref_session[0].split('@')]
    return ref_index

def load_data(cur, doc_id):
    sql = '''
        SELECT sentence_id,words,lemma,pos_tags,ner_tags,dependencies,parse_tree
		FROM sentences WHERE document_id = %s ORDER BY sentence_offset;
		'''
    cur.execute(sql, (doc_id,))
    sql_results = cur.fetchall()
    ner_tags = [r['ner_tags'] for r in sql_results]
    pos_tags = [r['pos_tags'] for r in sql_results]
    lemmas = [r['lemma'] for r in sql_results]
    words = [r['words'] for r in sql_results]
    sentence_ids = [r['sentence_id'] for r in sql_results]
    dependencies = [convert_dep(r['dependencies']) for r in sql_results]
    parse_trees = [r['parse_tree'] for r in sql_results]
    sql = '''SELECT news_title,news_time FROM raw_news WHERE news_id = %s;'''
    cur.execute(sql, (doc_id,))
    sql_result = cur.fetchone()
    if sql_result is None:
        news_time, news_title = None, None
    else:
        news_time = sql_result['news_time']
        news_title = sql_result['news_title']
    # the commented code used to get Co-reference result parsed from Stanford NLP, but it is not supported now.
    # sql = '''SELECT coref_offset, coreferences FROM doc_coreference WHERE document_id = %s ORDER BY coref_offset;'''
    # cur.execute(sql, (doc_id,))
    # sql_results = cur.fetchall()
    # corefs = {r['coref_offset']: r['coreferences'] for r in sql_results}
    # nlp_info = {'sen_id':sentence_ids, 'word':words, 'lemma':lemmas, 'ner':ner_tags, 'pos':pos_tags,
    #             'dependency':dependencies, 'parse_tree': parse_trees, 'cr':corefs}
    nlp_info = {'sen_id': sentence_ids, 'word': words, 'lemma': lemmas, 'ner': ner_tags, 'pos': pos_tags,
                'dependency': dependencies, 'parse_tree': parse_trees}
    return nlp_info, news_time, news_title


def coref_rsl(doc_id, db_name, username, pwd, host):
    con = None
    try:
        con = psycopg2.connect(database=db_name, user=username, password=pwd, host=host)
        cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
        # Loading Coref_Info and NLP_Info
        nlp_info, news_time, news_title = load_data(cur,doc_id)
        # Get topic company from article
        (topic_company, mentioned_comps, comp_pairs) = get_topic_company(nlp_info['word'], nlp_info['ner'], news_title,
                                                                         all_comps=True, comp_pairs=True)
        # Initialize our CR approach instance and get our CR process result
        cr = CR(nlp_info, topic_company, doc_id)
        cr_result = cr.entity_coref_rsl()

        '''
        # Code under comment aims at
        # merging stanford CR result (nlp_info['coref']) with our naive CR result (cr_result)
        # but this approach is still under development

        merge_cr = []
        for j in xrange(len(nlp_info['word'])):
            merge_cr.append(['O'] * len(nlp_info['word']))

        # Get coref_id for person and org pipeline individually
        person_pipeline = person_pip(nlp_info['cr'], nlp_info['word'], nlp_info['ner'])
        # org_pipeline = org_pip(corefs, words, ner_tags)

        for coref_id in person_pipeline:
            if validate_coref(nlp_info['cr'][coref_id], nlp_info['word']) > 0.5:
                (p_sen_id, p_s_id, p_e_id) = get_referent(nlp_info['cr'][coref_id], nlp_info['word'], strict=True)
                # check if referent have further referent in cr_result, if any, update referent
                for r in search_tag(cr_result[p_sen_id][p_s_id:p_e_id], 'O', cr_result[p_sen_id][p_s_id:p_e_id]):
                    (p_sen_id, p_s_id, p_e_id) = [int(tmp) for tmp in r.split('@')]
                # transfer index to word
                person_referent = ' '.join(nlp_info['word'][p_sen_id][p_s_id:p_e_id])
                for coref in nlp_info['cr'][coref_id]:
                    (sen_id, start_index, end_index) = [int(tmp) for tmp in coref.split('@')]
                    word = ' '.join(nlp_info['word'][sen_id][start_index:end_index])
                    # update person referent to entity map
                    if person_referent != ' '.join(nlp_info['word'][sen_id][start_index:end_index]):
                        if (end_index - start_index) <= 6:
                            for ii in xrange(start_index, end_index):
                                cr_result[sen_id][ii] = 'I-' + coref
                            cr_result[sen_id][start_index] = 'B-' + coref
        '''
        # update CR in database
        for j in xrange(0, len(nlp_info['word'])):
            value_sets = {"sen_id": nlp_info['sen_id'][j], "sen_coref": cr_result[j], "doc_id": doc_id, "sen_offset": j}
            cur.execute('''INSERT INTO doc_coref(sentence_id, sen_coref, document_id, sentence_offset)
                                VALUES (%(sen_id)s,%(sen_coref)s,%(doc_id)s,%(sen_offset)s);''', value_sets)
        logging.info('Document {} finished coref parser.'.format(doc_id))
        con.commit()
    except psycopg2.DatabaseError, e:
        logging.info('Error %s' % e)
    finally:
        if con:
            con.close()
