import re
from event.event_info import financial_terms, intention_flags, sp
from utils.help_func import search_word, search_tag, convert_date, match_substring
import logging


class IPO_Search(object):
    ipo_keywords = ["initial public offering", 'IPO',"initial public stock offering", "go public","public offering",
                    "SEC", "Securities and Exchange Commission"]
    event_priority = {'Withdraw': 7, 'Delay': 6, 'Trade': 5.5, 'File': 5.4, 'Price': 5.3, 'Upcoming': 5, 'Intention': 0,
                      None: -1}
    stock_codes = ["NYSE", "NASDAQ", "New York Stock Exchange", "Nasdaq"]

    def __init__(self, doc_id, topic_company, nlp_info, news_title, news_time):
        self.topic_company = topic_company
        self.company_ipo_score = 0
        self.ipo_ticker = []
        self.sen_tags = {'Intention': [], 'File': [], 'Price': [], 'Withdraw': [], 'Delay': [], 'Trade': [],
                         'Upcoming': []}
        self.event_time = []
        self.ipo_price = []
        self.ipo_fund = []
        self.logger = logging.getLogger('IPO_detect')
        self.nlp_info, self.news_title, self.news_time = nlp_info, news_title, news_time
        self.logger.setLevel(logging.DEBUG)
        self.logger.info('IPO event detection initialized for doc %d' % doc_id)



    def detect_ipo(self):
        # FOR EACH SENTENCE IN DOC, DETECT IPO KEYWORD AND IPO INFO
        for j in xrange(len(self.nlp_info['word'])):
            # GET PREPROCESS NLP INFO
            sen_id = self.nlp_info['sen_id'][j]
            sen = self.nlp_info['word'][j]
            sen_lemma = self.nlp_info['lemma'][j]
            sen_ner = self.nlp_info['ner'][j]
            sen_entity = self.nlp_info['entity'][j]
            sen_pos = self.nlp_info['pos'][j]
            sen_ipo_status = None

            # search IPO keywords from sentence
            ipo_tag, comp_ipo_score = self.search_ipo_keywords(sen_id, sen, sen_lemma, sen_pos, sen_entity )
            if ipo_tag != None:
                self.company_ipo_score += comp_ipo_score
            if IPO_Search.event_priority[ipo_tag] > IPO_Search.event_priority[sen_ipo_status]:
                sen_ipo_status = ipo_tag

            # search company ticker
            for comp_ticker in self.match_comp_ticker(sen_id, sen, sen_lemma, sen_ner, sen_entity):
                (searched_ticker, comp_ipo_score) = comp_ticker
                self.ipo_ticker.append(searched_ticker+'~^~'+sen_id)
                # Only topic company in the searched ticker info (comp_ipo_score > 0),
                # will the sen_ipo_status be updated
                if comp_ipo_score != 0:
                    ipo_tag = 'Upcoming'
                    self.company_ipo_score += comp_ipo_score
                    if IPO_Search.event_priority[ipo_tag] > IPO_Search.event_priority[sen_ipo_status]:
                        sen_ipo_status = ipo_tag

            # match begin trading pattern
            comp_ipo_score, ipo_tag = self.search_trade_info(sen_id, sen, sen_lemma, sen_ner, sen_entity)
            if ipo_tag != None:
                self.company_ipo_score += comp_ipo_score
                if IPO_Search.event_priority[ipo_tag] > IPO_Search.event_priority[sen_ipo_status]:
                    sen_ipo_status = ipo_tag

            # match stock price range
            comp_prices = list(self.search_stock_price(sen_id, sen, sen_lemma, sen_ner, sen_entity))
            if len(comp_prices) > 0:
                if 'sold' in sen and 'million' in sen and 'shares' in sen:
                    ipo_tag = 'Trade'
                    if IPO_Search.event_priority[ipo_tag] > IPO_Search.event_priority[sen_ipo_status]:
                        sen_ipo_status = ipo_tag
                else:
                    ipo_tag = 'Price'
                    if IPO_Search.event_priority[ipo_tag] > IPO_Search.event_priority[sen_ipo_status]:
                        sen_ipo_status = ipo_tag
                for comp_price in comp_prices:
                    self.ipo_price.append(comp_price+'~^~'+sen_id)

            # search event date
            if sen_ipo_status != None and sen_ipo_status != 'Intention':
                dates = self.search_date(sen_id, sen, sen_lemma, sen_ner)
                # If cannot found particular date in the sentence, use the news date instead and mark it with '#'
                if len(dates) == 0:
                    self.event_time.append('{}~^~{}~^~{}#~^~{}'.format(self.topic_company,sen_ipo_status, self.news_time, sen_id))
                else:
                    for date in dates:
                        t, updated_date = convert_date(self.news_time, date)
                        self.event_time.append('{}~^~{}~^~{}~^~{}'.format(self.topic_company, sen_ipo_status, updated_date,sen_id))
                # only if the sentence is marked with ipo related, search any fund raising info
                for comp_price_confid in self.search_raise_fund(sen_id, sen, sen_lemma, sen_ner, sen_entity):
                    self.ipo_fund.append(comp_price_confid+'~^~'+sen_id)

            if sen_ipo_status != None:
                self.sen_tags[sen_ipo_status].append(sen_id)

        return self.summary()


    def search_ipo_keywords(self, sen_id, sen, sen_lemma, sen_pos, sen_entity):
        sen_tag = None
        comp_ipo_score = 0
        keyword_l = []
        intention_l = []
        for ipo_keyword in IPO_Search.ipo_keywords:
            for index in search_word(ipo_keyword,sen_lemma):
                keyword_l.append((index,ipo_keyword))

        for intention in intention_flags:
            for index in search_word(intention,sen_lemma):
                intention_l.append((index,intention))

        for word_i,keyword in keyword_l:
            sen_tag = 'Upcoming'
            for intent_i,intention in intention_l:
                if intent_i <= word_i + intention_flags[intention][1] and intent_i >= word_i - intention_flags[intention][0]:
                    sen_tag = 'Intention'
                else:
                    comp_ipo_score += 1

        if sen_tag == None and 'offering' in sen and 'shares' in sen:
            sen_tag = 'IPO_related'

        if sen_tag != 'Intention' and sen_tag != None:
            if 'cancel' in sen_lemma or 'withdraw' in sen_lemma or 'withdrawl' in sen_lemma:
                sen_tag = 'Withdraw'
            elif 'delay' in sen_lemma or 'postpone' in sen_lemma:
                sen_tag = 'Delay'
            elif 'debut' in sen and 'to debut' not in ' '.join(sen) or 'debuted' in sen:
                sen_tag = 'Trade'
            elif 'raised' in sen:
                sen_tag = 'Trade'
            elif 'went public' in ' '.join(sen) or 'completed' in ' '.join(sen):
                sen_tag = 'Trade'
            elif 'file' in sen_lemma or 'filling' in sen_lemma or 'registered' in sen:
                sen_tag = 'File'

        if sen_tag == 'IPO_related':
            sen_tag = None

        return sen_tag, comp_ipo_score


    def match_comp_ticker(self, sen_id, sen, sen_lemma, sen_ner, sen_entity):
        comp_ipo_score = 0
        for stock_code in IPO_Search.stock_codes:
            if stock_code in ' '.join(sen):
                searched_ticker = self.search_ticker(sen_id, sen, sen_ner, stock_code)
                if searched_ticker == '':
                    continue
                elif searched_ticker.startswith(sp):
                    entities = [comp for comp in search_tag(sen, 'O', sen_entity)]
                    if len(entities) > 0:
                        searched_ticker = entities[0] + searched_ticker
                    elif self.topic_company in ' '.join(sen):
                        searched_ticker = self.topic_company + searched_ticker
                    else:
                        self.logger.debug(
                            'Error:\t|ipo_detect\tmatch_comp_ticker|\tNo match company for {}. \t|{}\n'.format(
                                searched_ticker, sen_id))
                        searched_ticker = 'None' + searched_ticker
                com_name = searched_ticker.split(sp)[0]
                if match_substring(com_name, self.topic_company):
                    (intention, confid) = self.search_intention(sen_id, sen, sen_lemma)
                    if intention == 'IPO':
                        print 'Find ticker | {} | in sentence{} for target company {}:\tget 1 score for IPO.'.format(
                            searched_ticker, sen_id, self.topic_company)
                        comp_ipo_score += 1
                    else:
                        searched_ticker += '*'
                yield (searched_ticker, comp_ipo_score)


    def search_trade_info(self, sen_id, sen, sen_lemma, sen_ner, sen_entity):
        comp_ipo_score, ipo_tag = 0, None
        if 'trad' in sp.join(sen_lemma):
            # eleminate the intention sentence
            if re.compile("^.*(will|could|would|to)~\^~(\w{,7}~\^~)*trade").match(sp.join(sen_lemma)) != None:
                return 1,'Upcoming'
            if re.compile('.*(open|begin|start)~\^~(.*~\^~){,1}(trade|trading)~\^~(.*~\^~){,1}(on|at).*').match(sp.join(sen_lemma)) != None:
                comp_candidate = [comp for comp in search_tag(sen, 'ORGANIZATION', sen_ner) if comp not in financial_terms]
                if len(comp_candidate) > 0:
                    for comp in comp_candidate:
                        if match_substring(comp, self.topic_company):
                            comp_ipo_score += 1
                            ipo_tag = 'Trade'
                            print 'Find IPO keyword | {} | in sentence{} for target company {}:\tget 1 score for IPO'.format(
                                'Begin Trade', sen_id, self.topic_company)
                            break
                elif self.topic_company in ' '.join(sen_entity):
                    comp_ipo_score += 1
                    ipo_tag = 'Trade'
                    print 'Entity linked:'
                    print 'Find IPO keyword | {} | in sentence{} for target company {}:\tget 1 score for IPO'.format(
                        'Begin Trade', sen_id, self.topic_company)

        return comp_ipo_score, ipo_tag


    def search_ticker(self, sen_id, sen, sen_ner, stock_code):
        start = 0
        index_flag = 0
        keywords = ['ticker', 'symbol']
        com_candidates = [company for company in search_tag(sen, 'ORGANIZATION', sen_ner)]
        flag = False
        symbol_code = ''
        if '-LRB- {} :'.format(stock_code) in ' '.join(sen):
            symbol_code = sen[sen.index('-RRB-') - 1]
            try:
                search_index = com_candidates.index(stock_code)
                if com_candidates.index(stock_code) > 0:
                    return '{}~^~{}~^~0.9'.format(com_candidates[search_index - 1], symbol_code)
                else:
                    self.logger.debug(
                        'Error\t: NER should have company before -LRB- {} : -RRB-.\t|{}\n'.format(stock_code, sen_id))
                    return '{}~^~{}~^~0.75'.format(sen[sen.index('-LRB-') - 1], symbol_code)
            except:
                self.logger.debug("Error: \t {} is not in the company list.\t|{}\n".format(stock_code, sen_id))
        for keyword in keywords:
            try:
                start = sen.index(keyword)
                index_flag = ' '.join(sen).index(keyword)
                break
            except ValueError:
                pass
            #   if start == 0:
            #       start = sen.index(stock_code)
        if start == 0:
            index_flag = ' '.join(sen).index(stock_code)

        symbol_code_distance = len(' '.join(sen))
        for ii in xrange(start + 1, len(sen)):
            if re.compile('^[A-Z]+$').match(sen[ii]) != None and sen[ii] not in financial_terms:
                flag = True
                if symbol_code_distance > abs(' '.join(sen).index(sen[ii]) - index_flag):
                    symbol_code = sen[ii]
                    symbol_code_distance = abs(' '.join(sen).index(sen[ii]) - index_flag)
        if flag:
            try:
                search_index = com_candidates.index(stock_code)
                if search_index > 0:
                    # print com_candidates[com_candidates.index(stock_code)-1],symbol_code
                    if com_candidates[search_index - 1] in financial_terms:
                        return '~^~{}~^~0.5'.format(symbol_code)
                    return '{}~^~{}~^~0.8'.format(com_candidates[search_index - 1], symbol_code)
                else:
                    # print stock_code,symbol_code
                    return '~^~{}~^~0.5'.format(symbol_code)
            except ValueError:
                self.logger.debug(
                    "Error:\t |ipo_detect\tsearch_ticker|\t{} is not in the company list.\t|{}\n".format(stock_code,
                                                                                                         sen_id))

        return ''


    def search_stock_price(self, sen_id, sen, sen_lemma, sen_ner, sen_entity):
        comps = [comp for comp in search_tag(sen, 'ORGANIZATION', sen_ner) if comp not in financial_terms]
        entities = [comp for comp in search_tag(sen, 'O', sen_entity)]
        if 'MONEY' in sen_ner:
            for (index, money) in search_tag(sen, 'MONEY', sen_ner, index=True):
                if money.endswith('illion'):
                    continue
                if re.compile('^between \$ [0-9]+ and \$ [0-9]+$').match(' '.join(sen[index - 4:index + 2])):
                    continue
                if re.compile('^between \$ [0-9]+ and \$ [0-9]+$').match(' '.join(sen[index - 1:index + 5])):
                    money_range = ' '.join(sen[index - 1:index + 5])
                    comp_candidate = self.search_comp_with_flag(sen, sen_lemma, sen_entity, comps, entities, money_range,
                                                           stem=False)
                    if comp_candidate != None:
                        yield sp.join([comp_candidate, money_range])
                    else:
                        self.logger.debug(
                            'Error:\t |ipo_detect\tsearch_stock_price|\tCannot find company to match price {}.\t|{}\n'.format(
                                money_range, sen_id))
                elif re.compile('.*(price|sell)~\^~([a-zA-Z0-9]*~\^~){,5}at.*').match(sp.join(sen_lemma)):
                    flag_word = 'price' if 'price' in ' '.join(sen_lemma) else 'sell'
                    if ' '.join(sen_lemma).index(flag_word) < ' '.join(sen_lemma).index(money):
                        comp_candidate = self.search_comp_with_flag(sen, sen_lemma, sen_entity, comps, entities, flag_word,
                                                                    stem=False)
                        if comp_candidate != None:
                            yield sp.join([comp_candidate, money])
                        else:
                            self.logger.debug(
                                'Error:\t |ipo_detect\tsearch_stock_price|\tCannot find company to match price {}.\t|{}\n'.format(
                                    money, sen_id))
                elif 'per share' in ' '.join(sen) and (' '.join(sen).index(money) < ' '.join(sen).index('per share')):
                    comp_candidate = self.search_comp_with_flag(sen, sen_lemma, sen_entity, comps, entities, 'per', stem=False)
                    if comp_candidate != None:
                        yield sp.join([comp_candidate, money])
                    else:
                        self.logger.debug(
                            'Error:\t |ipo_detect\tsearch_stock_price|\tCannot find company to match price {}.\t|{}'.format(
                                money, sen_id))
                elif 'stock' in sen and 'price' in sen:
                    comp_candidate = self.search_comp_with_flag(sen, sen_lemma, sen_entity, comps, entities, sen[index])
                    if comp_candidate != None:
                        yield sp.join([comp_candidate, money])
                    else:
                        self.logger.debug(
                            'Error:\t |ipo_detect\tsearch_stock_price|\tCannot find company to match price {}.\t|{}'.format(
                                money, sen_id))


    def search_raise_fund(self, sen_id, sen, sen_lemma, sen_ner, sen_entity, sen_ipo_tags=None):
        comps = [comp for comp in search_tag(sen, 'ORGANIZATION', sen_ner) if comp not in financial_terms]
        entities = [comp for comp in search_tag(sen, 'O', sen_entity)]
        if 'MONEY' in sen_ner:
            for (index, money) in search_tag(sen, 'MONEY', sen_ner, index=True):
                if money.endswith('illion'):
                    confi = 0.2
                    comp_candidate = self.search_comp_with_flag(sen, sen_lemma, sen_entity, comps, entities, money, stem=False)
                    if sen_ipo_tags == None:
                        confi += 0.15
                    elif sen_id in sen_ipo_tags:
                        confi += 0.3
                    if 'file' in sen_lemma and sen_lemma.index('file') > index:
                        confi += 0.2
                        comp_candidate = self.search_comp_with_flag(sen, sen_lemma, sen_entity, comps, entities, 'file')
                    elif 'raise' in sen_lemma:
                        confi += 0.1
                        if ' '.join(sen_lemma).index('raise') < ' '.join(sen_lemma).index(money):
                            comp_candidate = self.search_comp_with_flag(sen, sen_lemma, sen_entity, comps, entities, 'raise')
                        elif 'raise by' in ' '.join(sen_lemma):
                            comp_candidate = self.search_comp_with_flag(sen, sen_lemma, sen_entity, comps, entities, 'raise',
                                                                       dirc=1)
                    if comp_candidate != None:
                        yield sp.join([comp_candidate, money, str(confi)])
                    else:
                        self.logger.debug(
                            'Error:\t |ipo_detect\tsearch_raise_fund|\tCannot find company to match price {}.\t|{}\n'.format(
                                money, sen_id))
        # Count stock share
        elif 'shares' in sen and 'NUMBER' in sen_ner:
            for (index, number) in search_tag(sen, 'NUMBER', sen_ner, index=True):
                position = sen.index('shares')
                if index < position and position - index <= 4:
                    comp_candidate = self.search_comp_with_flag(sen, sen_lemma, sen_entity, comps, entities, number)
                    confi = 0.7
                    if comp_candidate != None:
                        yield sp.join([comp_candidate, number+' shares', str(confi)])
                    else:
                        self.logger.debug(
                            'Error:\t |ipo_detect\tsearch_raise_fund|\tCannot find company to match stock share {}.\t|{}\n'.format(
                                number+' shares', sen_id))



    def search_comp_with_flag(self, sen, sen_lemma, sen_entity, comps, entities, flag, stem=True, dirc=-1):

        if stem:
            stemmed_flag = flag[:-1]
        else:
            stemmed_flag = flag
        if dirc == -1:
            comp_index = len(comps) - 1
            while comp_index >= 0:
                if ' '.join(sen).index(comps[comp_index]) < ' '.join(sen_lemma).index(stemmed_flag):
                    # print comps[comp_index],
                    return comps[comp_index]
                comp_index -= 1
        else:
            comp_index = 0
            while comp_index < len(comps):
                if ' '.join(sen).index(comps[comp_index]) > ' '.join(sen_lemma).index(stemmed_flag):
                    return comps[comp_index]
                comp_index += 1
        if comp_index < 0 or comp_index == len(comps):
            for entity in set(entities):
                if dirc == -1 and sen_entity.index('B-' + entity) < ' '.join(sen_lemma).index(flag):
                    return entity
                if dirc == 1 and ' '.join(sen).index(comps[comp_index]) > ' '.join(sen).index(stemmed_flag):
                    return entity
        return None


    def search_date(self, sen_id, sen, sen_lemma, sen_ner, keyword=None, dirc=None):
        date_candidates = [date for date in search_tag(sen, 'DATE', sen_ner)]
        if 'morning' in ' '.join(sen_lemma):
            date_candidates.append('morning')
        elif 'afternoon' in ' '.join(sen_lemma):
            date_candidates.append('afternoon')
        if keyword != None:
            if dirc == None:
                self.logger.debug(
                    'Error:\t |ipo_detect\tsearch_date|\tNeed search dirction for search keyword {}\n'.format(keyword))
            elif dirc > 0:
                for date in date_candidates:
                    if ' '.join(sen_lemma).index(keyword) > ' '.join(sen_lemma).index(date):
                        date_candidates.remove(date)
            else:
                for date in date_candidates:
                    if ' '.join(sen_lemma).index(keyword) < ' '.join(sen_lemma).index(date):
                        date_candidates.remove(date)


        return date_candidates


    def search_intention(self, sen_id, sen, sen_lemma):
        confid = 1
        intent = 'IPO'
        for flag in sorted(intention_flags, key=intention_flags.__getitem__):
            if flag in ' '.join([lemma.decode('utf-8') for lemma in sen_lemma]):
                intent = True
                confid = intention_flags[flag]
                if confid <= -1:
                    intent = 'Withdrawl'
                elif confid < 0:
                    intent = 'Delay'
                else:
                    intent = 'Intention'
                print 'Intention:\t', ' '.join(sen)
                return (intent, confid)
        # print 'IPO:\t{}\t{}'.format(sen_id,' '.join(sen_lemma))
        return (intent, confid)


    def summary(self):
        ipo_label = None
        # ipo_score is used to evaluated the topic relevance of IPO
        ipo_score = 0
        # PROCESS AND GENERATING EVENT LABEL FOR DOCUMENT
        for label in self.sen_tags:
            ipo_score += len(self.sen_tags[label])
            if len(self.sen_tags[label]) > 0:
                if IPO_Search.event_priority[label] > IPO_Search.event_priority[ipo_label]:
                    ipo_label = label

        # CORRECTION:
        # If the status tag is upcoming but there is not any ipo price, ipo ticker or fund info,
        # assume the news to be ipo intention instead of upcoming ipo event
        if ipo_label == 'Upcoming' and len(self.ipo_price) == 0 and len(self.ipo_fund) == 0:
            is_intention = True
            for ticker in self.ipo_ticker:
                if self.topic_company in ticker:
                    is_intention = False
            if is_intention:
                ipo_label = 'Intention'

        # USING TITLE INFO TO CORRECT LABEL
        if 'prices IPO' in self.news_title and ipo_label != 'Price':
            ipo_label = 'Price*'
        if 'files' in self.news_title and ipo_label != 'File':
            ipo_label = 'File*'

        # summarize event information from snippet information collected from sentence
        event_info = {'ipo_status': ipo_label,
                      'event_time': [],
                      'stock_price': [],
                      'fund_info': [],
                      'trade_ticker': []}

        if ipo_label is not None:
            ipo_label = ipo_label.strip('*')
        if ipo_score > 0:
            # event time info summary
            for date_info in self.event_time:
                (comp, event, date, sen_id) = date_info.split(sp)
                if event == ipo_label:
                    if '(' not in date and '#' not in date:
                        # remove date which is not accurate or estimated
                        while len(event_info['event_time']) > 0 and \
                        ('(' in event_info['event_time'][-1]['time'] or '#' in event_info['event_time'][-1]['time']):
                            event_info['event_time'].pop()
                        event_info['event_time'].append({'company': comp, 'event': 'ipo_'+event, 'sen_id': sen_id,
                                                         'time': date})
                    else:
                        # find any existing date which is more accurate than this date,
                        # if yes, ignore this date
                        flag = False
                        for candidate in event_info['event_time']:
                            if '(' not in candidate['time'] and '#' not in candidate['time']:
                                flag = True
                        # if not, append this date
                        if not flag:
                            event_info['event_time'].append({'company': comp, 'event': 'ipo_'+event, 'sen_id': sen_id,
                                                             'time': date})
            # IPO STOCK PRICE
            for comp_price in self.ipo_price:
                (comp, price, sen_id) = comp_price.split(sp)
                event_info['stock_price'].append({'company': comp, 'stock_price': price, 'sen_id': sen_id})

            # IPO FUNDING OR STOCK SHARE
            for comp_fund_confid in self.ipo_fund:
                (comp, fund, confid, sen_id) = comp_fund_confid.split(sp)
                event_info['fund_info'].append({'company': comp, 'fund/share': fund, 'sen_id': sen_id})

            # IPO TICKER
            for ticker in self.ipo_ticker:
                (comp, ticker, confid, sen_id) = ticker.split(sp)
                event_info['trade_ticker'].append({'company': comp, 'ticker': ticker, 'sen_id': sen_id})
        else:
            print 'This article is recognized not containing any company IPO,since the point for IPO is {}'.format(
                ipo_score)
        return event_info