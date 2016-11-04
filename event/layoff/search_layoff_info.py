from event.event_info import *
from utils.help_func import *
from nltk.stem import WordNetLemmatizer
import logging

wordnet_lemmatizer = WordNetLemmatizer()

class Layoff_Search(object):
    layoff_keywords = {"pink slip": 1, 'layoff': 1, "lay off": 1, "laid-off": 1, "job cut": 1, "severance package": 0.8,
                       "terminate": 0.3, "rebalance": 0.3, "re-balancing": 0.3, "realign": 0.3, "re-align": 0.3,
                        "restructure": 0.3}
    layoff_institutions = ["Department of Commerce", "Commerce Department", "Union", "N.C. Department of Commerce"]
    employ_words = ['worker','employee','workforce']

    def __init__(self, doc_id, nlp_info, news_title, news_time, topic_company, all_companies):
        self.logger = logging.getLogger('layoff_detect')
        self.nlp_info = nlp_info
        self.topic_company, self.all_companies = topic_company, all_companies
        self.news_time, self.news_title = news_time, news_title
        self.layoff_confid = 0
        self.layoff_sens = []
        self.layoff_infos = []
        self.logger.setLevel(logging.DEBUG)
        self.logger.info('Layoff event detection initialized for doc %d' % doc_id)

    def detect_layoff(self):

        """

        :rtype: object
        """
        title_lemma = [wordnet_lemmatizer.lemmatize(word.decode('utf-8')) for word in self.news_title.split(' ')]
        self.layoff_confid += self.search_layoff_keywords('sen_id', self.news_title.split(' '), title_lemma)
        for j in xrange(0, len(self.nlp_info['word'])):
            sen_id = self.nlp_info['sen_id'][j]
            sen = self.nlp_info['word'][j]
            sen_lemma = self.nlp_info['lemma'][j]
            sen_ner = self.nlp_info['ner'][j]
            sen_entity = self.nlp_info['entity'][j]
            sen_pos = self.nlp_info['pos'][j]
            # find any trigger word of layoff event in the sentence,
            # if any, score is larger than 0
            layoff_score = self.search_layoff_keywords(sen_id, sen, sen_lemma)
            if layoff_score != 0:
                layoff_info = [info for info in
                               self.search_layoff_info(sen_id, sen, sen_lemma, sen_ner, sen_entity) if
                               info != '']
                if len(layoff_info) > 0:
                    self.layoff_confid += layoff_score
                    self.layoff_sens.append(sen_id)
                    self.layoff_infos += layoff_info
        event_summary = self.summary()
        return event_summary
        # return self.layoff_sens, self.layoff_confid, self.layoff_infos


    def search_layoff_keywords(self, sen_id, sen, sen_lemma):
        for keyword in self.layoff_keywords:
            if keyword in ' '.join(sen) or keyword in ' '.join(sen_lemma):
                # if the keyword confidence is less than 0.5, additional info needed such as employment indicator
                if self.layoff_keywords[keyword] < 0.5:
                    for employ in self.employ_words:
                        if employ in ' '.join(sen_lemma):
                            return self.layoff_keywords[keyword]
                return self.layoff_keywords[keyword]
        return 0


    def search_layoff_info(self, sen_id, sen, sen_lemma, sen_ner, sen_entity):
        comps = [(index, comp) for (index, comp) in search_tag(sen, 'ORGANIZATION', sen_ner, index=True) if
                 comp not in financial_terms + special_journals]
        entities = [(index, comp) for (index, comp_len, comp) in search_tag(sen, 'O', sen_entity, index=True) if
                    comp not in financial_terms + special_journals]
        num_of_employ = [num for num in search_tag(sen, 'NUMBER', sen_ner, index=True)]
        layoff_date = [date for date in search_tag(sen, 'DATE', sen_ner, index=True)]
        # if any layoff info founded but no company info searched
        # iterate all companies mentioned in the article
        if (len(entities) + len(comps)) == 0 and (len(num_of_employ) + len(layoff_date)) > 0:
            for comp in self.all_companies:
                for ii in xrange(0, len(sen)):
                    if comp in sen[ii]:
                        comps.append((ii, comp))
        # if still not any company matched, considered the sentence to be a report from related department
        if (len(entities) + len(comps)) == 0:
            self.logger.info('Layoff report:\t{}\n'.format(' '.join(sen)))
        else:
            comps += entities
            for comp_index in comps:
                (index, comp) = comp_index
                (n_index, number) = self.match_pair(comp_index, num_of_employ, index=True)
                (d_index, date) = self.match_pair(comp_index, layoff_date, index=True)
                if number is not None and number.isalpha():
                    self.logger.debug(
                        'Error:\t|search_layoff_info|\tWrong Number: {}\t|{}\n'.format(number, sen_id))
                    number = None
                if d_index is not None and sen[d_index - 1] in 'from/since/until':
                    date = '{}*'.format(self.news_time)
                elif date is not None:
                    time_indicator, new_date = convert_date(self.news_time, date)
                    date = new_date
                if comp in self.layoff_institutions and len(comps) == 1:
                    self.logger.info('Layoff Institution:\t{}\n'.format(' '.join(sen)))
                elif comp not in self.layoff_institutions:
                    yield '{}~^~{}~^~{}'.format(comp, number, date)
                else:
                    continue


    def match_pair(self, target, info, index=False):
        '''
        :param target: index position of the target company
        :param info: a list of (index, word) candidates
        :param index: if True, return both index and word
        :return: (index, word) return the asserted most matched word
        '''
        distance = 10000
        ideal_pair = (None, None)
        if index:
            (t_index, t_word) = target
            for pair in info:
                (p_index, p_word) = pair
                if abs(p_index - t_index) < distance:
                    distance = p_index - t_index
                    ideal_pair = (p_index, p_word)
        return ideal_pair


    def summary(self):
        event_summary = {'layoff_status': None,
                   'event_info': []}
        if self.layoff_confid >= 1.5:
            for info in set(self.layoff_infos):
                comp,layoff_num,layoff_date = info.split(sp)
                event_summary['event_info'].append({'Company': comp, 'NumOfLayoff': layoff_num, 'DateOfLayoff': layoff_date})
        else:
            self.logger.info('This article is recognized not containing any company Layoff,'
                               'since the point for Layoff is {}'.format(self.layoff_confid))
        return event_summary
