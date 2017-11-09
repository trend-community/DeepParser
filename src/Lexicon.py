#!/bin/python
#read in the lookup dictionary. It is mainly used for segmenation (combining multiple tokens into one word/token)
# defLexX.txt sample: 也就: EX advJJ preXV pv rightB /就/

import logging, re, operator, sys, os, pickle, requests
import string

from utils import *
from FeatureOntology import *
import Tokenization

# url = "http://localhost:5001"
# url_ch = "http://localhost:8080"

_LexiconDict = {}
_LexiconLookupSet = set()
#_LexiconLookupDict = {}     # extra dictionary for lookup purpose.
                            # the same node is also saved in _LexiconDict
#_LexiconBlacklist = []
_CommentDict = {}

C1ID = None
C2ID = None
C3ID = None
C4ID = None
C4plusID = None


class LexiconNode(object):
    def __init__(self, word=''):
        self.text = word
        self.norm = word
        self.atom = word
        self.features = set()
        self.missingfeature = ""
        #self.forLookup = False

    def __str__(self):
        output = self.text + ": "
        for feature in self.features:
            f = GetFeatureName(feature)
            if f:
                output += f + ","
            else:
                logging.warning("Can't get feature name of " + self.text + " for id " + str(feature))
        return output

    def entry(self):
        output = self.text + ": "
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
                logging.warning("Can't find feature of " + self.text)

        featureSorted = sorted(featureSorted)

        for feature in featureSorted:
            output += feature +" "

        if self.norm != self.text:
            output += "'" + self.norm + "' "
        if self.atom != self.text:
            output += "/" + self.atom + "/ "
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


def OutputLexicon(EnglishFlag = False):
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


def OutputLexiconFile(FolderLocation):
    if FolderLocation.startswith("."):
        FolderLocation = os.path.join(os.path.dirname(os.path.realpath(__file__)),  FolderLocation)
    FileLocation = os.path.join(FolderLocation, "lexicon.txt")

    with open(FileLocation, "w", encoding="utf-8") as writer:
        writer.write(OutputLexicon())


# def LoadLexiconBlacklist(BlacklistLocation):
#     if BlacklistLocation.startswith("."):
#         BlacklistLocation = os.path.join(os.path.dirname(os.path.realpath(__file__)),  BlacklistLocation)
#     with open(BlacklistLocation, encoding="utf-8") as dictionary:
#         for line in dictionary:
#             pattern, _ = SeparateComment(line)
#             if not pattern:
#                 continue
#             _LexiconBlacklist.append(pattern)


# def InLexiconBlacklist(word):
#     for pattern in _LexiconBlacklist:
#         if re.match(pattern, word):
#             logging.debug("Blacklisted:" + word)
#             return True
#     return False

def LoadLexicon(lexiconLocation, forLookup = False):
    global _LexiconDict, _LexiconLookupSet
    global _CommentDict
    if lexiconLocation.startswith("."):
        lexiconLocation = os.path.join(os.path.dirname(os.path.realpath(__file__)),  lexiconLocation)

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

            code = code.replace("\:", Tokenization.IMPOSSIBLESTRING)
            blocks = [x.strip() for x in re.split(":", code) if x]
            if not blocks:
                continue
            newNode = False
            word = blocks[0].replace(Tokenization.IMPOSSIBLESTRING, ":").lower()
            #Ditionary is case insensitive: make the words lowercase.
            word = word.replace(" ", "").replace("~", "")

            #if InLexiconBlacklist(word):
            #    continue
            ### This checking is only for external dictionary.
            ### So let's apply it to them when generating (offline)

            node = SearchLexicon(word, 'origin')
            #node = None
            if not node:
                newNode = True
                node = LexiconNode(word)
                if comment:
                    node.comment = comment
            if len(blocks) == 2:
                # there should be no "\:" on the right side.
                features = SplitFeatures(blocks[1]) # blocks[1].split()
                for feature in features:
                    if re.match('^\'.*\'$', feature):
                        node.norm = feature.strip('\'')
                    elif re.match('^/.*/$', feature):
                        node.atom = feature.strip('/')
                    elif ChinesePattern.search(feature):    #Chinese
                        node.norm = feature
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
                _LexiconDict.update({node.text: node})
                if forLookup \
                        or "_" in node.text:    #
                    #_LexiconLookupDict.update({node.word: node})
                    _LexiconLookupSet.add(node.text)
                #logging.debug(node.word)
            oldWord = blocks[0]

    # Apply the features of stem/norm into it's variants.
    #   Only use "stem" to apply. Not norm.
    logging.debug("Start applying features for variants")
    for lexicon in _LexiconDict:
        node = _LexiconDict[lexicon]
        _ApplyWordStem(node, node)

    logging.info("Finish loading lexicon file " + lexiconLocation + "\n\t Total Size:" + str(len(_LexiconDict)))


def _ApplyWordStem(NewNode, lexiconnode):
    #VFeatureID = GetFeatureID("deverbal")
    VBFeatureID = GetFeatureID("VB")
    VedFeatureID = GetFeatureID("Ved")
    VingFeatureID = GetFeatureID("Ving")

    if NewNode.text != lexiconnode.norm and lexiconnode.norm in _LexiconDict:
        normnode = _LexiconDict[lexiconnode.norm]
        #NewNode.features.update(normnode.features)
        if VBFeatureID in NewNode.features:
            if NewNode.text == normnode.text + "ed" or NewNode.text == normnode.text + "d":
                    NewNode.features.remove(VBFeatureID)
                    NewNode.features.add(VedFeatureID)
            if NewNode.text == normnode.text + "ing":
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

    if ChinesePattern.search(word):
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


def ApplyLexiconToNodes(NodeList):
    node = NodeList.head
    while node:
        ApplyLexicon(node)
        node = node.next
    return NodeList


def ApplyWordLengthFeature(node):
    global C1ID, C2ID, C3ID, C4ID, C4plusID
    if IsAscii(node.text):
        return
    if not C1ID:
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

    wordlength = len(node.text)
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
        lex = SearchLexicon(node.text)
    # if not node.lexicon:    # If lexicon is assigned before, then don't do the search
    #                         #  because the node.word is not as reliable as stem.
    #     node.lexicon = SearchLexicon(node.word)
    if lex is None:
        if IsCD(node.text):
            node.features.add(GetFeatureID('CD'))
        elif node.text in string.punctuation:
            node.features.add(GetFeatureID('punc'))
        else:
            node.features.add(GetFeatureID('NNP'))
            node.features.add(GetFeatureID('OOV'))
    else:
        node.norm = lex.norm
        node.atom = lex.atom
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


#Lookup will be used right after segmentation.
# Dynamic programming?
def LexiconLookup(strTokens):
    sentenceLenth = strTokens.size
    bestScore = [1 for _ in range(sentenceLenth+1)]
    combinedText = ''
    combinedCount = 0
    p = strTokens.head
    i = 1

    while p:
        if p.text:
            combinedText += p.text
            combinedCount += 1
            if combinedText in _LexiconLookupSet:
                logging.debug("i=" + str(i) + " combinedCount = " + str(combinedCount) + " combinedText=" + combinedText + " in dict.")
                bestScore[i] = combinedCount

            else:
                combinedText = p.text
                combinedCount = 1
        i += 1
        p = p.next

    logging.debug("After one iteration, the bestScore list is:" + str(bestScore))

    i -= 1
    while i>0:
        if bestScore[i]>1:
            NewNode = strTokens.combine(i-bestScore[i], bestScore[i], -1)
            i = i - bestScore[i]
            ApplyLexicon(NewNode)
            NewNode.sons = []   #For lookup, eliminate the sons
            logging.debug("NewNodeAfterLexiconLookup:" + str(strTokens.get(i)))
        else:
            i = i - 1


if __name__ == "__main__":
    dir_path = os.path.dirname(os.path.realpath(__file__))
    logging.basicConfig( level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

    LoadFeatureOntology(dir_path + '/../../fsa/Y/feature.txt')
    LoadLexicon('../../fsa/X/LexX.txt')
    LoadLexicon('../../fsa/X/LexXplus.txt')
    LoadLexicon('../../fsa/X/brandX.txt')
    LoadLexicon('../../fsa/X/idiom4X.txt')
    LoadLexicon('../../fsa/X/idiomX.txt')
    LoadLexicon('../../fsa/X/locX.txt')
    LoadLexicon('../../fsa/X/perX.txt')
    LoadLexicon('../../fsa/X/defPlus.txt')
    LoadLexicon('../../fsa/X/defLexX.txt', forLookup=True)


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


