import re
from Queue import Queue
from itertools import combinations
from copy import deepcopy


class Sentence:
    def __init__(self, original):
        self.og = original
        self.literals = original.replace(" ", "").split("|")

    def toString(self):
        return " | ".join(self.literals)


def readfile(filename):
    file_input = open(filename, 'r')
    i = 1
    nQuery, nSentences = 0, 0
    queries = Queue()
    sentences = set()
    for line in file_input:
        if i == 1:
            nQuery = int(line.strip())
        if 2 <= i <= 1 + nQuery:
            queries.put_nowait(Sentence("~" + line.strip()))
        if i == 2 + nQuery:
            nSentences = int(line.strip())
        if 3 + nQuery <= i <= 3 + nQuery + nSentences:
            sentences.add(Sentence(line.strip()))
        i += 1
    file_input.close()
    return dict(Nq=nQuery, Ns=nSentences, Q=queries, S=sentences)


def is_variable(a):
    if type(a) == str and not a[0].isupper():
        return True
    if type(a) == list and a.__len__() == 1:
        x = a[0]
        if x.find("(") == -1 and not x[0].isupper():
            return True
    return False


def is_compound(a):
    if type(a) == list and a.__len__() == 1:
        x = a[0]
        if x.find("(") != -1:
            return True
    return False


def is_list(a):
    if type(a) == list and a.__len__() > 1:
        return True
    return False


def unify_var(var, x, tetha):
    x = x[0]
    if tetha.__contains__(var):
        return unify(tetha[var], x, tetha)
    elif tetha.__contains__(x):
        return unify(var, tetha[x], tetha)
    # elif occur_check(var,x) then return None
    else:
        tetha[var] = x
        return tetha


def split_compound(x):
    if x[0][0] == "~":
        a = x[0][1:]
    else:
        a = x[0]
    match = re.match(r"(?P<function>\w+)\s?\((?P<arg>(?P<args>\w+(,\s?)?)+)\)", a)
    d = match.groupdict()
    del d['args']
    d['arg'] = [arg.strip() for arg in d['arg'].split(',')]
    x_args = d['arg']
    x_op = d['function']
    return d


def unify(x, y, tetha):
    # xy -  a variable,constant,list or compound expression
    # tetha - a substitution built up so far,default to empty dictionary (hashtable)
    if tetha is None:
        return False
    elif x == y:
        return tetha
    elif is_variable(x):
        return unify_var(x[0], y, tetha)
    elif is_variable(y):
        return unify_var(y[0], x, tetha)
    elif is_compound(x):
        d = split_compound(x)
        x_args = d['arg']
        x_op = d['function']
        d = split_compound(y)
        y_args = d['arg']
        y_op = d['function']
        return unify(x_args, y_args, unify(x_op, y_op, tetha))
    elif is_list(x) and is_list(y):
        x_first, x_rest = x[:1], x[1:]
        y_first, y_rest = y[:1], y[1:]
        return unify(x_rest, y_rest, unify(x_first, y_first, tetha))
    else:
        return None


def has_empty(resolvent):
    for i in resolvent:
        if i == "":
            return True
    return False


def resolve(s1, s2):
    subst = unify(s1.literals, s2.literals, {})
    res = set()
    literals = deepcopy(s1.literals + s2.literals)
    #DO SUBSTITUTIONS

    for x in combinations(literals, 2):
        c1 = deepcopy(x[0])
        c2 = deepcopy(x[1])
        c1 = c1.replace("~", "")
        c2 = c2.replace("~", "")
        if c1 == c2:
            literals.remove(x[0])
            literals.remove(x[1])
        del c1, c2
    res.add(Sentence(" | ".join(literals)))
    del literals
    return res


def resolution(KB, alpha):
    KB.add(alpha)
    new = set()
    for x in combinations(KB, 2):
        resolvents = resolve(x[0], x[1])
        if has_empty(resolvents.pop().literals):
            return True
        new = new.union(resolvents)
        if new.issubset(KB):
            return False
        KB = KB.union(new)
    del KB
    return False


input_param = readfile("input1.txt")
queries, nQuery, nSentences = input_param["Q"], input_param["Nq"], input_param["Ns"]
file_output = open("output.txt", 'w')
p = set()
p.add(Sentence("Knows(John,x)"))
p.add(Sentence("Knows(y,Amy)"))

inference = resolution(p, Sentence("~Knows(John,Amy)"))
print inference
# while not queries.empty():
#     KB = deepcopy(input_param['S'])
#     inference = resolution(KB, queries.get())
#     if inference:
#         file_output.write("TRUE")
#     else:
#         file_output.write("FALSE")
#     file_output.write("\n")
# file_output.close()

# x = Sentence("American(West)").literals
# y = Sentence("~American(West) | ~Weapon(x)").literals
# print unify(x, y, {})
# print y
