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
_LexiconList = []

def SeparateComment(line):
    blocks = [x.strip() for x in re.split("//", line) ]   # remove comment.
    return blocks[0].strip(), " ".join(blocks[1:])


class OntologyRule:
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
        if feature not in _FeatureDict:
            logging.error("Feature[" + feature + "] in file is not in _FeatureDict!")
            return  # ignore.
        self.openWordID = _FeatureDict[feature]
        if len(features) > 1:
            for feature in features[1:]:
                if feature not in _FeatureDict:
                    logging.error("Feature[" + feature + "] in file is not in _FeatureDict!")
                else:
                    self.ancestors.add(_FeatureDict[feature])


    @staticmethod
    def ProcessAlias( line):
        blocks = [x.strip() for x in re.split("=", line) if x]
        if len(blocks) <= 1:
            return line     # there is no "=" sign.
        #Now the last block has the real feature name and code
        code = blocks[-1]
        features = re.split(",|;| ", code)    # the first feature is the real one.
        feature = features[0]
        if feature not in _FeatureDict:
            logging.error("Feature[" + feature + "] in file is not in _FeatureDict (ProcessAlias)!")
            # _FeatureList.append([feature])
            # _FeatureSet.add({feature, len(_FeatureList)})
            return code # ignore.

        featureID = _FeatureDict[feature]
        for alias in blocks[:-1]:
            _AliasDict[alias] = featureID

        return code

#Used to extract feature from dictionary, to create full feature list.
#   not useful after full feature list is created.
def LoadFeatureSet(dictionaryLocation):
    with open(dictionaryLocation) as dictionary:
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
    with open(featureListLocation) as dictionary:
        for line in dictionary:
            feature, __ = SeparateComment(line)
            if len(feature) == 0:
                continue
            _FeatureSet.add(feature)
    _FeatureList = list(sorted(_FeatureSet))
    _FeatureDict = {f:i for i,f in enumerate(sorted(_FeatureSet))}


def PrintFeatureSet():
    for feature in sorted(_FeatureSet):
        print( feature )

def PrintFeatureOntology():
    print "\n\n***Ontology***"
    for node in sorted(_FeatureOntology, key=operator.attrgetter('openWord')):
        print node
    print "\n\n***Alias***"
    for key in sorted(_AliasDict):
        print "[" + key + "]:" + _FeatureList[_AliasDict[key]]

def LoadFeatureOntology(featureOncologyLocation):
    global _FeatureOntology
    with open(featureOncologyLocation) as dictionary:
        for line in dictionary:
            node = OntologyRule()
            node.SetRule(line)
            if node.openWord <> '':
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
    return -1    # -1?
def GetFeatureName(featureID):
    if 0 <= featureID < len(_FeatureList):
        return _FeatureList[featureID]
    else:
        return None

def LoadLexicon(lexiconLocation):
    global _LexiconList
    with open(lexiconLocation) as dictionary:
        for line in dictionary:
            code, __ = SeparateComment(line)
            blocks = [x.strip() for x in re.split(":", code) if x]
            if len(blocks) <> 2:
                #logging.warn("line is not in [word]:[features] format:\n\t" + line)
                continue
            node = EmptyBase()
            node.word = blocks[0]
            node.features = set()
            features = blocks[1].split()
            for feature in features:
                if re.match('^\'.*\'$', feature) or re.match('^/.*/$', feature):
                    continue
                node.features.add(_FeatureDict[feature])
            _LexiconList.append(node)

def SearchLexicon(word):
    for node in _LexiconList:
        if node.word == word:
            return node
    return None

def SearchFeatures(word):
    lexicon = SearchLexicon(word)
    if lexicon is None:
        return {}   #return empty feature set
    for feature in list(lexicon.features):
        ancestors = SearchFeatureOntology(feature)
        if ancestors:
            lexicon.features.update(ancestors)
    return lexicon.features

LoadFullFeatureList('../../fsa/extra/FeatureList.txt')
LoadFeatureOntology('../doc/featureOntology.txt')
LoadLexicon('../../fsa/Y/lexY.txt')

if __name__ == "__main__":
    logging.basicConfig( level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
    # LoadFeatureSet('../../fsa/Y/lexY.txt')
    # LoadFeatureSet('../../fsa/X/lexX.txt')
    #PrintFeatureOntology()
    #PrintFeatureSet()

    print SearchFeatureOntology(GetFeatureID("com"))
    s = SearchLexicon("airline")
    print s.features

    print SearchFeatures("airline")
