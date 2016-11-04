import re
from datetime import datetime, timedelta
from event.event_info import financial_terms, months, date_indice, sp, special_terms
import logging
def search_tag(sen, tag, sen_tag, index=False):
    if tag == 'O':
        last_tag = None
        start_index = None
        for i in xrange(0, len(sen)):
            if last_tag == None:
                # cannot just use sen_tag[i][2:] since sen_tag can be 'O'
                last_tag = sen_tag[i].replace('B-', '') if sen_tag[i].startswith('B-') else sen_tag[i].replace('I-', '')
                start_index = i
            elif 'B-' + last_tag != sen_tag[i] and 'I-' + last_tag != sen_tag[i]:
                if last_tag != tag:
                    if index:
                        yield (start_index, i, last_tag)
                    else:
                        yield last_tag
                last_tag = sen_tag[i].replace('B-', '') if sen_tag[i].startswith('B-') else sen_tag[i].replace('I-', '')
                start_index = i
        if last_tag != tag:
            if index:
                yield (start_index, len(sen), last_tag)
            else:
                yield last_tag
    elif tag in sen_tag:
        com_candidate = []
        for ii in xrange(sen_tag.index(tag), len(sen_tag)):
            if sen_tag[ii] == tag:
                com_candidate.append(sen[ii])
            elif len(com_candidate) > 0:
                if index:
                    yield (ii - len(com_candidate), ' '.join(com_candidate))
                else:
                    yield ' '.join(com_candidate)
                com_candidate = []


def search_word(word, sen, case_sensitive=False):
    word_l = [word]
    if ' ' in word:
        word_l = word.split(' ')
    sen_l = sen
    if not case_sensitive:
        sen_l = [w.lower() for w in sen]
        word_l = [w.lower() for w in word_l]
    i = 0
    j = 0
    while i < len(sen_l):
        if sen_l[i] == word_l[j]:
            j += 1
        else:
            j = 0
        i += 1
        if j == len(word_l):
            yield i-len(word_l)
            j = 0


def match_substring(word1, word2):
    long_word = word1 if len(word1) > len(word2) else word2
    short_word = word1 if len(word1) <= len(word2) else word2
    threshold = min(int(0.8 * len(long_word)), 7)
    try:
        start_index = long_word.index(short_word[0])
    except ValueError:
        return False
    for i in xrange(start_index, min(start_index + len(short_word), len(long_word))):
        if long_word[i] == short_word[i - start_index]:
            threshold -= 1
        else:
            break
    if threshold > 0:
        return False
    return True


def get_topic_company(article, ner, news_title, all_comps=False, comp_pairs=False):
    (companies, entity_pair) = search_existing_company(article, ner)
    comp_names = sorted(companies)
    for pair in entity_pair:
        (entity1, entity2) = pair
        if len(entity1) < len(entity2):
            companies[entity1] += companies[entity2]
        else:
            companies[entity2] += companies[entity1]
    for comp in comp_names:
        if comp in news_title:
            if all_comps and comp_pairs:
                return (comp, companies, entity_pair)
            elif all_comps:
                return (comp, companies)
            elif comp_pairs:
                return (comp, entity_pair)
            else:
                return comp
    comp = ''
    # if len(companies) > 0:
    s_comps = sorted(companies, key=companies.__getitem__)
    while len(s_comps) > 0:
        comp = s_comps.pop()
        if comp not in financial_terms and not comp.endswith('Journal'):
            break
    if all_comps and comp_pairs:
        return (comp, companies, entity_pair)
    elif all_comps:
        return (comp, companies)
    elif comp_pairs:
        return (comp, entity_pair)
    else:
        return comp


def search_existing_company(article, ner):
    companies = dict()
    entity_pair = []
    for j in xrange(0, len(article)):
        sen = article[j]
        sen_ner = ner[j]
        for searched_company in search_tag(sen, 'ORGANIZATION', sen_ner):
            if searched_company != '':
                if searched_company in special_terms:
                    pass
                elif searched_company not in companies:
                    companies[searched_company] = 1
                else:
                    companies[searched_company] += 1
    comp_names = sorted(companies)
    for ii in xrange(0, len(comp_names)):
        for jj in xrange(ii + 1, len(comp_names)):
            if comp_names[ii] in comp_names[jj]:
                entity_pair.append((comp_names[ii], comp_names[jj]))
            else:
                break
    logging.info('Find mentioned companies - Entity pair:', entity_pair)
    return companies, entity_pair


def write_demo(demo_writer, article, ner, news_title, news_time, ner_tag=None, sen_tag=None, article_tag=None):
    # Explanation: sen_tag = {'event':[Sen_ids]}, article_tag = [event_tags],
    # ner_tag = [tags need color], default is display all tags
    ner_color = {'location': 'yellow', 'organization': '#33CC99', 'person': '#9966FF', 'number': '#FF00CC'}
    sen_color = {'IPO': '#99CCFF', 'Layoff': '#FF99FF', 'Investment': '#FF6633'}
    # Preprocess sen_tag
    tmp = []
    for tag in sen_tag:
        if len(sen_tag[tag]) > 0:
            sen_tag[tag] = [int(i.split('@')[1]) for i in sen_tag[tag]]
        else:
            tmp.append(tag)
    for tag in tmp:
        del sen_tag[tag]

    # Generate HTML
    head = ''
    body = ''
    head += '<!DOCTYPE html>\n<head><meta charset="UTF-8"><style>'
    # Define Style for NER and event tag
    if ner_tag != None:
        for key in ner_tag:
            key = key.lower()
            head += '.{} {{background-color: {};}}\n'.format(key, ner_color[key])
            # Write color map of NER
            body += '<span class = \'{}\'>{}</span>\t'.format(key, key.upper())
    if sen_tag != None:
        for key in sen_tag:
            head += '.{} {{background-color: {};}}\n'.format(key, sen_color[key])
            # Write color map of event tag
            body += '<span class = \'{}\'>{}</span>\t'.format(key, key.upper())
    # o.write('#stanford {width: 50%; display: inline-block; margin: auto;}\n')
    # o.write('#improve {width: 50%; display: inline-block; margin: auto; float:right;}\n')
    head += '</style></head><body>\n'

    # Writing News Content
    body += '<div>\n'
    body += '<h4>{}</h4>'.format(news_title)
    body += '<p id=\'time\'>{}</p>'.format(news_time.split(' ')[0])
    if article_tag != None:
        body += '<p id=\'article_tag\' >Tags:\t{}</p>'.format('; '.join(article_tag))
    for j in xrange(0, len(article)):
        # Generate NER meta
        ner_indices = [a for a in search_tag(article[j], 'O', ner[j], index=True)]
        meta_indices = [''] * (len(article[j]) + 1)
        for ner_index in ner_indices:
            (s_index, e_index, tag) = ner_index
            meta_indices[s_index] += '<span class=\'{}\'>'.format(tag.lower())
            meta_indices[e_index] += '</span>'
        sen_meta = ''
        for tag in sen_tag:
            if j in sen_tag[tag]:
                if sen_meta == '':
                    sen_meta = 'class = "{}"'.format(tag)
                else:
                    sen_meta = sen_meta.strip('"') + ' ' + tag + '"'
        body += '<p ' + sen_meta + '>'
        for ii in xrange(0, len(article[j])):
            body += meta_indices[ii] + article[j][ii].replace('-LRB-', '(').replace('-RRB-', ')') + ' '
        body += '</p>\n'
    body += '</div>\n</body>\n</html>'

    demo_writer.write(head + body)



def article_metadata(event_score, event_info, entity_pair):
    metadata = set()
    for event in event_score:
        if event_score[event] >= 1.5:
            metadata.add(event)
    for info in event_info:
        comp = info.split(sp)[0]
        for pair in entity_pair:
            if comp in sp.join(list(pair)):
                comp = pair[0]
        if comp != 'None':
            metadata.add(comp)
    return list(metadata)


def convert_date(news_time, date):
    if date in date_indice.keys():
        if date_indice[date] < 0:
            return (1, news_time)
        else:
            dt = datetime.strptime(news_time, "%Y-%m-%d")
            td = timedelta(days=date_indice[date] - dt.isoweekday())
            dt += td
            if dt.strftime('%Y-%m-%d') < news_time:
                return -1,dt.strftime('%Y-%m-%d')
            else:
                return 1,dt.strftime('%Y-%m-%d')
    elif len(date.split(' ')) > 1 and date.split(' ')[0].strip('.') in months and re.compile(
            '^[1-9]$|^0[1-9]$|^[1-2][0-9]$|^3[0-1]$').match(date.split(' ')[1]):
        date = date.replace(', ', '')
        if (len(date.split(' '))) == 3:
            month, day, year = date.split(' ')
            try:
                if int(year) >= 1990:
                    dt = datetime.strptime('{}-{}-{}'.format(year, month[:3], day), "%Y-%b-%d")
                    if dt.strftime('%Y-%m-%d') < news_time:
                        return -1,dt.strftime('%Y-%m-%d')
                    else:
                        return 1,dt.strftime('%Y-%m-%d')
            except ValueError:
                logging.debug('Error:\t cannot convert date for {}'.format(date))
                if 'last' in date or 'ago' in date:
                    return -1,'{} ({})'.format(date, news_time)
                else:
                    return 1,'{} ({})'.format(date, news_time)
        else:
            year = news_time.split('-')[0]
            month, day = date.split(' ')
            dt = datetime.strptime('{}-{}-{}'.format(year, month[:3], day), "%Y-%b-%d")
            if dt.strftime('%Y-%m-%d') < news_time:
                return -1,dt.strftime('%Y-%m-%d')
            else:
                return 1,dt.strftime('%Y-%m-%d')
    elif len(date) >= 3 and date.strip('.') in months:
        year = news_time.split('-')[0]
        dt = datetime.strptime('{}-{}'.format(year, date[:3]), "%Y-%b")
        if dt.strftime('%Y-%m-%d') < news_time:
            return -1,dt.strftime('%Y-%m-%d')
        else:
            return 1,dt.strftime('%Y-%m-%d')
    else:
        if 'last' in date or 'ago' in date:
            return -1,'{} ({})'.format(date, news_time)
        else:
            return 1,'{} ({})'.format(date, news_time)