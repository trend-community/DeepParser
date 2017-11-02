#!/bin/python
#read a file in main(), then do tokenization.
import logging, requests, jsonpickle
import FeatureOntology
from utils import *

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
        self.stem = word.lower()
        self.norm = word.lower()
        self.features = set()
        #self.lexicon = None
        self.Gone = False
        self.SkipRead = False
        self.StartTrunk = 0
        self.EndTrunk = 0
        self.StartOffset = -1
        self.EndOffset = -1

        #From webservice, only word/StartOffset/features are set,
        #    and the features are "list", need to change to "set"
    def populatedefaultvalue(self):
        self.stem = self.word.lower()
        self.norm = self.word.lower()
        self.features = set()
        for featurename in self.featurenames:
            self.features.add(FeatureOntology.GetFeatureID(featurename))
        #self.lexicon = None
        self.Gone = False
        self.SkipRead = False
        self.StartTrunk = 0
        self.EndTrunk = 0
        self.EndOffset = self.StartOffset + len(self.word) - 1

    def __str__(self):
        output = "[" + self.word + "] "
        output += self.stem
        if self.Gone:
            output += '(Gone)'
        featureString = self.GetFeatures()
        if featureString:
            output += ":" + featureString
        return output

    def oneliner(self):
        output = self.stem
        featureString = self.GetFeatures()
        if featureString:
            output += ":" + featureString
        return output

    def GetFeatures(self):
        featureString = ""
        for feature in sorted(self.features):
            f = FeatureOntology.GetFeatureName(feature)
            if f:
                if featureString:
                    featureString += ","
                featureString += f
            else:
                logging.warning("Can't get feature name of " + self.word + " for id " + str(feature))
        return featureString

    def JsonOutput(self):
        a = JsonClass()
        a.word = self.word
        if self.stem != self.word:
            a.stem = self.stem
        if self.norm != self.word:
            a.norm = self.norm
        a.features = [FeatureOntology.GetFeatureName(f) for f in self.features]
        #self.lexicon = None
        if self.Gone:
            a.Gone = self.Gone
        if self.SkipRead:
            a.SkipRead = self.SkipRead
        if self.StartTrunk:
            a.StartTrunk = self.StartTrunk
        if self.EndTrunk:
            a.EndTrunk = self.EndTrunk
        a.StartOffset = self.StartOffset
        a.EndOffset = self.EndOffset

        return a.toJSON()

class JsonClass(object):
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, ensure_ascii=False)

def Tokenize_space(sentence):
    StartToken = True
    StartPosition = 0
    #for i in range(1, len(sentence)):   #ignore the first one.
    i = 1
    Tokens = []
    while i<len(sentence):
        c = sentence[i]
        prevc = sentence[i-1]
        if c == "'":
            if 0<i<len(sentence)-1 and sentence[i-1].isalpha() and sentence[i+1].isalpha():
                i+=2
                continue    #when ' sign is inside a word, like can't don't

        if (prevc.isalnum() and not c.isalnum()) or (not prevc.isalnum() and not prevc.isspace()):
            Element = SentenceNode(sentence[StartPosition:i])
            Element.StartOffset = StartPosition
            Element.EndOffset = i
            Tokens.append(Element)
            StartToken = False

        if (c.isalnum() and (not prevc.isalnum()) ) or (not c.isalnum() and not c.isspace()):
            StartToken = True
            StartPosition = i
        i += 1

    if StartToken:  #wrap up the last one
        Element = SentenceNode(sentence[StartPosition:])
        Element.StartOffset = StartPosition
        Element.EndOffset = len(sentence)
        Tokens.append(Element)

    return Tokens


IMPOSSIBLESTRING = "@#$%!"
def Tokenize(Sentence):
    Sentence = Sentence.strip()
    if IsAscii(Sentence):
        Tokens = Tokenize_space(Sentence)

        # if FeatureOntology._FeatureSet:
            #this part is to get tokenize from webservice. not actually practical.
        # TokenizeURL = url + "/Tokenize"
        # ret_t = requests.post(TokenizeURL, data=Sentence)
        # nodes_t = jsonpickle.decode(ret_t.text)
    else:
        TokenizeURL = url_ch + "/TokenizeJson/"
        #ret_t = requests.get(TokenizeURL + Sentence)

        data = {'Sentence': URLEncoding(Sentence)}
        ret = requests.get(TokenizeURL, params=data)
        if ret.status_code>399:
            logging.error("Return code:" + str(ret.status_code))
            logging.error(data)
            return []
        segmented = ret.text
        try:
            Tokens = jsonpickle.decode(segmented)
        except ValueError as e:
            logging.error("Can't be process:")
            logging.error(segmented)
            logging.error(data)
            logging.error(str(e))
            return []

        #logging.info("segmented text=\n" + segmented)

        # Tokens = []
        for token in Tokens:
            token.populatedefaultvalue()

        #logging.info("Tokens encode text=\n" + jsonpickle.encode(Tokens))
        # segmented = segmented.replace("\/", IMPOSSIBLESTRING)
        # blocks = segmented.split("/")
        # Tokens = []
        # for block in blocks:
        #     block = block.replace(IMPOSSIBLESTRING, "/")
        #     WordPropertyPair = block.split(":")
        #     Element = SentenceNode(WordPropertyPair[0])
        #     if len(WordPropertyPair)>1:
        #         features = WordPropertyPair[1]
        #         for feature in features.split():
        #             featureid = FeatureOntology.GetFeatureID(feature)
        #             Element.features.add(featureid)
        #
        #     Tokens.append(Element)
    return Tokens


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
    DisplayDS_old(nodes)



