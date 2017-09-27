#!/bin/python
#read a file in main(), then do tokenization.
import logging
from FeatureOntology import GetFeatureName as FeatureOntology_GetFeatureName

#class EmptyBase(object): pass
#
# def Tokenize(sentence):
#     global DS
#     tokens = nltk.word_tokenize(sentence)
#
#     for token in tokens:
#         Element = EmptyBase()
#         Element.word = token
#         Element.position = 1
#         DS.append(Element)


class SentenceNode(object):
    def __init__(self, word):
        self.word = word
        self.stem = word
        self.norm = word
        self.features = set()
        self.lexicon = None
        self.Gone = False

    def __str__(self):
        output = "[" + self.word + "] "
        output += self.stem
        if self.Gone:
            output += '(Gone)'
        output += ": "
        for feature in self.features:
            f = FeatureOntology_GetFeatureName(feature)
            if f:
                output += f + ","
            else:
                logging.warning("Can't get feature name of " + self.word + " for id " + str(feature))
        return output

    def oneliner(self):
        output = self.stem
        featureString = ""
        for feature in self.features:
            f = FeatureOntology_GetFeatureName(feature)
            if f:
                if featureString:
                    featureString += ","
                featureString += f
            else:
                logging.warning("Can't get feature name of " + self.word + " for id " + str(feature))
        if featureString:
            output += ":" + featureString
        return output



def Tokenize(sentence):
    StartToken = True
    StartPosition = 0
    #for i in range(1, len(sentence)):   #ignore the first one.
    i = 1
    DS = []
    while i<len(sentence):
        c = sentence[i]
        prevc = sentence[i-1]
        if c == "'":
            if 0<i<len(sentence)-1 and sentence[i-1].isalpha() and sentence[i+1].isalpha():
                i+=2
                continue    #when ' sign is inside a word, like can't don't

        if (prevc.isalnum() and not c.isalnum()) or (not prevc.isalnum() and not prevc.isspace()):
            Element = SentenceNode(sentence[StartPosition:i])
            Element.position = StartPosition
            DS.append(Element)
            StartToken = False

        if (c.isalnum() and (not prevc.isalnum()) ) or (not c.isalnum() and not c.isspace()):
            StartToken = True
            StartPosition = i
        i += 1

    if StartToken:  #wrap up the last one
        Element = SentenceNode(sentence[StartPosition:])
        Element.position = StartPosition
        DS.append(Element)

    return DS

def DisplayDS(DS):
    for ds in DS:
        print("[word]:" + ds.word + "\t[position]:" + str(ds.position))


if __name__ == "__main__":
    logging.basicConfig( level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
    target = "This is a 'bad_sentence', not a word. Don't classify it as a character."
    target = """PassiveSimpleING = {<"being|getting" [RB:^.R]? [VBN|ED:VG Passive Simple Ing]>};"""
    print(target)
    # Tokenize(target)
    # print "\n\n NLTK tokenization:"
    # DisplayDS()

    print("\n\n My tokenization:")
    nodes = Tokenize(target)
    DisplayDS(nodes)



