sp = '~^~'


def word_depen(dependency_str):
    # depen_info = dependency_str.replace('(',sp).replace(')',sp).replace(', ',sp).split(sp)
    # depen_info.remove('')
    depen_info = dependency_str.split('@')
    if len(depen_info) == 3:
        (tag, word_index1, word_index2) = depen_info
        #	index1 = int(word_index1.split('-')[-1]) - 1
        #	index2 = int(word_index2.split('-')[-1]) - 1
        index1 = int(word_index1)
        index2 = int(word_index2)
        return (tag, index1, index2)
    else:
        return None


def sen_depen(dependencies, length, reverse=False):
    depens = {i: [] for i in xrange(-1, length)}
    for depend in dependencies:
        if depend != None:
            (tag, dep_index, word_index) = depend
            if reverse:
                depens[word_index].append((dep_index, tag))
            else:
                depens[dep_index].append((word_index, tag))
    if depens:
        return depens
    else:
        return None


def dep_repr_tree_str(dependencies, sentence):
    node_stack = [(0, tmp) for tmp in dependencies[-1]]
    dep_str = ''
    last_dep = -1
    while len(node_stack) > 0:
        node = node_stack.pop()
        (dep, (next_node, tag)) = node
        if last_dep >= dep:
            dep_str += ')' * (last_dep - dep + 1)
        dep_str += '(' + sentence[next_node] + '-' + tag
        dependencies[next_node] = sorted(dependencies[next_node], key=lambda node: node[0], reverse=True)
        n_nodes = [(dep + 1, tmp) for tmp in dependencies[next_node]]
        node_stack.extend(n_nodes)
        last_dep = dep
    dep_str += ')' * (last_dep + 1)
    return dep_str


# Below  ---- > OUT OF DATE
def depen_structure(dependencies, key_index, tag):
    dep_tree = []
    for (dep_index, tag) in dependencies[key_index]:
        sub_tree = depen_structure(dependencies, dep_index, tag)
        if len(sub_tree) > 0:
            dep_tree.append((tag, dep_index, sub_tree))
        else:
            dep_tree.append((tag, dep_index))
    return dep_tree


def repr_tree(depends, dep, sen):
    tree_str = ''
    for node in depends:
        for i in xrange(0, dep):
            print '\t',
        if len(node) == 3:
            (tag, index, sub_tree) = node
            if len(sub_tree) > 1:
                print '{} {}:{} {}'.format(dep, tag, index, sen[index])
            else:
                print '{} {}:{} {}'.format(dep, tag, index, sen[index]),
            repr_tree(sub_tree, dep + 1, sen)
        else:
            (tag, index) = node
            print '{} {}:{} {}'.format(dep, tag, index, sen[index])
    return tree_str
