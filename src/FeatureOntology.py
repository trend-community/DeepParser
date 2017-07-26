#!/bin/python
#read in rules, starting from dictionary (lexY.txt), then lexicon.
#might want to remember line number for rules (excluding dictionary).
import logging, re, operator

class EmptyBase(object): pass


_FeatureSet = set()
_FeatureList = []   #this is populated from FeatureSet. to have featureID.
_FeatureDict = {}   #this is populated from FeatureSet. for better searching
_AliasDict = {}
_FeatureOntology = []
_LexiconDict = {}


def SeparateComment(line):
    blocks = [x.strip() for x in re.split("//", line) ]   # remove comment.
    return blocks[0], "//".join(blocks[1:])


class OntologyNode:
    def __init__(self):
        self.openWord = ''
        self.Comment = ''
        self.openWordID = 0
        self.ancestors = set()

    def __str__(self):
        output = "[" + self.openWord + "]"
        if self.ancestors:
            output += ": "
            for i in self.ancestors:
                output += _FeatureList[i] +"; "
        if self.Comment:
            output += "\t//" + self.Comment
        return output

    def SetRule(self, line):
        code, comment = SeparateComment(line)
        self.Comment = comment
        code = self.ProcessAlias(code)
        if len(code) == 0:
            return

        features = [x.strip() for x in re.split(",|;| ", code) if x]
        self.openWord = features[0]
        feature = features[0]
        self.openWordID = GetFeatureID(feature)
        if len(features) > 1:
            for feature in features[1:]:
                self.ancestors.add(GetFeatureID(feature))


    @staticmethod
    def ProcessAlias( line):
        blocks = [x.strip() for x in re.split("=", line) if x]
        if len(blocks) <= 1:
            return line     # there is no "=" sign.
        #Now the last block has the real feature name and code
        code = blocks[-1]
        features = re.split(",|;| ", code)    # the first feature is the real one.
        featureID = GetFeatureID(features[0])
        if featureID == -1: #the feature in file is not in featureFullList
            return code # ignore
        for alias in blocks[:-1]:
            _AliasDict[alias] = featureID

        return code

#Used to extract feature from dictionary, to create full feature list.
#   not useful after full feature list is created.
def LoadFeatureSet(dictionaryLocation):
    with open(dictionaryLocation, encoding="utf-8") as dictionary:
        for line in dictionary:
            code, __ = SeparateComment(line)
            blocks = [x.strip() for x in re.split(":", code) if x]
            if len(blocks) <= 1:
                continue            # there is no ":" sign
            featurestring = blocks[-1]   # the last block has features
            features = featurestring.split()    #separate by space
            for feature in features:
                if re.match('^\'.*\'$', feature) or re.match('^/.*/$', feature):
                    continue
                _FeatureSet.add(feature)


def LoadFullFeatureList(featureListLocation):
    global _FeatureList, _FeatureDict
    _FeatureSet.clear()
    with open(featureListLocation, encoding="utf-8") as dictionary:
        for line in dictionary:
            feature, __ = SeparateComment(line)
            if len(feature) == 0:
                continue
            _FeatureSet.add(feature)
    _FeatureList = list(sorted(_FeatureSet))
    _FeatureDict = {f:i for i,f in enumerate(sorted(_FeatureSet))}


def PrintFeatureSet():
    print("\n\n***Feature Set***")
    for feature in sorted(_FeatureSet):
        print( feature )

def PrintFeatureOntology():
    print("\n\n***Ontology***")
    for node in sorted(_FeatureOntology, key=operator.attrgetter('openWord')):
        print(node)
    print("\n\n***Alias***")
    for key in sorted(_AliasDict):
        print("[" + key + "]:" + _FeatureList[_AliasDict[key]])

def LoadFeatureOntology(featureOncologyLocation):
    global _FeatureOntology
    with open(featureOncologyLocation, encoding="utf-8") as dictionary:
        for line in dictionary:
            node = OntologyNode()
            node.SetRule(line)
            if node.openWord != '':
                _FeatureOntology.append(node)

def SearchFeatureOntology(featureID):    #Can be organized to use OpenWordID (featureID), for performance gain.
    for node in _FeatureOntology:
        if node.openWordID == featureID:
            return node.ancestors
    return None

def GetFeatureID(feature):
    if feature in _AliasDict:
        return _AliasDict[feature]
    if feature in _FeatureDict:
        return _FeatureDict[feature]
    logging.warning("Searching for " + feature + " but it is not in featurefulllist.")
    return -1    # -1? 0?
def GetFeatureName(featureID):
    if 0 <= featureID < len(_FeatureList):
        return _FeatureList[featureID]
    else:
        return None

def LoadLexicon(lexiconLocation):
    global _LexiconDict
    with open(lexiconLocation, encoding='utf-8') as dictionary:
        for line in dictionary:
            code, __ = SeparateComment(line)
            blocks = [x.strip() for x in re.split(":", code) if x]
            if len(blocks) != 2:
                #logging.warn("line is not in [word]:[features] format:\n\t" + line)
                continue
            newNode = False
            node = SearchLexicon(blocks[0])
            #node = None
            if not node:
                newNode = True
                node = EmptyBase()
                node.word = blocks[0]
                node.features = set()
            else:
                logging.debug("This word is repeated in lexicon: %s" % blocks[0])
            features = blocks[1].split()
            for feature in features:
                if re.match('^\'.*\'$', feature):
                    node.stem = feature.strip('\'')
                elif re.match('^/.*/$', feature):
                    node.norm = feature.strip('/')
                else:
                    featureID =GetFeatureID(feature)
                    node.features.add(featureID)
                    # ancestors = SearchFeatureOntology(featureID)
                    # if ancestors:
                    #     node.features.update(ancestors)
            if newNode:
                _LexiconDict.update({node.word: node})


#this can be more complicate: search for case-insensitive, _ed _ing _s...
def SearchLexicon(word):
    word = word.lower()
    if word in _LexiconDict.keys():
        return _LexiconDict.get(word)


    word_ed = word.rstrip("ed")
    if word_ed in _LexiconDict.keys():
        return _LexiconDict.get(word_ed)
    word_d = word.rstrip("d")
    if word_d in _LexiconDict.keys():
        return _LexiconDict.get(word_d)
    word_ing = word.rstrip("ing")
    if word_ing in _LexiconDict.keys():
        return _LexiconDict.get(word_ing)
    word_s = word.rstrip("s")
    if word_s in _LexiconDict.keys():
        return _LexiconDict.get(word_s)
    word_es = word.rstrip("es")
    if word_es in _LexiconDict.keys():
        return _LexiconDict.get(word_es)

    return None

def SearchFeatures(word):
    lexicon = SearchLexicon(word)
    if lexicon is None:
        return {}   #return empty feature set
    return lexicon.features

import os
dir_path = os.path.dirname(os.path.realpath(__file__))
LoadFullFeatureList(dir_path + '/../../fsa/extra/featurelist.txt')
LoadFeatureOntology(dir_path + '/../doc/featureOntology.txt')
LoadLexicon(dir_path + '/../../fsa/Y/lexY.txt')

if __name__ == "__main__":
    logging.basicConfig( level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
    # LoadFeatureSet('../../fsa/Y/lexY.txt')
    # LoadFeatureSet('../../fsa/X/lexX.txt')
    PrintFeatureOntology()
    PrintFeatureSet()

    print(SearchFeatureOntology(GetFeatureID("com")))
    s = SearchLexicon("is")
    if s:
        print(s.features)
    s = SearchLexicon("ised")
    if s:
        print(s.features)
    print(SearchFeatures("airliner"))
    print(SearchFeatures("airliners"))
    print("there are so many lexicons:%s" % len(_LexiconDict))
    print(SearchFeatures("pretty"))
