# from nltk.stem.porter import *
sp = '~^~'
# stemmer = PorterStemmer()
intention_flags = {"want": (4,2), "consider": (4,2), "hope": (4,2), "prepare": (4,2), "upcoming": (4,2), "decide": (4,2),
                   "likely": (4,2), "appear":(4,2), "expect": (4,2), "will": (4,2)}
                    #, "withdrawl":-1, "withdraw":-1, "delay":-0.5, "plan":(4,2), }
# intention_flags = {stemmer.stem(flag): intention_flags[flag] for flag in intention_flags}
stock_codes = ["NYSE", "NASDAQ", "New York Stock Exchange", "Nasdaq"]
financial_terms = stock_codes + ["SEC", "IPO","Wall Street", "Securities and Exchange Commission",
                                 "U.S. Securities and Exchange Commission", "Renaissance Capital"]
special_journals = ['Triangle Business Journal', 'Wall Street Journal']
special_terms = financial_terms + special_journals

raise_fund_keyowrds = {'raise': 0.8, 'funding round': 0.8}


date_indice = {'morning': -1, 'afternoon': -1, 'today': -1,
               'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5}
months = 'January~^~February~^~March~^~April~^~May~^~June~^~July~^~August~^~September~^~October~^~November~^~December'

ner_color = {'location': 'yellow', 'organization': '#33CC99', 'person': '#9966FF', 'number': '#FF00CC'}
sen_color = {'IPO': '#99CCFF', 'Layoff': '#FF99FF', 'Investment': '#FF6633'}




