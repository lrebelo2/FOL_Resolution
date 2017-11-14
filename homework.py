import re
from Queue import Queue
from copy import deepcopy
from itertools import combinations


class Sentence:
    id = 0

    def __init__(self, original):
        self.og = original
        self.literals = original.replace(" ", "").split("|")
        Sentence.id += 1
        self.idi = Sentence.id

    def toString(self):
        return " | ".join(self.literals)

    def __equals__(self, s):
        if self.toString() == s.toString():
            return True
        return False

    def __hash__(self):
        return self.og.__hash__()


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


def standarize(s):
    ns = ""
    for x in s.literals:
        d = split_compound([x])
        x_args = d['arg']
        x_op = d['function']
        n = ""
        for i in x_args:
            if is_variable(i):
                i = ''.join([w for w in i if not w.isdigit()])
                i += str(s.idi)
            n = n + str(i) + ","
        n = n[:-1]

        if x[0].find("~") != -1:

            n = str("~" + x_op + "(") + n + ")"
        else:
            n = str(x_op + "(") + n + ")"
        ns += n + " | "
    ns = ns[:-3]
    s.og = ns
    s.literals = ns.replace(" ", "").split("|")


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
            s = line.strip()
            if s[0] == "~":
                s = s[1:]
                sentence = Sentence(s)
                standarize(sentence)
                queries.put_nowait(sentence)
            else:
                sentence = Sentence("~" + s)
                standarize(sentence)
                queries.put_nowait(sentence)
        if i == 2 + nQuery:
            nSentences = int(line.strip())
        if 3 + nQuery <= i <= 3 + nQuery + nSentences:
            sentence = Sentence(line.strip())
            standarize(sentence)
            sentences.add(sentence)
        i += 1
    file_input.close()
    return dict(Nq=nQuery, Ns=nSentences, Q=queries, S=sentences)


def unify_var(var, x, tetha):
    if type(x) == list:
        x = x[0]
    if type(var) == list:
        var = var[0]
    if tetha.__contains__(var):
        return unify(tetha[var], x, tetha)
    if tetha.__contains__(x):
        return unify(var, tetha[x], tetha)
    else:
        tetha[var] = x
        return tetha


def unifyR(x, y, tetha):
    t = {}
    c = deepcopy(x)
    c.extend(y)
    for a in combinations(c, 2):
        u = unify([a[0]], [a[1]], tetha)
        if u is not None:
            f = False
            for i in u:
                if t.has_key(i):
                    f = True
            if len(u) != 0 and not f:
                z = t.copy()  # start with x's keys and values
                z.update(u)  # modifies z with y's keys and values & returns None
                t = z
    del c
    if len(t) != 0:
        return t
    else:
        return None


def unify(x, y, tetha):
    # xy -  a variable,constant,list or compound expression
    # tetha - a substitution built up so far,default to empty dictionary (hashtable)
    if len(x) == 0 or len(y) == 0:
        return tetha
    elif tetha is None:
        return None
    elif x == y:
        return tetha
    elif is_variable(x):
        return unify_var(x, y, tetha)
    elif is_variable(y):
        return unify_var(y, x, tetha)
    elif is_compound(x) and is_compound(y):
        d = split_compound(x)
        x_args = d['arg']
        x_op = d['function']
        d = split_compound(y)
        y_args = d['arg']
        y_op = d['function']
        if x[0][0] == "~":
            x_neg = "~"
        else:
            x_neg = ""
        if y[0][0] == "~":
            y_neg = "~"
        else:
            y_neg = ""
        if x_op == y_op and x_neg != y_neg:
            return unify(x_args, y_args, unify(x_op, y_op, tetha))
    elif is_list(x) and is_list(y):
        x_first, x_rest = x[:1], x[1:]
        y_first, y_rest = y[:1], y[1:]
        return unify(x_rest, y_rest, unify(x_first, y_first, tetha))
    else:
        return None


def has_empty(resolvents):
    for i in resolvents:
        if len(i.literals) == 0:
            return True
        elif i.literals[0] == "":
            return True
    return False


def test(a, b):
    if a == b:
        return False
    if a[0] == "~" and b[0] != "~" and a[1:] == b:
        return True
    elif b[0] == "~" and a[0] != "~" and b[1:] == a:
        return True
    return False


def in_custom(c, KB):
    for i in KB:
        if i.og == c.og:
            return True
    return False


def pl_resolve(ci, cj):
    clauses = []
    c1 = deepcopy(ci)
    c2 = deepcopy(cj)
    for di in c1.literals:
        for dj in c2.literals:
            if test(di, dj):
                c1.literals.remove(di)
                c2.literals.remove(dj)
                d = set(c1.literals + c2.literals)
                clauses.append(Sentence(" | ".join(list(d))))
return set(clauses)


def substitute(s1, s2, subst):
    og1 = deepcopy(s1)
    og2 = deepcopy(s2)
    c1 = s1.literals
    f = False
    c2 = s2.literals
    if len(subst) != 0:
        ns1 = ""
        for x in c1:
            d = split_compound([x])
            x_args = d['arg']
            x_op = d['function']
            s = ""
            for i in x_args:
                if subst.__contains__(i):
                    if subst[i] not in x_args:
                        i = subst[i]
                    else:
                        f = True
                s = s + str(i) + ","
            s = s[:-1]
            if x[0].find("~") != -1:

                s = str("~" + x_op + "(") + s + ")"
            else:
                s = str(x_op + "(") + s + ")"
            ns1 += s + " | "
        ns1 = ns1[:-3]

        ns2 = ""
        for x in c2:
            d = split_compound([x])
            x_args = d['arg']
            x_op = d['function']
            s = ""
            for i in x_args:
                if subst.__contains__(i):
                    if subst[i] not in x_args:
                        i = subst[i]
                    else:
                        f = True
                s = s + str(i) + ","
            s = s[:-1]
            if x[0] == "~":
                s = str("~" + x_op + "(") + s + ")"
            else:
                s = str(x_op + "(") + s + ")"
            ns2 += s + " | "
        ns2 = ns2[:-3]
        return [Sentence(ns1), Sentence(ns2)]


def resolve(s1, s2, support):
    if not (in_custom(s1, support) or in_custom(s2, support)):
        return set()
    subst = unifyR(s1.literals, s2.literals, {})
    # applying substitution to sentences
    if subst is not None:
        s = substitute(s1, s2, subst)
        s1 = s[0]
        s2 = s[1]
    # resolving
    return pl_resolve(s1, s2)


def resolution(KB, alpha):
    new = set()
    support = set()
    support.add(alpha)
    iteration = 0
    max = KB.__len__() * 10
    while iteration < max:
        iteration += 1
        if iteration == 1:
            KB.add(alpha)
        for x in combinations(KB, 2):
            # x = q.get()
            ci = x[0]
            cj = x[1]
            resolvents = resolve(ci, cj, support)
            if len(resolvents) != 0:
                if has_empty(resolvents):
                    return True
                for i in resolvents:
                    if not in_custom(i, support):
                        support.add(i)
                    if not in_custom(i, new):
                        new.add(i)
        n = 0
        if len(new) != 0:
            for c in new:
                if not in_custom(c, KB):
                    n += 1
                    KB.add(c)
            if n == 0:
                return False
        else:
            return False
    return False


input_param = readfile("input.txt")
queries, nQuery, nSentences = input_param["Q"], input_param["Nq"], input_param["Ns"]
file_output = open("output.txt", 'w')

while not queries.empty():
    KBs = deepcopy(input_param['S'])
    inference = resolution(KBs, queries.get())
    print inference
    if inference:
        file_output.write("TRUE")
    else:
        file_output.write("FALSE")
    file_output.write("\n")
file_output.close()


# Testing drivers
# KBs = deepcopy(input_param['S'])
# inference = resolution2(KBs, Sentence("~H(John)"))
# print inference

# r=resolve(Sentence("~Mother(x8,y8) | Parent(x8,y8)"),Sentence("~Parent(Liz,y7) | ~Ancestor(y7,Billy)"),set())
# print 1

# KB = set()
# KB.add("a")
# KB.add("b")
# KB.add("c")
# q = comb(KB)
# new=set()
#
# comb_new(KB,new,q)
# print q.get()
#
# x = Sentence("C(x,y,z)").literals
# y = Sentence("C(y,Joe,Bob)").literals
# print unifyR(x, y, {})
# print x
# print y

# p = set()
# p.add(Sentence("Knows(John,x)"))
# p.add(Sentence("Knows(y,Amy)"))
#
# d = split_compound(["A(xy,xyz)"])
# x_args = d['arg']
# x_op = d['function']
# print x_op,x_args
