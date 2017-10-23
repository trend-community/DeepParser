#!/bin/python
#read in the lookup dictionary. It is mainly used for segmenation (combining multiple tokens into one word/token)
# defLexX.txt sample: 也就: EX advJJ preXV pv rightB /就/

import logging, re, operator, sys, os, pickle, requests
import string

from utils import *
from FeatureOntology import *

# url = "http://localhost:5001"
# url_ch = "http://localhost:8080"

_LexiconDict = {}
_LexiconLookupSet = set()
_LexiconLookupDict = {}     # extra dictionary for lookup purpose.
                            # the same node is also saved in _LexiconDict
_CommentDict = {}

class LexiconNode(object):
    def __init__(self, word=''):
        self.word = word
        self.stem = word
        self.norm = word
        self.features = set()
        self.missingfeature = ""
        #self.forLookup = False

    def __str__(self):
        output = self.stem + ": "
        for feature in self.features:
            f = GetFeatureName(feature)
            if f:
                output += f + ","
            else:
                logging.warning("Can't get feature name of " + self.word + " for id " + str(feature))
        return output

    def entry(self):
        output = self.word + ": "
        features = sorted(self.features)
        featuresCopy = features.copy()
        #remove redundant ancestors.
        for feature in features:
            nodes = SearchFeatureOntology(feature)
            if nodes:
                ancestors = nodes.ancestors
                if ancestors:
                    c = ancestors.intersection(featuresCopy)
                    if c:
                        for a in c:
                            featuresCopy.remove(a)
        featureSorted = set()
        for feature in featuresCopy:
            featureName = GetFeatureName(feature)
            if featureName:
                featureSorted.add(featureName)
            else:
                logging.warning("Can't find feature of " + self.word)

        featureSorted = sorted(featureSorted)

        for feature in featureSorted:
            output += feature +" "

        if self.stem != self.word:
            output += "'" + self.stem + "' "
        if self.norm != self.word:
            output += "/" + self.norm + "/ "
        if self.missingfeature !="":
            output +=  self.missingfeature
        if hasattr(self, "comment"):
            output += self.comment

        return output


def SplitFeatures(FeatureString):
    StemPart = None
    stemMatch = re.match("(.*)(\'.+\')(.*)", FeatureString)
    #if re.search('\'.*\'$', FeatureString):
    if stemMatch and stemMatch.lastindex == 3:
        StemPart = stemMatch.group(2)
        FeatureString = stemMatch.group(1) + stemMatch.group(3)

    NormPart = None
    normMatch = re.match("(.*)(/.+/)(.*)", FeatureString)
    #if re.search('\'.*\'$', FeatureString):
    if normMatch and normMatch.lastindex == 3:
        NormPart = normMatch.group(2)
        FeatureString = normMatch.group(1) + normMatch.group(3)

    features = FeatureString.split()
    if StemPart:
        features += [StemPart]
    if NormPart:
        features += [NormPart]
    return features


def RealLength(x):
    index = 0
    occurance = 0
    while index < len(x):
        index = x.find(' ', index)
        if index!=-1:
            occurance += 1
            index += 1
        else:
            break
    if " " in x:
        return len(x) - occurance
    return len(x)


def OutputLexicon(EnglishFlag):
    # print("//***Lexicon***")
    Output = ""
    if _CommentDict.get("firstCommentLine"):
        Output += _CommentDict.get("firstCommentLine") + "\n"
    oldWord = None
    if EnglishFlag:
        s=sorted(_LexiconDict.keys())
    else :
        s = sorted(_LexiconDict.keys(), key=lambda x: (RealLength(x), x))
    for word in s:
        if oldWord in _CommentDict.keys():
            Output += _CommentDict[oldWord]
            oldWord = word

        Output += _LexiconDict.get(word).entry() + "\n"
        oldWord = word

    return Output

def LoadLexicon(lexiconLocation, forLookup = False):
    global _LexiconDict, _LexiconLookupSet
    global _CommentDict

    logging.debug("Start Loading Lexicon " + os.path.basename(lexiconLocation))

    with open(lexiconLocation, encoding='utf-8') as dictionary:
        oldWord = "firstCommentLine"
        for line in dictionary:
            if line.startswith("//"):
                if _CommentDict.get(oldWord):
                    _CommentDict.update({oldWord:_CommentDict.get(oldWord)+line})
                else:
                    _CommentDict.update({oldWord: line})
                continue
            code, comment = SeparateComment(line)
            blocks = [x.strip() for x in re.split(":", code) if x]
            if len(blocks) != 2:
                #logging.warn("line is not in [word]:[features] format:\n\t" + line)
                continue
            newNode = False
            node = SearchLexicon(blocks[0], 'origin')
            #node = None
            if not node:
                newNode = True
                node = LexiconNode(blocks[0])
                # node.forLookup = forLookup
                # if "_" in node.word:            #TODO: to confirm.
                #     node.forLookup = True       #for those combination words.
                if comment:
                    node.comment = comment
            # else:
            #     logging.debug("This word is repeated in lexicon: %s" % blocks[0])
            features = SplitFeatures(blocks[1]) # blocks[1].split()
            for feature in features:
                if re.match('^\'.*\'$', feature):
                    node.stem = feature.strip('\'')
                elif re.match('^/.*/$', feature):
                    node.norm = feature.strip('/')
                elif re.search(u'[\u4e00-\u9fff]', feature):
                    node.stem = feature
                else:
                    featureID = GetFeatureID(feature)
                    if featureID==-1:
                        logging.debug("Missing Feature: " + feature)
                        node.missingfeature += "\\" + feature
                    else:
                        node.features.add(featureID)
                        ontologynode = SearchFeatureOntology(featureID)
                        if ontologynode:
                            ancestors = ontologynode.ancestors
                            if ancestors:
                                node.features.update(ancestors)

            if newNode:
                _LexiconDict.update({node.word: node})
                if forLookup \
                        or "_" in node.word:    #
                    #_LexiconLookupDict.update({node.word: node})
                    _LexiconLookupSet.add(node.word)
                #logging.debug(node.word)
            oldWord = blocks[0]

    # Apply the features of stem/norm into it's variants.
    #   Only use "stem" to apply. Not norm.
    logging.debug("Start applying features for variants")
    for lexicon in _LexiconDict:
        node = _LexiconDict[lexicon]
        _ApplyWordStem(node, node)

    logging.debug("Finish loading lexicon")

    GenerateLookupDict(_LexiconLookupSet)


def GenerateLookupDict(lookupset):
    global _LexiconLookupDict
    for word in lookupset:
        partialword = ""
        for character in word:
            partialword += character
            if partialword in _LexiconLookupDict:
                _LexiconLookupDict[partialword].add(word)
            else:
                _LexiconLookupDict[partialword] = {word}



def _ApplyWordStem(NewNode, lexiconnode):
    #VFeatureID = GetFeatureID("deverbal")
    VBFeatureID = GetFeatureID("VB")
    VedFeatureID = GetFeatureID("Ved")
    VingFeatureID = GetFeatureID("Ving")

    if NewNode.word != lexiconnode.stem and lexiconnode.stem in _LexiconDict:
        stemnode = _LexiconDict[lexiconnode.stem]
        NewNode.features.update(stemnode.features)
        if VBFeatureID in NewNode.features:
            if NewNode.word == stemnode.word + "ed" or NewNode.word == stemnode.word + "d":
                    NewNode.features.remove(VBFeatureID)
                    NewNode.features.add(VedFeatureID)
            if NewNode.word == stemnode.word + "ing":
                    NewNode.features.remove(VBFeatureID)
                    NewNode.features.add(VingFeatureID)


#   If the SearchType is not flexible, then search the origin word only.
# Otherwise, after failed for the origin word, search for case-insensitive, _ed _ing _s...
def SearchLexicon(word, SearchType='flexible'):
    #word = word.lower()
    if word in _LexiconDict.keys():
        return _LexiconDict.get(word)

    if SearchType != 'flexible':
        return None

    word = word.lower()
    if word in _LexiconDict.keys():
        return _LexiconDict.get(word)

    word_ed = re.sub("ed$", '', word)
    if word_ed in _LexiconDict.keys():
        return _LexiconDict.get(word_ed)
    word_d = re.sub("d$", '', word)
    if word_d in _LexiconDict.keys():
        return _LexiconDict.get(word_d)
    word_ing = re.sub("ing$", '', word)
    if word_ing in _LexiconDict.keys():
        return _LexiconDict.get(word_ing)
    word_s = re.sub("s$", '', word)
    if word_s in _LexiconDict.keys():
        return _LexiconDict.get(word_s)
    word_es = re.sub("es$", '', word)
    if word_es in _LexiconDict.keys():
        return _LexiconDict.get(word_es)

    return None


def SearchFeatures(word):
    lexicon = SearchLexicon(word)
    if lexicon is None:
        return {}   #return empty feature set
    return lexicon.features


def ApplyLexiconToNodes(nodes):
    for node in nodes:
        ApplyLexicon(node)
    return nodes


def ApplyWordLengthFeature(node):
    if IsAscii(node.stem):
        return

    C1ID = GetFeatureID('c1')
    C2ID = GetFeatureID('c2')
    C3ID = GetFeatureID('c3')
    C4ID = GetFeatureID('c4')
    C4plusID = GetFeatureID('c4plus')

    # Below is for None-English only:
    if C1ID in node.features:
        node.features.remove(C1ID)
    if C2ID in node.features:
        node.features.remove(C2ID)
    if C3ID in node.features:
        node.features.remove(C3ID)
    if C4ID in node.features:
        node.features.remove(C4ID)
    if C4plusID in node.features:
        node.features.remove(C4plusID)

    wordlength = len(node.stem)
    if wordlength<1:
        pass
    elif wordlength == 1:
        node.features.add(C1ID)
    elif wordlength == 2:
        node.features.add(C2ID)
    elif wordlength == 3:
        node.features.add(C3ID)
    elif wordlength == 4:
        node.features.add(C4ID)
    else:
        node.features.add(C4plusID)

    return


def ApplyLexicon(node, lex=None):
    if not lex:
        lex = SearchLexicon(node.word)
    # if not node.lexicon:    # If lexicon is assigned before, then don't do the search
    #                         #  because the node.word is not as reliable as stem.
    #     node.lexicon = SearchLexicon(node.word)
    if lex is None:
        if IsCD(node.word):
            node.features.add(GetFeatureID('CD'))
        elif node.word in string.punctuation:
            node.features.add(GetFeatureID('punc'))
        else:
            node.features.add(GetFeatureID('NNP'))
            node.features.add(GetFeatureID('OOV'))
    else:
        node.stem = lex.stem
        node.norm = lex.norm
        NEWFeatureID = GetFeatureID("NEW")
        if NEWFeatureID in lex.features:
            node.features = set()
            node.features.update(lex.features)
            node.features.remove(NEWFeatureID)
        else:
            node.features.update(lex.features)
        _ApplyWordStem(node, lex)

    ApplyWordLengthFeature(node)
    return node


#combining some tokens into one token and
# (1) refresh with the lexical features;
# (2) void the combined tokens with FEATURE:Gone
def ChunkingLexicon(strtokens, length, lexicon):
    logging.debug("Start chunking lexicon " + lexicon.word)
    NewStems = []
    for i in range(length):
        NewStems.append( strtokens[i].stem)     # or StrTokens[i].lexicon.stem?
        strtokens[i].Gone = True
        strtokens[i].features = set()      #remove the existing features

    if IsAscii(NewStems):
        NewStem = "_".join(NewStems)
    else:
        NewStem = "".join(NewStems)
    strtokens[0].stem = NewStem
    #strtokens[0].word = NewStem
    strtokens[0].Gone = False
    #strtokens[0].lexicon = lexicon
    ApplyLexicon(strtokens[0], lexicon)      #including features and stems


# return the how many tokens combined together as the "word".
# -1 if not matched.
def HeadMatchLexicon(strTokens, word):
    i = 0
    CombinedString = ""
    if not word.startswith(strTokens[0].stem):
        return -1   #verify first stem to be the starting of word.
    while i< len(strTokens):
        # if not strTokens[i].stem:   #JS and other empty strings. ignore.
        #     i += 1
        #     continue                # do this judgment before it gets in here.
        if IsAscii(CombinedString) \
            and CombinedString:         #ignore the first word.
            CombinedString += "_" + strTokens[i].stem
        else:
            CombinedString += strTokens[i].stem
        if len(CombinedString) > len(word):
            return -1
        if len(CombinedString) == len(word):
            if CombinedString == word:
                return i+1              # Return the length
            else:
                return -1
        if not word.startswith(CombinedString):
            return -1
        i += 1

    return -1

#Lookup will be used right after segmentation.
#Assume there is no "Gone" tokens here.
def LexiconLookup(strTokens):
    i = 0
    while i < len(strTokens):
        localstem = strTokens[i].stem
        if not localstem:   #JS and other empty strings. ignore.
            i += 1
            continue

        WinningLexicon = None
        if localstem in _LexiconLookupDict:
            for word in _LexiconLookupDict[localstem]:
                MatchLength = HeadMatchLexicon(strTokens[i:], word)
                if MatchLength > 0:
                    if WinningLexicon and len(WinningLexicon.word) >= len(word):
                        pass
                    else:
                        WinningLexicon = _LexiconDict.get(word)
                        WinningLexicon_MatchLength = MatchLength
                        logging.debug("Found Winning Lexicon " + str(WinningLexicon))

        if WinningLexicon:
            logging.debug("Start applying winning lexicon")
            ChunkingLexicon(strTokens[i:], WinningLexicon_MatchLength, WinningLexicon)
            i += WinningLexicon_MatchLength - 1

        i += 1


if __name__ == "__main__":
    dir_path = os.path.dirname(os.path.realpath(__file__))
    logging.basicConfig( level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

    LoadFeatureOntology(dir_path + '/../../fsa/Y/feature.txt')
    para = dir_path + '/../../fsa/X/perX.txt'
    LoadLexicon(para)
    para = dir_path + '/../../fsa/X/defLexX.txt'
    LoadLexicon(para, forLookup=True)
    if "/fsa/X" in para:
        Englishflag = False
    else:
        Englishflag = True
    print(OutputLexicon(Englishflag))
    print(OutputMissingFeatureSet())


