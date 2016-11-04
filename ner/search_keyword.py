import re
from ner_info import *
import logging
special = "-&'s,"


def search(sen_id, sen, sen_ner, sen_pos, ii, keyword, people=[]):
    if sen_ner[ii] == 'TITLE':
        return False
    if sen_ner[ii] == 'ORGANIZATION':
        return True
    if sen[ii] in special_term:
        return False
    if re.compile('.*[A-Z|\d].*').match(sen[ii]) != None:
        if re.compile('NN.*').match(sen_pos[ii]) != None:
            if sen_ner[ii] in 'O/MISC':
                logging.info('a.Search_Func:\tsen_id:{}:\tword:{}\t|stanford ner:{}; predicted: ORGANIZATION, keyword:{}'.format(
                    sen_id, sen[ii], sen_ner[ii], keyword))
                sen_ner[ii] = 'ORGANIZATION'
                return True
            elif sen_ner[ii] == 'PERSON':
                if search_person_flag(sen_id, sen, sen_ner, sen_pos, ii, people=people):
                    pass
                else:
                    logging.info('b.Search_Func:\tsen_id:{}:\tword:{}\t|stanford ner:{}; predicted: ORGANIZATION, keyword:{}'.format(
                        sen_id, sen[ii], sen_ner[ii], keyword))
                    sen_ner[ii] = 'ORGANIZATION'
                    return True
    elif sen[ii] in special:
        f = min(ii + 1, len(sen) - 1)
        b = max(0, ii - 1)
        if search(sen_id, sen, sen_ner, sen_pos, f, keyword, people=people) and \
                search(sen_id, sen, sen_ner, sen_pos, b, keyword, people=people):
            logging.info('c.Search_Func(exception):\tsen_id:{}:\tword:{}\t|stanford ner:{}; predicted: ORGANIZATION, keyword:{}'.format(
                sen_id, sen[ii], sen_ner[ii], keyword))
            sen_ner[ii] = 'ORGANIZATION'
            return True
    return False


def search_person_flag(sen_id, sen, sen_ner, sen_pos, key_index, people=[]):
    search_range = 5
    profile_words = ['figure', 'named', 'owner', 'who']
    i = sen_id.split('@')[0]
    mode = [sen_ner[ii] if sen[ii] != ',' else sen[ii] for ii in xrange(key_index, min(len(sen), key_index + 8))]
    if re.compile('([A-Z]*~\^~)*,~\^~([A-Z]*~\^~)*TITLE(~\^~[A-Z]*)*').match(sp.join(mode)):
        # logging.info( sen[key_index], sen[key_index:key_index + 8])
        logging.info( '{}\t{} is recognized as PERSON because of rule 4'.format(sen_id, sen[key_index]))
        people.append(sen[key_index])
        return True

    mode = [sen_ner[ii] if sen[ii] != ',' else sen[ii] for ii in xrange(max(0, key_index - 8), key_index + 1)]
    if re.compile('([A-Z|,]*~\^~)*TITLE~\^~(,~\^~)?(PERSON~\^~)*PERSON').match(sp.join(mode)):
        logging.info( '{}\t{} is recognized as PERSON because of rule 5'.format(sen_id, sen[key_index]))
        people.append(sen[key_index])
        return True

    if sen[key_index] in sp.join(people):
        logging.info( '{}:\t{} is recognized as PERSON because of rule 1'.format(sen_id, sen[key_index]))
        return True

    for ii in xrange(max(0, key_index - search_range), min(key_index + search_range, len(sen))):
        if re.compile('PRP.*').match(sen_pos[ii]) != None and re.compile('it*').match(sen[ii].lower()) is None:
            if ii < key_index and 'VB' in sp.join(sen_pos[ii:key_index]):
                return False
            elif ii > key_index and 'VB' in sp.join(sen_pos[key_index:ii]):
                return False
            else:
                logging.info( '{}\t{} is recognized as PERSON because of rule 2'.format(sen_id, sen[key_index]))
                people.append(sen[key_index])
                return True

    if ',~^~who' in sp.join(sen[key_index:key_index + 5]):
        # logging.info( sen[key_index], sen[key_index:key_index + 5])
        logging.info('{}\t{} is recognized as PERSON because of rule 3'.format(sen_id, sen[key_index]))
        people.append(sen[key_index])
        return True
    return False


def search_keyword(id, article, ner, pos, keywords=[], companies=[], people=[]):
    for j in xrange(0, len(article)):
        sen = article[j]
        sen_ner = ner[j]
        sen_id = id[j]
        sen_pos = pos[j]
        i = sen_id.split('@')[0]
        for word_i in xrange(len(sen)):
            word = sen[word_i]
            # For pattern Location xxx-based company
            if word.endswith('-based') and word[0].isupper():
                sen_ner[word_i] = 'LOCATION'
                for ii in xrange(word_i-1, max(word_i-3, -1), -1):
                    if sen[ii].istitle() and sen_ner[ii] != 'LOCATION':
                        logging.info('Based_pattern: sen:{} , change {} from {} to \'LOCATION\',keyword {}'.format(sen_id,
                                                                            sen[ii],
                                                                            sen_ner[ii],
                                                                            word))
                        if sen_ner[ii] == 'ORGANIZATION':
                            try:
                                companies.remove(sen[ii])
                                logging.info( 'Remove {} from companies'.format(sen[ii]), companies)
                            except ValueError:
                                logging.debug( 'Error: Word {} is not in {}'.format(sen[ii], companies))
                        sen_ner[ii] = 'LOCATION'
                    else:
                        break
                com_candidate = []
                for ii in xrange(word_i + 1, min(word_i + 6, len(sen))):
                    if sen[ii] in special_term:
                        continue
                    if re.compile('.*[A-Z].*').match(sen[ii]) != None:
                        if re.compile('NN.*').match(sen_pos[ii]) != None:
                            if sen_ner[ii] != 'ORGANIZATION':
                                logging.info( 'Based_Patt:\tsen_id:{}:\tword:{}\t|stanford ner:{}; predicted: ORGANIZATION, keyword:{}'.format(
                                    sen_id, sen[ii], sen_ner[ii], word))
                            sen_ner[ii] = 'ORGANIZATION'
                            com_candidate.append(sen[ii])
                        else:
                            break
                    else:
                        break
                if len(com_candidate) > 0:
                    # logging.info( ' '.join(com_candidate), sp.join(companies))
                    if ' '.join(com_candidate) not in sp.join(companies):
                        companies.append(' '.join(com_candidate))
                        logging.info( '1~Add {} to company list'.format(' '.join(com_candidate)))
            # Search keywords like company/business.....
            elif word in keywords:
                keyword = word
                start_flag = False
                search_flag, search_range = keywords[keyword].split('@')
                sen_ner[sen.index(keyword)] = 'ORGANIZATION' if search_range == '1' else 'O'
                search_range = 10 if search_range == '0' else 5
                if search_flag != '1':
                    search_index = 0
                    while search_index < len(sen):
                        com_candidate = []
                        end_search = 0
                        try:
                            end = sen[search_index:].index(keyword)
                            for ii in xrange(end + search_index - 1, max(0, end + search_index - search_range) - 1, -1):
                                end_search = ii
                                if search(sen_id, sen, sen_ner, sen_pos, ii, keyword, people=people):
                                    start_flag = True
                                    com_candidate.insert(0, sen[ii])
                                elif start_flag:
                                    end_search = ii + 1
                                    break
                            if ' '.join(com_candidate) in local_city:
                                logging.info('Consider {} to be local city'.format(' '.join(com_candidate)), ' '.join(
                                    sen[max(0, end - search_range):end]))
                                # sen_ner[ii-1] = 'LOCATION'
                                for jj in xrange(end_search, end_search + len(com_candidate)):
                                    # logging.info(sen[jj], sen_ner[jj])
                                    sen_ner[jj] = 'LOCATION'
                            elif ' '.join(com_candidate) not in sp.join(companies):
                                companies.append(' '.join(com_candidate))
                                logging.info('2~Add {} to company list'.format(' '.join(com_candidate)))
                        except ValueError:
                            break
                        search_index += end + 1
                if search_flag != '-1':
                    search_index = 0
                    while search_index < len(sen):
                        com_candidate = []
                        end_search = 0
                        try:
                            start = sen.index(keyword) + 1
                            for ii in xrange(start + search_index, min(start + search_index + search_range, len(sen))):
                                end_search = ii - 1
                                if search(sen_id, sen, sen_ner, sen_pos, ii, keyword, people=people):
                                    start_flag = True
                                    com_candidate.append(sen[ii])
                                elif start_flag:
                                    end_search = ii - 1
                                    break
                            if ' '.join(com_candidate) in local_city:
                                logging.info('Consider {} to be Local City'.format(' '.join(com_candidate)), ' '.join(
                                    sen[start:min(start + search_range, len(sen))]))
                                for jj in xrange(end_search, end_search - len(com_candidate), -1):
                                    # logging.info( sen[jj], sen_ner[jj])
                                    sen_ner[jj] = 'LOCATION'
                            elif ' '.join(com_candidate) not in sp.join(companies):
                                logging.info( '3~Add {} to company list'.format(' '.join(com_candidate)))
                                companies.append(' '.join(com_candidate))
                        except ValueError:
                            break
                        search_index += start + 1


def search_people(article, ner, people=[]):
    names = []
    for per_name in people:
        names.extend(per_name.split(' '))
    for j in xrange(0, len(article)):
        sen = article[j]
        sen_ner = ner[j]
        for word in sen:
            if word in names:
                sen_ner[sen.index(word)] = 'PERSON'


def search_company(id, article, ner, pos, companies={}, people={}):
    i = id[0].split('@')[0]
    names = [com_word for com_name in companies for com_word in com_name.split(' ') if com_word != '']
    comps_postfixes = ['Inc.', ', Inc.', 'Corp.', '& Co.', 'Co.']
    # for j in xrange(0,len(article)):

    #	if len(sen) < 12:
    #		match_special_patt(i,j)
    #	for word in sen:
    #		if word in set(names):
    #			ii = sen.index(word)
    #			search(sen_id,sen,sen_ner,sen_pos,ii,word)
    long_names = []
    short_names = []
    for name in companies:
        if len(name.split(' ')) > 1:
            long_names.append(name)
            for postfix in comps_postfixes:
                name.strip(postfix)
            if len(name.split(' ')) > 2:
                for jj in xrange(2, len(name.split(' '))):
                    long_names.append(' '.join(name.split(' ')[:jj]))
            elif name.split(' ')[0] not in special:
                short_names.append(name.split(' ')[0])
        elif name != '' and name not in special:
            short_names.append(name)
    long_names = [com_name.replace(' ', sp) for com_name in long_names]
    long_names = [name for name in long_names if name.replace(sp, ' ').replace('.', '') not in local_city + state_name]
    logging.info( 'Article {} Company Name Substring Match:\t{}'.format(i, long_names))
    search_multi_words(id, article, ner, pos, long_names, 'ORGANIZATION')

    # filter location names
    short_names = [name for name in short_names if name.replace(sp, ' ') not in local_city]
    logging.info('Article {} Company Name String Match:\t{}'.format(i, short_names))
    for j in xrange(0, len(article)):
        sen_id = id[j]
        sen = article[j]
        sen_ner = ner[j]
        sen_pos = pos[j]
        for ii in xrange(0, len(sen)):
            if sen[ii] in short_names and sen[ii] not in people:
                if sen_ner[ii] != 'ORGANIZATION':
                    logging.info('Com_Func:\tsen_id:{}:\tword:{}\t|stanford ner:{}; predicted: ORGANIZATION, keyword:{}'.format(
                        sen_id, sen[ii], sen_ner[ii], sen[ii]))
                    sen_ner[ii] = 'ORGANIZATION'


# def match_special_patt(i,j):
# 	sen = sp.join(sen)
# 	if re.compile('^(.*~\^~)*([A-Z].*~\^~)+on~\^~([A-Z].*~\^~)+[Street|Avenue](.*~\^~)*\.$').match(sen)!= None:
# 		sen = sen.split(sp)
# 		key_index = sen.index('on')
# 		start_index = 0
# 		end_index = 0
# 		for ii in xrange(0,key_index):
# 			if sen[ii][0].isupper():
# 				start_index = ii
# 				break
# 		for ii in xrange(start_index,key_index):
# 			sen_ner[ii] = 'ORGANIZATION'
# 		logging.info( '4~Add {} to company list, based on Special_Patt:\t xxx on the street.'.format(' '.join(sen[start_index:key_index])))
# 		try:
# 			end_index = sen.index('Street')
# 		except ValueError:
# 			try:
# 				end_index = sen.index('Avenue')
# 			except ValueError:
# 				logging.debug( '*****************Pattern Error**************')
# 		for ii in xrange(key_index,end_index):
# 			sen_ner[ii+1] = 'LOCATION'
# 		logging.info( 'Change {} to be location, based on Special_Patt:\t xxx on the street.'.format(' '.join(sen[key_index:end_index])))




def search_multi_words(id, article, ner, pos, words, tag, companies={}, people={}):
    i = id[0].split('@')[0]
    for word in words:
        for j in xrange(0, len(article)):
            sen_id = id[j]
            sen = article[j]
            sen_ner = ner[j]
            sen_pos = pos[j]
            start = 0
            end = 0
            search_index = 0
            while search_index < len(sen):
                try:
                    if tag == 'TITLE':
                        start = sp.join(sen[search_index:]).lower().split(sp).index(word.split(sp)[0].lower())
                        end = sp.join(sen[search_index:]).lower().split(sp).index(word.split(sp)[-1].lower())
                    else:
                        start = sen[search_index:].index(word.split(sp)[0])
                        end = sen[search_index:].index(word.split(sp)[-1])
                    start += search_index
                    end += search_index
                except ValueError:
                    break
                if word.lower() == sp.join(sen[start:end + 1]).lower() or (
                            word == 'Chief~^~Officer' and end - start < 5 and end > start):
                    # if word == 'Chief~^~Officer':
                    #     logging.info( ' '.join(sen[start:end + 1]))
                    for ii in xrange(start, end + 1):
                        if tag == 'ORGANIZATION' and sen_ner[ii] != tag:
                            logging.info( 'Search_Multi:\tsen_id:{}:\tword:{}\t|stanford ner:{}; predicted: ORGANIZATION, keyword:{}'.format(
                                sen_id, sen[ii], sen_ner[ii], word))
                        elif tag == 'TITLE':
                            logging.info( 'Search_Multi:\tsen_id:{}:\tword:{}\t|stanford ner:{}; predicted: TITLE, keyword:{}'.format(
                                sen_id, sen[ii], sen_ner[ii], word))
                        sen_ner[ii] = tag
                    if tag == 'TITLE':
                        com_candidate = []
                        if start > 0 and re.compile('.*[A-Z].*').match(sen[start - 1]) != None:
                            search_range = 3
                            for ii in xrange(start - 1, max(0, start - 1 - search_range) - 1, -1):
                                if re.compile('.*[A-Z].*').match(sen[ii]) != None or sen[ii] in "-&'s,":
                                    if sen[ii] not in special_term:
                                        com_candidate.insert(0, sen[ii])
                                        sen_ner[ii] = 'ORGANIZATION'
                                else:
                                    break
                            if sp.join(com_candidate) not in sp.join(companies):
                                companies.append(' '.join(com_candidate))
                                logging.info( '4~Add {} to company list because of Pattern: Company + Title + Person'.format(
                                    ' '.join(com_candidate)))
                        if end < len(sen) and sen[end + 1][0].isupper():
                            per_candidate = []
                            for ii in xrange(end + 1, min(len(sen), end + 4)):
                                if sen[ii][0].isupper():
                                    if sen_ner[ii] == 'ORGANIZATION':
                                        logging.info( '**********{} is ALREADY be recoginzed as ORGANIZATION'.format(sen[ii]))
                                    else:
                                        sen_ner[ii] = 'PERSON'
                                        logging.info( '{}\t{} is recognized as PERSON because of Pattern: Company + Title + Person'.format(
                                            sen_id, sen[ii]))
                                        per_candidate.append(sen[ii])
                                else:
                                    people.append(' '.join(per_candidate))
                                    break
                                logging.info( '~Add {} to person list because of Pattern: Company + Title + Person'.format(
                                    ' '.join(per_candidate)))
                        if len(com_candidate) == 0:
                            try:
                                sub_start = sen[end + 1:].index('of')
                            except ValueError:
                                try:
                                    sub_start = sen[end + 1:].index('for')
                                except ValueError:
                                    sub_start = -1
                            if sub_start != -1 and sub_start < 6:
                                search_start = False
                                for ii in xrange(end + sub_start + 1, len(sen)):
                                    if re.compile('.*[A-Z|\d].*').match(sen[ii]) != None and re.compile('NN.*').match(
                                            sen_pos[ii]) != None and sen[ii] not in special_term:
                                        sen_ner[ii] = 'ORGANIZATION'
                                        logging.info( '{}\t{} is recognized as ORGANIZATION because of Pattern: Title of Company'.format(
                                            sen_id, sen[ii]))
                                        search_start = True
                                    elif search_start:
                                        break
                search_index = start + 1


def search_existing_company(id, article, ner, pos, companies=[]):
    logging.info( 'Existing Cmompany:',)
    for j in xrange(0, len(article)):
        sen_id = id[j]
        sen = article[j]
        sen_ner = ner[j]
        sen_pos = pos[j]
        if 'ORGANIZATION' in sen_ner:
            com_candidate = []
            for ii in xrange(sen_ner.index('ORGANIZATION'), len(sen_ner)):
                if sen_ner[ii] == 'ORGANIZATION':
                    com_candidate.append(sen[ii])
                else:
                    if ' '.join(com_candidate) == 'IPO':
                        sen_ner[ii - 1] = 'O'
                    elif len(com_candidate) > 0 and ' '.join(com_candidate) not in companies:
                        logging.info(' '.join(com_candidate), '||',)
                        companies.append(' '.join(com_candidate))
                    com_candidate = []
