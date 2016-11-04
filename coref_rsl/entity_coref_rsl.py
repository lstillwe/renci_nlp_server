from sen_tree_help_func import tree_position, search_b_before_a_in_sen_tree, find_first_a_in_sen_tree, update_coref_entity
from utils.depend_parse import *
from utils.help_func import search_tag, search_word
import logging

class CR(object):
    special_terms = ["NYSE", "NASDAQ", "New York Stock Exchange", "Nasdaq", "SEC", "IPO", "Wall Street",
                 "Securities and Exchange Commission", "U.S. Securities and Exchange Commission", "Renaissance Capital"]

    def __init__(self, nlp_info, topic_company, doc_id):
        self.sen_ids = nlp_info['sen_id']
        self.words = nlp_info['word']
        self.lemmas = nlp_info['lemma']
        self.ners = nlp_info['ner']
        self.pos_tags = nlp_info['pos']
        self.parse_trees = nlp_info['parse_tree']
        self.dependencies = nlp_info['dependency']
        self.topic_company = topic_company
        self.entity_coref = [[]] * len(self.words)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh = logging.FileHandler('./coref_rsl/debug.log')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        self.logger = logging.getLogger('Co-reference_Resolution')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(fh)
        self.logger.info('Co-reference Resolution initialized for doc %d' % doc_id)

    # This Function take nlp info as input and use naive approach to find any referent
    # for pronoun or definite article
    def entity_coref_rsl(self):
        # predefined pronouns and definite articles
        pds = ['it', 'its','the company', 'the business', 'the firm']
        # last_entity/last_entity_index are used to record the org entity in the subject part of prior sentence
        last_entity, last_entity_index = None, None
        # Iterate each sentence
        for j in xrange(0, len(self.words)):
            self.entity_coref[j] = ['O'] * len(self.words[j])
            # Load NLP info for each sentence and
            sen_id, sen, sen_lemma  = self.sen_ids[j], self.words[j], self.lemmas[j]
            sen_ner, sen_pos, sen_tree_str = self.ners[j], self.pos_tags[j], self.parse_trees[j]
            sen_depend = sen_depen(self.dependencies[j], len(sen), reverse=True)
            # self.logger.info('Sentence id: {} \n'.format(sen_id))
            # find all candidates companies other than special entities like journal, stock exchange institutions
            comps = [(comp_index, comp) for (comp_index, comp) in search_tag(sen, 'ORGANIZATION', sen_ner, index=True)
                     if comp not in CR.special_terms]
            # using dependency feature to find any definite articles
            # like the XXX company and add them to the preps list
            for index in search_word('the', sen):
                (dep_index, tag) = sen_depend[index][0]
                if sen[dep_index] in ['company', 'business', 'firm']:
                    new_pd = ' '.join(sen[index:dep_index + 1])
                    if new_pd not in pds:
                        pds.append(new_pd)
            for pd in pds:
                pd_indices = [index for index in search_word(pd, sen)]
                for pd_index in pd_indices:
                    if pd == 'it':
                        # Skip sentence such as 'it's + adj, it's + noun.'
                        (dep_index, tag) = sen_depend[pd_index][0]
                        if sen[dep_index + 1] in ["to", "for", "that", "about", "because"]:
                            if sen_lemma[dep_index] == 'be' or \
                                ('be' in sen_lemma[pd_index:dep_index] and
                                     (sen_pos[dep_index] == 'JJ' or sen_pos[dep_index].startswith('NN'))
                                 ):
                                # self.logger.info('"it" is not recognized as pronoun, because of it + adj or noun.\n')
                                continue
                        if ',' in sen[pd_index:]:
                            sen_tree, sen_tree_index, sen_structure = tree_position(sen_tree_str)
                            if 'SBAR' in sen_structure[pd_index]:
                                # self.logger.debug("Should find entity after pronoun/definite article {}.Sen_id:\t{}\n".
                                #                    format(pd, sen_id))
                                pass
                    # Resolve the situation when referent is supposed to locate after pronoun
                    # that is when there is ':' or '--' followed by organization entity right after the pronoun
                    flag = False
                    dash_count = 0
                    if '--' in sen[pd_index:pd_index+3] or ':' in sen[pd_index:pd_index+3]:
                        i = pd_index + 1
                        while i < len(sen) - 1:
                            if (sen[i] == ':' or (sen[i] == '--' and dash_count%2 == 0)) \
                                    and sen_ner[i+1] == 'ORGANIZATION':
                                start = i + 1
                                while i < len(sen) and sen_ner[i] == 'ORGANIZATION':
                                    i += 1
                                referent = '{}@{}@{}'.format(j, start, i)
                                update_coref_entity(pd_index, pd_index + len(pd.split(' ')), self.entity_coref[j], referent)
                                flag = True
                                if sen[i] == '--':
                                    dash_count += 1
                            i += 1
                    # if any situation above is triggered, skip this pronoun for prior organization detection
                    if flag:
                        # self.logger.info('Referent is assumed to locate after pronoun, because of ":" or "--".\n')
                        pass
                    # Code below is used to prior organization entity detection and linked with pronoun
                    (np_start, np_end, verb_index) = self.search_dominated_np_for_pd(sen_tree_str, pd_index)
                    if np_start is None:
                        pass
                        # self.logger.debug('Cannot Find directed dominated NP for pronoun {}, and assign subject entity \
                        # --{}-- of the prior sentence to this pronoun.\n'.format(pd, last_entity))
                    else:
                        # Find any org entity located in the range (np_start, np_end)
                        # in sentence or its co-reference array
                        sub_entities = [(comp_index, comp) for (comp_index, comp) in comps
                                        if comp_index <= np_end and np_start <= comp_index]
                        sub_entities += [(comp_index, comp) for (comp_index, comp_end, comp) in
                                         search_tag(self.entity_coref[j], 'O', self.entity_coref[j], index=True)
                                         if comp_index <= np_end and np_start <= comp_index]
                        # If any, get the last one, which is assumed to be nearest one to the pronoun
                        if len(sub_entities) > 0:
                            (referent_index, refer_entity) = sub_entities[-1]
                            # if '@' in refer_entity means the refer_entity is from the co-reference array,
                            # just assign its value to the referent
                            if '@' in refer_entity:
                                referent = refer_entity
                            else:
                                # entity_index format is sen_id@start_index@end_index
                                referent = '{}@{}@{}'.format(j, referent_index, referent_index + len(refer_entity.split(' ')))
                            # update referent in the co-reference array
                            update_coref_entity(pd_index, pd_index + len(pd.split(' ')), self.entity_coref[j], referent)
                            continue
                        else:
                            pass
                            # self.logger.debug('Cannot find entity for pronoun/definite article {} in dominated NP part,\
                            #  and assign subject entity --{}-- of the prior sentence to this pronoun.\n'.format(pd, last_entity))
                    # if last entity is None,
                    if last_entity is None:
                        # if the sentence is the first sentence, use topic company instead
                        if j == 0:
                            last_entity = self.topic_company
                            last_entity_index = self.topic_company + '*'
                            # self.logger.info('Last entity is None and update it with topic company (1st sentence)!\n')
                        else:
                            pre_comps = [(comp_index, comp) for (comp_index, comp) in
                                        search_tag(self.words[j-1], 'ORGANIZATION', self.ners[j-1], index=True)
                                       if comp not in CR.special_terms]
                            if len(pre_comps) > 0:
                                comp_index, last_entity = pre_comps[0]
                                last_entity_index = '{}@{}@{}'.format(j-1, comp_index, comp_index + len(last_entity.split(' ')))
                                # self.logger.info('Last entity is None and update last entity with organization \
                                # appeared in prior sentence: {}\n'.format(last_entity))
                            else:
                                # self.logger.info('Last entity is None and update it with topic company!\n')
                                last_entity = self.topic_company
                                last_entity_index = self.topic_company + '*'
                    # update referent in the co-reference array
                    update_coref_entity(pd_index, pd_index + len(pd.split(' ')), self.entity_coref[j], last_entity_index)
            # Identify new organization entity in subject of the sentence and
            # update it to be the last entity
            (new_entity_index, new_entity) = self.search_subject_entity(sen_id, sen, sen_tree_str, sen_ner, comps)
            if new_entity:
                last_entity = new_entity
                last_entity_index = '{}@{}@{}'.format(sen_id.split('@')[1], new_entity_index,
                                                      new_entity_index + len(new_entity.split(' ')))
                # self.logger.info('UPDATE LAST ENTITY to be {}\n'.format(sen_id, new_entity))

        return self.entity_coref





    def search_dominated_np_for_pd(self, sen_tree_str, pronoun_index):
        '''
        :param sen_tree_str: a string of sentence parse tree
        :param pronoun_index: the position of the pronoun in a sentence
        :return: start_index, end_index, verb_index, (start_index, end_index) is the range for dominated NP
                and verb_index to be the beginning index of verb of this sentence
        '''
        # sen_structure is 2D list, sen_structure[i] represents a path of node labels
        # from root to ith word in the sentence
        sen_tree, sen_structure_index, sen_structure = tree_position(sen_tree_str)
        # sen_structure[pronoun_index] is a list of nodes representing a path from root to the word
        start_index = None
        end_index = None
        verb_index = None
        # If VP is in the sen_structure[pronoun_index], that means the pronoun is not the subject of this sentence
        # and we can find the directly dominated NP of this pronoun to be the referent
        # otherwise, search dominated np in previous sentence to be referent instead
        # self.logger.info('----Search dominated np for pd----\n')
        if 'VP' in sen_structure[pronoun_index]:
            # if SBAR in the path, search NP under SBAR first
            if 'SBAR' in sen_structure[pronoun_index]:
                # Notice: there might be multiple VPs in the sen_structure[pronoun_index]
                # To start with the nearest parent whose label is VP
                vb_dep = list(search_word('VP', sen_structure[pronoun_index]))[-1]
                sbar_deps = reversed(list(search_word('SBAR', sen_structure[pronoun_index])))
                for sbar_dep in sbar_deps:
                    # SBAR is supposed to appear before VP
                    if sbar_dep >= vb_dep:
                        continue
                    # Start from the position of pronoun, search backward
                    # to find the starting position of SBAR to be range_index
                    # and to find the starting position of VP under SBAR to be verb_index
                    range_index = None
                    for ii in xrange(pronoun_index - 1, -1, -1):
                        if sbar_dep < len(sen_structure[ii]) and sen_structure[ii][sbar_dep] == 'SBAR':
                            if vb_dep < len(sen_structure[ii]) and 'VP' in sen_structure[ii][vb_dep:vb_dep + 3]:
                                verb_index = ii
                        else:
                            range_index = ii + 1
                            break
                    if range_index:
                        # if WHNP following SBAR, dominated NP should located prior to the range_index
                        # Otherwise the NP should located between range_index and pronoun_index
                        if sen_structure[range_index][sbar_dep + 1] == 'WHNP':
                            label = None
                            for ii in xrange(range_index - 1, -1, -1):
                                # find the first noun and update label to
                                # be the label at position min(sbar_dep - 1, len(sen_structure[ii]) - 1) of its path
                                if end_index and sen_structure[ii][-1].startswith('N'):
                                    end_index = ii + 1
                                    label = sen_structure[ii][min(sbar_dep - 1, len(sen_structure[ii]) - 1)]
                                if end_index:
                                    if len(sen_structure[ii]) <= sbar_dep - 1 or sen_structure[ii][sbar_dep - 1] != label:
                                        start_index = ii + 1
                                        break
                            if end_index and start_index is None:
                                start_index = 0
                        else:
                            for ii in xrange(range_index, pronoun_index):
                                if 'NP' in sen_structure[ii][sbar_dep + 1:sbar_dep + 3]:
                                    if start_index is None:
                                        start_index = ii
                                elif start_index:
                                    end_index = ii
                                    break
                            if start_index and end_index is None:
                                end_index = pronoun_index
                    else:
                        pass
                        # self.logger.debug('Error: No range for SBAR.\t|pronoun_index: {}\n'.format(pronoun_index))
                    break
            else:
                # Notice: there might be multiple VPs in the sen_structure[pronoun_index]
                # To start with the nearest parent whose label is VP, and search backward to find
                # any word whose NP label is at the same depth with the VP
                vp_indices = reversed(list(search_word('VP', sen_structure[pronoun_index])))
                for jj in vp_indices:
                    verb_index = find_first_a_in_sen_tree('VP', sen_structure, jj, pronoun_index)
                    (start_index, end_index) = search_b_before_a_in_sen_tree('VP', 'NP', sen_structure, jj, pronoun_index)
                    if start_index:
                        np_indices = list(search_word('NP', sen_structure[start_index]))
                        np_index = np_indices[-1]
                        for np_ii in xrange(start_index, end_index):
                            if sen_structure[np_ii][min(np_index, len(sen_structure[np_ii]) - 1)] != 'NP' and \
                                            sen_structure[np_ii][min(np_index, len(sen_structure[np_ii]) - 1)] != ',':
                                end_index = np_ii
                                break
                        break
        else:
            pass
            # self.logger.debug('Error: No VP!\t|pronoun_index: {}\n'.format(pronoun_index))
        return start_index, end_index, verb_index

    def search_subject_entity(self, sen_id, sen, sen_tree_str, sen_ner, comp_candidates):
        '''
        :param sen_id: sentence id, string
        :param sen: array of words
        :param sen_tree_str: string of parse tree for sentence,eg: (Root (S (NP I) (VP (V saw) (NP him))))
        :param sen_ner: array of ners
        :return: if any matching organization entity is founded,return its index and word, otherwise, return None,None
        '''
        # self.logger.info('----Search subject entity of sentence----\n')
        if len(comp_candidates) > 0:
            # sen_tree is built from sen_tree_str, see more info at: http://www.nltk.org/_modules/nltk/tree.html
            # An example of node index representation is shown as below:
            """
            (Root
                (S                                          -> sen_tree[0] which means the 0th child of ROOT
                  (NP                                       -> sen_tree[0,0] which means the 0th child of S -- sen_tree[0]
                    (NP (NNP SecureWorks) (NNP Inc.))       -> sen_tree[0,0,0]
                    (, ,)
                    (NP
                      (NP (DT the) (NN cybersecurity) (NN subsidiary))
                      (PP (IN of) (NP (NNP Dell) (NNP Inc.))))
                    (, ,))
                  (VP                                       -> sen_tree[0,1]
                    (VP                                     -> sen_tree[0,1,0]
                      (VBZ has)
                      (NP
                        (NP (NP (DT the) (NN year) (POS 's)) (JJ first) (NN tech))
                        (NP (JJ initial) (JJ public) (NN offering))))
                    (CC but)
                    (VP
                      (VBD had)
                      (S
                        (VP
                          (TO to)
                          (VP
                            (VB slash)
                            (NP (PRP$ its) (JJ share-price) (NNS expectations))
                            (ADVP (RB dramatically)))))))
                  (. .))
            """
            sen_tree, sen_tree_index, sen_structure = tree_position(sen_tree_str)  # Tree.fromstring(sen_tree_str)
            # d_index refers to the root position of subtree we would like to traverse to search for prep referent
            # Since the sentence parse tree always starts with 'ROOT(S(....))', that is sen_tree[0] is always 'S',
            # so we set d_index default value to be [0] to skip 'ROOT(S(..' and directly traverse children of 'S'.
            # a common example of sen_surface_labels is: ['NP', 'VP', '.']
            d_index = [0]
            sen_surface_labels = [node.label() for node in sen_tree[0]]
            # self.logger.info('{} surface labels: {}'.format(sen_id, ' '.join(sen_surface_labels)))
            # if the sentence surface structure is not the typical 'NP + VP', in general is 'S(NP VP.)' instead,
            # search in the deeper level.
            if 'NP' not in ' '.join(sen_surface_labels) and 'VP' not in ' '.join(sen_surface_labels):
                try:
                    sen_surface_labels = [node.label() for node in sen_tree[0][0]]
                    d_index.append(0)
                    # self.logger.info('{} updated surface labels:{}'.format(sen_id, ' '.join(sen_surface_labels)))
                except AttributeError:
                    # self.logger.debug('Error: Sentence structure is not compatible! ({},{})'.
                    #                      format(sen_id, ' '.join(sen_surface_labels)))
                    return None, None

            if 'VP' in sen_surface_labels and 'NP' in sen_surface_labels:
                np_index = sen_surface_labels.index('NP')
                t_index = d_index + [np_index]
                # node position index requires tuple
                np_structure = [node.label() for node in sen_tree[tuple(t_index)]]
                # self.logger.info('{}:{} '.format(sen_id, ' '.join(np_structure)))
                # According to difference sentence structure, identify the position of NP
                if ' '.join(sen_surface_labels).replace("''", '').replace("``", '') == 'S , NP VP .':
                    # self.logger.info('~ {}:{}'.format(sen_id, ' '.join(np_structure)))
                    t_index = d_index + [sen_surface_labels.index('S')]
                    search_tree = sen_tree[tuple(t_index)]
                elif ' '.join(np_structure) == 'NP , NP ,' or ' '.join(np_structure) == 'NP , SBAR ,':
                    # self.logger.info('* {}:{}'.format(sen_id, ' '.join(np_structure)))
                    t_index = d_index + [np_index, np_structure.index('NP')]
                    search_tree = sen_tree[tuple(t_index)]
                elif ' '.join(np_structure) == 'DT':
                    # self.logger.info('# {}:{}'.format(sen_id, ' '.join(np_structure)))
                    t_index = d_index + [sen_surface_labels.index('VP')]
                    search_tree = sen_tree[tuple(t_index)]
                else:
                    t_index = d_index + [np_index]
                    search_tree = sen_tree[tuple(t_index)]
                while len(comp_candidates) > 0:
                    (comp_index, comp) = comp_candidates.pop()
                    if comp in ' '.join(search_tree.leaves()):
                        return (comp_index, comp)
            elif 'VP' in sen_surface_labels:
                pass
                # self.logger.debug('Error: No NP in sentence structure! ({},{})'.format(sen_id, ' '.join(sen_surface_labels)))
            else:
                pass
                # self.logger.debug('Error: No VP in sentence structure! ({},{})'.format(sen_id, ' '.join(sen_surface_labels)))
        else:
            # Skip this sentence if none of entity is found.
            pass
            # self.logger.info('No organization detected from sentence! Sen_id: {}'.format(sen_id))
        return None, None