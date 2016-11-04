from nltk.tree import Tree

def update_coref_entity(start, end, sen_coref, referent):
    for ii in xrange(start, end):
        sen_coref[ii] = 'I-' + referent
    sen_coref[start] = 'B-' + referent

def tree_position(sen_tree_str):
    sen_tree = Tree.fromstring(sen_tree_str)
    # sen_structure is 2D list, sen_structure[i] represents a path of node labels
    # from root to ith word in the sentence
    sen_structure = []
    for pos_i in sen_tree.treepositions('leaves'):
        node_labels = []
        for i in xrange(1, len(pos_i)):
            node_labels.append(sen_tree[pos_i[:i]].label())
        sen_structure.append(node_labels)
    return sen_tree, sen_tree.treepositions('leaves'), sen_structure


def search_b_before_a_in_sen_tree(a, b, sen_structure, col_index, search_index):
    start_index = None
    end_index = None
    for ii in xrange(search_index - 1, -1, -1):
        if col_index < len(sen_structure[ii]):
            if sen_structure[ii][col_index] == b:
                if end_index == None:
                    end_index = ii + 1
            elif sen_structure[ii][col_index] != a:
                if end_index != None:
                    start_index = ii + 1
                break
        else:
            if end_index != None:
                start_index = ii + 1
            break
    if end_index != None and start_index == None:
        start_index = 0
    return (start_index, end_index)


def find_first_a_in_sen_tree(a, sen_structure, col_index, search_index):
    a_index = None
    for ii in xrange(search_index - 1, -1, -1):
        if col_index < len(sen_structure[ii]) and sen_structure[ii][col_index] == a:
            continue
        else:
            a_index = ii + 1
            break
    if a_index == None:
        a_index = 0
    return a_index


"""
FUNCTION BELOW IS OUT OF DATE

def get_best_match_entity(entities, key_index, sen_structure_index):
    last_score = 0
    last_entity = None
    last_index = None
    for entity_index in entities:
        (index, entity) = entity_index
        similarity = word_structure_similarity(sen_structure_index, index, key_index)
        if similarity > last_score:
            last_entity = entity
            last_score = similarity
            last_index = index
        elif similarity == last_score and abs(last_index - key_index) > abs(index - key_index):
            last_entity = entity
            last_score = similarity
            last_index = index
    return (last_index, last_entity, last_score)

def word_structure_similarity(sen_structure, word1_index, word2_index):
    word1_structure = sen_structure[word1_index]
    word2_structure = sen_structure[word2_index]
    i = 0
    similarity = 0
    while i < len(word1_structure) and i < len(word2_structure):
        if word1_structure[i] == word2_structure[i]:
            similarity += 1
        else:
            break
        i += 1
    return similarity
"""