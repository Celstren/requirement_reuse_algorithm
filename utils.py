'''
utility functions
'''

import spacy
from collections import Counter

from spacy.tokenizer import Tokenizer

BOILERPLATE = 'System shall provide the user with the ability to {} {} {}'


def tokenize(requirements):
    """
    Tokenize every line in a file
    :param path: path to file
    :return: an array of tokens
    """
    nlp = spacy.load('en_core_web_sm')
    tokenizes = []
    for requirement in requirements:
        tokenizer = Tokenizer(nlp.vocab)
        tokens = [token.text for token in tokenizer(requirement.get("cleanActionDescription").replace('system should ', '').replace('\n', ''))]
        tokenizes.append(tokens)

    return tokenizes


def make_requirements(boilerplates):
    """
    make a requirement from boilerplate elements
    :param elements: DataFrame containing verb, object, and additional information of a requirement
    :return: a list of requirements created by combining elements value
    """

    verbs = []
    objs = []
    details = []

    for bp in boilerplates:
        if bp != None:
            verbs.append(bp.get("verb"))
            objs.append(bp.get("object"))
            details.append(bp.get("detail"))

    requirements = []
    for i in range(len(verbs)):
        for j in range(len(objs)):
            for k in range(len(details)):
                if i != j and j != k:
                    requirements.append(make_requirement(verbs[i], objs[j], details[k]))

    return requirements


def make_requirement(verb, obj, detail):
    return BOILERPLATE.format(verb, obj, detail)

# c = Counter()
# for line in open('f').splitlines():
#     c.update(line.split())
# print(c)