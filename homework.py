import re
from Queue import Queue, LifoQueue
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

    def equals(self, s):
        if self.toString() == s.toString():
            return True
        return False


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
    x = x[0]
    if tetha.__contains__(var):
        return unify(tetha[var], x, tetha)
    if tetha.__contains__(x):
        return unify(var, tetha[x], tetha)
    # elif occur_check(var,x) then return None
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
            if len(u) != 0:
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
        return unify_var(x[0], y, tetha)
    elif is_variable(y):
        return unify_var(y[0], x, tetha)
    elif is_compound(x) and is_compound(y):
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


def has_empty2(resolvents):
    for i in resolvents:
        if i.literals[0] == "":
            return True
    return False


def will_not_resolve(s1, s2):
    literals = s1.literals + s2.literals
    n1 = s1.literals.__len__()
    n2 = s2.literals.__len__()
    setl = set()
    for x in combinations(literals, 2):
        c1 = deepcopy(x[0])
        c2 = deepcopy(x[1])
        c1 = c1.replace("~", "")
        c2 = c2.replace("~", "")
        d = split_compound([c1])
        x_op = d['function']
        d = split_compound([c2])
        y_op = d['function']
        if x_op == y_op:
            return False
    return True


def test(a, b):
    if a == b:
        return False
    if a[0] == "~" and b[0] != "~" and a[1:] == b:
        return True
    if b[0] == "~" and a[0] != "~" and b[1:] == a:
        return True
    return False


def all_variables(s):
    for i in s.literals:
        d = split_compound([i])
        x_args = d['arg']
        for j in x_args:
            if not is_variable(j):
                return False
    return True


def pl_resolve(ci, cj):
    clauses = []
    c1 = deepcopy(ci)
    c2 = deepcopy(cj)
    test1=all_variables(c1)
    test2=all_variables(c2)
    if not test1 and not test2:
        for di in c1.literals:
            for dj in c2.literals:
                if test(di, dj):

                    c1.literals.remove(di)
                    c2.literals.remove(dj)
                    d = set(c1.literals + c2.literals)
                    clauses.append(Sentence(" | ".join(list(d))))
    return set(clauses)


def substitute(s1, s2, subst):
    c1 = s1.literals
    c2 = s2.literals
    if len(subst) != 0:
        ns = ""
        for x in c1:
            d = split_compound([x])
            x_args = d['arg']
            x_op = d['function']
            s = ""
            for i in x_args:
                if subst.__contains__(i):
                    i = subst[i]
                s = s + str(i) + ","
            s = s[:-1]
            if x[0].find("~") != -1:

                s = str("~" + x_op + "(") + s + ")"
            else:
                s = str(x_op + "(") + s + ")"
            ns += s + " | "
        ns = ns[:-3]
        s1.og = ns
        s1.literals = ns.replace(" ", "").split("|")
        ns = ""
        for x in c2:
            d = split_compound([x])
            x_args = d['arg']
            x_op = d['function']
            s = ""
            for i in x_args:
                if subst.__contains__(i):
                    i = subst[i]
                s = s + str(i) + ","
            s = s[:-1]
            if x[0] == "~":
                s = str("~" + x_op + "(") + s + ")"
            else:
                s = str(x_op + "(") + s + ")"
            ns += s + " | "
        ns = ns[:-3]
        s2.og = ns
        s2.literals = ns.replace(" ", "").split("|")


def resolve(s1, s2):
    subst = unifyR(s1.literals, s2.literals, {})
    # applying substitution to sentences
    if subst is not None:
        substitute(s1, s2, subst)
    # resolving
    return pl_resolve(s1, s2)
    # f = False
    # for x in combinations(literals, 2):
    #     c1 = deepcopy(x[0])
    #     c2 = deepcopy(x[1])
    #     if c1 != c2:
    #         c1 = c1.replace("~", "")
    #         c2 = c2.replace("~", "")
    #         if c1 == c2:
    #             if literals.__contains__(x[0]):
    #                 literals.remove(x[0])
    #                 f = True
    #             if literals.__contains__(x[1]):
    #                 literals.remove(x[1])
    #                 f = True
    #         del c1, c2
    #     else:
    #         if literals.__contains__(x[0]):
    #             literals.remove(x[0])
    #             f = True
    #         del c1, c2
    # if f:
    #     sentence = Sentence(" | ".join(literals))
    #     # standarize(sentence)
    #     res.add(sentence)
    #     del literals
    #     return res
    # else:
    #     del literals
    #     return set()


def comb(KB):
    q = LifoQueue()
    for x in combinations(KB, 2):
        q.put_nowait(x)
    return q


def comb_new(KB, new, q):
    if len(new) != 0:
        for i in new:
            for j in KB:
                q.put_nowait([i, j])


def in_custom(c,KB):
    for i in KB:
        if i.og == c.og:
            return True
    return False

def is_subset(a,b):
    c=0
    n=len(a)
    for i in a:
        for j in b:
            if j.og==i.og:
                c+=1
    if c>=n:
        return True
    return False

def resolution2(KB, alpha):
    new = set()
    KB.add(alpha)
    iteration = 0
    max = KB.__len__()
    # KB = list(KB)
    while iteration < max:
        iteration += 1
        # n = len(KB)
        # print n
        # pairs = [(KB[i], KB[j]) for i in range(n) for j in range(i + 1, n)]
        # SORT PAIRS? O(m+w_n_r)?
        comb=combinations(KB,2)
        for x in comb:
            # x = q.get()
            ci = x[0]
            cj = x[1]
            resolvents = resolve(ci, cj)
            if len(resolvents) != 0:
                if has_empty2(resolvents):
                    return True
                for i in resolvents:
                    if not in_custom(i, new):
                        new.add(i)
        if is_subset(new, KB):
            return False
        for c in new:
            if not in_custom(c, KB):
                KB.add(c)

    return False


def resolution(KB, alpha):
    new = set()
    max = KB.__len__() * KB.__len__()
    i = 0
    q = comb(KB)
    comb_new(KB, [alpha], q)
    KB.add(alpha)
    while i < max:
        i += 1
        # if i>1:
        #     q = comb(KB)
        print i, q.qsize()
        while not q.empty():
            x = q.get()
            # print x[0].toString()," with ",x[1].toString()
            if not x[0].equals(x[1]):
                resolvents = resolve(x[0], x[1])
            else:
                resolvents = set()
            if len(resolvents) != 0:
                # print list(resolvents)[0].literals
                if has_empty2(resolvents):
                    del KB
                    return True
                comb_new(KB, resolvents, q)
                # print q.qsize()
                new.add(list(resolvents)[0])
        if new.issubset(KB) and len(new) != 0:
            del KB
            return False
        comb_new(KB, new, q)
        for x in new:
            KB.add(x)

    del KB
    return False

# RESULT SO FAR: IF answer should be False, im always right,
# if answer should be True, seems random
input_param = readfile("input1.txt")
queries, nQuery, nSentences = input_param["Q"], input_param["Nq"], input_param["Ns"]
file_output = open("output.txt", 'w')
while not queries.empty():
    KBs = deepcopy(input_param['S'])
    inference = resolution2(KBs, queries.get())
    print inference
    if inference:
        file_output.write("TRUE")
    else:
        file_output.write("FALSE")
    file_output.write("\n")
file_output.close()

# KB = set()
# KB.add("a")
# KB.add("b")
# KB.add("c")
# q = comb(KB)
# new=set()
#
# comb_new(KB,new,q)
# print q.get()

# x = Sentence("~Criminal(West)").literals
# y = Sentence("~Hostile(z) | Criminal(x)").literals
# print unifyR(x, y, {})
# print x
# print y

# p = set()
# p.add(Sentence("Knows(John,x)"))
# p.add(Sentence("Knows(y,Amy)"))
#
# d = split_compound(["A(xy,cuzinho)"])
# x_args = d['arg']
# x_op = d['function']
# print x_op,x_args
