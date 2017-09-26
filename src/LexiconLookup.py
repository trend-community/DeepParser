#!/bin/python
#read in the lookup dictionary. It is mainly used for segmenation (combining multiple tokens into one word/token)


import logging, re, operator, sys, os, pickle, requests
from functools import lru_cache

from utils import *

url = "http://localhost:5001"
url_ch = "http://localhost:8080"

_LexLookupDict = []



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


def LoadLexicon(lexiconLocation):
    global _LexiconDict
    global _CommentDict

    # pickleLocation = "lexicon.pickle"
    # #if os.path.isfile(pickleLocation):
    # if False:
    #     with open(pickleLocation, 'rb') as pk:
    #         _CommentDict = pickle.load(pk)
    #         _LexiconDict = pickle.load(pk)
    #     return
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
                    continue
                else:
                    featureID = GetFeatureID(feature)
                    if featureID==-1:
                        logging.debug("Missing Feature: " + feature)
                        node.missingfeature += " " + feature
                    node.features.add(featureID)
                    ontologynode = SearchFeatureOntology(featureID)
                    if ontologynode:
                        ancestors = ontologynode.ancestors
                        if ancestors:
                            node.features.update(ancestors)

            if newNode:
                _LexiconDict.update({node.word: node})
                #logging.debug(node.word)
            oldWord = blocks[0]

    # Apply the features of stem/norm into it's variants.
    logging.debug("Start applying features for variants")
    for lexicon in _LexiconDict:
        node = _LexiconDict[lexicon]
        _ApplyWordStem(node, node)

    logging.debug("Finish loading lexicon")
    # with open(pickleLocation, 'wb') as pk:
    #     pickle.dump(_LexiconDict, pk)
    #     pickle.dump(_CommentDict, pk)



#   If the SearchType is not flexible, then search the origin word only.
# Otherwise, after failed for the origin word, search for case-insensitive, _ed _ing _s...
def SearchLexicon(word):
    #word = word.lower()
    if word in _LexiconDict.keys():
        return _LexiconDict.get(word)

    return None


if __name__ == "__main__":
    dir_path = os.path.dirname(os.path.realpath(__file__))
    logging.basicConfig( level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

    if len(sys.argv) != 2:
        print("Usage: python FeatureOntology.py CreateFeatureList/CreateFeatureOntology/CreateLexicon > outputfile.txt")
        exit(0)
    command = sys.argv[1]

    if command == "CreateFeatureList":
        _CreateFeatureList = True
        LoadFeatureOntology(dir_path + '/../../fsa/Y/feature.txt')
        # LoadLexicon(dir_path + '/../../fsa/X/lexX.txt')
        # LoadLexicon(dir_path + '/../../fsa/Y/lexY.txt')
        PrintFeatureSet()

    elif command == "CreateFeatureOntology":
        LoadFullFeatureList(dir_path + '/../../fsa/extra/featurelist.txt')
        LoadFeatureOntology(dir_path + '/../../fsa/Y/feature.txt')
        PrintFeatureOntology()
        PrintMissingFeatureSet()

    elif command == "CreateLexicon":
        LoadFullFeatureList(dir_path + '/../../fsa/extra/featurelist.txt')
        LoadFeatureOntology(dir_path + '/../../fsa/Y/feature.txt')
        para = dir_path + '/../../fsa/X/perX.txt'
        LoadLexicon(para)
        if "/fsa/X" in para:
            Englishflag = False
        else:
            Englishflag = True
        PrintLexicon(Englishflag)
        PrintMissingFeatureSet()

    else:
        print("Usage: python FeatureOntology.py CreateFeatureList/CreateFeatureOntology/CreateLexicon > outputfile.txt")
        exit(0)

