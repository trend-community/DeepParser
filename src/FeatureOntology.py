#!/bin/python
#read in rules, starting from dictionary (lexY.txt), then lexicon.
#might want to remember line number for rules (excluding dictionary).
#usage: to output feature list, run:
#       python Rules.py > features.txt

import logging, re, operator, sys, os

class LexiconNode(object):
    def __init__(self, word=''):
        self.word = word
        self.stem = word
        self.norm = word
        self.features = set()
    def __str__(self):
        output = self.word + ": "
        for feature in self.features:
            f = GetFeatureName(feature)
            if f:
                output += f + ","
            else:
                logging.warning("Can't get feature name of " + self.word + " for id " + str(feature))
        return output
    def entry(self):
        output = self.word + ": "
        lexiconCopy = set()
        features = sorted(self.features)
        lexiconCopy = features.copy()
        for feature in features:
            nodes = SearchFeatureOntology(feature)
            if nodes:
                ancestors = nodes.ancestors
                if ancestors:
                    c = ancestors.intersection(lexiconCopy)
                    if c:
                        for a in c:
                            lexiconCopy.remove(a)
        featureSorted = set()
        for feature in lexiconCopy:
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
            output += "/" + self.norm + " / "

        if hasattr(self, "comment"):
            output += " //" + self.comment

        return output

_FeatureSet = set()
_FeatureList = []   #this is populated from FeatureSet. to have featureID.
_FeatureDict = {}   #this is populated from FeatureSet. for better searching
_AliasDict = {}
_FeatureOntology = []
_LexiconDict = {}
_CommentDict = {}
_CreateFeatureList = False
_MissingFeatureSet = set()

def SeparateComment(line):
    blocks = [x.strip() for x in re.split("//", line) ]   # remove comment.
    return blocks[0], "//".join(blocks[1:])


class OntologyNode:
    def __init__(self):
        self.openWord = ''
        self.Comment = ''
        self.openWordID = -1
        self.ancestors = set()

    def __str__(self):
        output = self.openWord
        if self.ancestors:
            output += ", "
            self.ancestors = sorted(self.ancestors)
            for i in self.ancestors:
                output += GetFeatureName(i) +"; "
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
        openWord = features[0]
        openWordID = GetFeatureID(openWord)


        TryOldNode = SearchFeatureOntology(openWordID)
        if TryOldNode:
            if len(features) > 1:
                for feature in features[1:]:
                    TryOldNode.ancestors.add(GetFeatureID(feature))
        else:
            self.openWord = openWord
            self.openWordID = openWordID

            if len(features) > 1:
                for feature in features[1:]:
                    fid = GetFeatureID(feature)
                    self.ancestors.add(fid)
                    #self.ancestors = set(self.ancestors)

    @staticmethod
    def ProcessAlias( line):
        blocks = [x.strip() for x in re.split("=", line) if x]
        if len(blocks) <= 1:
            return line     # there is no "=" sign.
        #Now the last block has the real feature name and code
        code = blocks[-1]
        features = re.split(",|;| ", code)    # the first feature is the real one.
        realfeature = features[0]

        featureID = GetFeatureID(realfeature)
        if featureID == -1: #the feature in file is not in featureFullList
            logging.warning("The feature in file is not in feature list!" + realfeature + " in \n\t" + line)
            return code # ignore

        realnode = SearchFeatureOntology(featureID)
        if not realnode:
            realnode = OntologyNode()
            realnode.openWord = realfeature
            realnode.openWordID = featureID
            _FeatureOntology.append(realnode)

        for alias in blocks[:-1]:
            aliasnode = SearchFeatureOntology(GetFeatureID(alias))
            if aliasnode:
                realnode.ancestors.update(aliasnode.ancestors)
                aliasnode.ancestors.clear()
                if alias in _FeatureSet:
                    _FeatureSet.remove(alias)
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
    print("// ***Feature Set***")
    for feature in sorted(_FeatureSet):
        print( feature )
    print("// ***Alias***")
    for key in sorted(_AliasDict):
        print( key )

def PrintMissingFeatureSet():
    if _MissingFeatureSet:
        print("//  ***Features that are not included in FullFeatureList***")
        for feature in sorted(_MissingFeatureSet):
            print(feature)

def PrintFeatureOntology():
    print("//***Ontology***")
    for node in sorted(_FeatureOntology, key=operator.attrgetter('openWord')):
        if node.ancestors:
            print(node)
    print("//***Alias***")
    for key in sorted(_AliasDict):
        print( key + "=" + _FeatureList[_AliasDict[key]])

def PrintLexicon():
    print("//***Lexicon***")
    if _CommentDict.get("firstCommentLine"):
        print(_CommentDict.get("firstCommentLine"))
    oldWord = None
    for word in _LexiconDict.keys():
        if oldWord in _CommentDict.keys():
            print(_CommentDict[oldWord],end="")
            oldWord = word

        output = _LexiconDict.get(word).entry()
        print(output)
        oldWord = word

def LoadFeatureOntology(featureOncologyLocation):
    global _FeatureOntology
    with open(featureOncologyLocation, encoding="utf-8") as dictionary:
        for line in dictionary:
            node = OntologyNode()
            node.SetRule(line)
            if node.openWordID != -1:
                _FeatureOntology.append(node)

def SearchFeatureOntology(featureID):    #Can be organized to use OpenWordID (featureID), for performance gain.
    for node in _FeatureOntology:
        if node.openWordID == featureID:
            return node
    return None

def GetFeatureID(feature):
    if feature in _AliasDict:
        return _AliasDict[feature]
    if feature in _FeatureDict:
        return _FeatureDict[feature]
    if _CreateFeatureList:
        _FeatureSet.add(feature)
        return 1
    logging.warning("Searching for " + feature + " but it is not in featurefulllist.")
    _MissingFeatureSet.add(feature)
    return -1    # -1? 0?
def GetFeatureName(featureID):
    if 0 <= featureID < len(_FeatureList):
        return _FeatureList[featureID]
    else:
        # logging.warning("Searching for " + str(featureID) + " but it is not in featurefulllist.")
        # raise(Exception("error"))
        return None


def LoadLexicon(lexiconLocation):
    global _LexiconDict
    global _CommentDict
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
            node = SearchLexicon(blocks[0])
            #node = None
            if not node:
                newNode = True
                node = LexiconNode(blocks[0])
                if comment:
                    node.comment = comment
            # else:
            #     logging.debug("This word is repeated in lexicon: %s" % blocks[0])
            features = blocks[1].split()
            for feature in features:

                if re.match('^\'.*\'$', feature):
                    node.stem = feature.strip('\'')
                elif re.match('^/.*/$', feature):
                    node.norm = feature.strip('/')
                elif re.search(u'[\u4e00-\u9fff]', feature):
                    node.stem = feature
                    continue
                else:
                    featureID =GetFeatureID(feature)
                    node.features.add(featureID)
                    ontologynode = SearchFeatureOntology(featureID)
                    if ontologynode:
                        ancestors = ontologynode.ancestors
                        if ancestors:
                            node.features.update(ancestors)

            if newNode:
                _LexiconDict.update({node.word: node})
            oldWord = blocks[0]


#this can be more complicate: search for case-insensitive, _ed _ing _s...
def SearchLexicon(word):
    word = word.lower()
    if word in _LexiconDict.keys():
        return _LexiconDict.get(word)


    # word_ed = word.rstrip("ed")
    # if word_ed in _LexiconDict.keys():
    #     return _LexiconDict.get(word_ed)
    # word_d = word.rstrip("d")
    # if word_d in _LexiconDict.keys():
    #     return _LexiconDict.get(word_d)
    # word_ing = word.rstrip("ing")
    # if word_ing in _LexiconDict.keys():
    #     return _LexiconDict.get(word_ing)
    # word_s = word.rstrip("s")
    # if word_s in _LexiconDict.keys():
    #     return _LexiconDict.get(word_s)
    # word_es = word.rstrip("es")
    # if word_es in _LexiconDict.keys():
    #     return _LexiconDict.get(word_es)

    return None

def SearchFeatures(word):
    lexicon = SearchLexicon(word)
    if lexicon is None:
        return {}   #return empty feature set
    return lexicon.features


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

    if command == "CreateFeatureOntology":
        LoadFullFeatureList(dir_path + '/../../fsa/extra/featurelist.txt')
        LoadFeatureOntology(dir_path + '/../../fsa/Y/feature.txt')
        PrintFeatureOntology()
        PrintMissingFeatureSet()

    if command == "CreateLexicon":
        LoadFullFeatureList(dir_path + '/../../fsa/extra/featurelist.txt')
        LoadFeatureOntology(dir_path + '/../../fsa/Y/feature.txt')
        LoadLexicon(dir_path + '/../../fsa/Y/lexY.txt')
        PrintLexicon()
        PrintMissingFeatureSet()

