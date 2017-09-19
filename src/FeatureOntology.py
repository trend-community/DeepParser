#!/bin/python
#read in rules, starting from dictionary (lexY.txt), then lexicon.
#might want to remember line number for rules (excluding dictionary).
#usage: to output feature list, run:
#       python Rules.py > features.txt

import logging, re, operator, sys, os, pickle
from functools import lru_cache


_FeatureSet = set()
_FeatureList = []   #this is populated from FeatureSet. to have featureID.
_FeatureDict = {}   #this is populated from FeatureSet. for better searching
_AliasDict = {}
_FeatureOntology = []
_LexiconDict = {}
_CommentDict = {}
_CreateFeatureList = False
_MissingFeatureSet = set()


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

        if hasattr(self, "comment"):
            output += " //" + self.comment

        return output


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

        features = [x.strip() for x in re.split("[,; ]", code) if x]
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
        #Now the last block has the alias name and code
        code = blocks[-1]
        realfeature = blocks[0]
        realfeatureId = GetFeatureID(realfeature)

        #featureID = GetFeatureID(realfeature)
        if realfeatureId == -1: #the feature in file is not in featureFullList
            logging.warning("The feature in file is not in feature list!" + realfeature + " in \n\t" + line)
            return code # ignore

        realnode = SearchFeatureOntology(realfeatureId)
        if not realnode:
            realnode = OntologyNode()
            realnode.openWord = realfeature
            realnode.openWordID = realfeatureId
            _FeatureOntology.append(realnode)

        features = re.split("[,; ]", code)    # the first feature is the last alias.
        lastalias = features[0]
        for alias in blocks[1:-1] + [lastalias]:
            aliasnode = SearchFeatureOntology(GetFeatureID(alias))
            aliasId = GetFeatureID(alias)
            if aliasnode:
                realnode.ancestors.update(aliasnode.ancestors)
                aliasnode.ancestors.clear()
                if alias in _FeatureSet:
                    _FeatureSet.remove(alias)

            # find all feature ontology nodes that have alias as ancestor
            #   replace that using the realfeatureId
            for node in _FeatureOntology:
                if aliasId in node.ancestors:
                    node.ancestors.remove(aliasId)
                    node.ancestors.add(realfeatureId)

            _AliasDict[alias] = realfeatureId

        return code.replace(lastalias, realfeature )

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
        print( _FeatureList[_AliasDict[key]] + "=" + key )

def PrintLexicon(flag):
    print("//***Lexicon***")
    if _CommentDict.get("firstCommentLine"):
        print(_CommentDict.get("firstCommentLine"))
    oldWord = None
    if flag:
        s=sorted(_LexiconDict.keys())
    else :
        s = sorted(_LexiconDict.keys())
        s = sorted(s, key=len)
    for word in s:
        if oldWord in _CommentDict.keys():
            print(_CommentDict[oldWord],end="")
            oldWord = word

        output = _LexiconDict.get(word).entry()
        print(output)
        oldWord = word

def LoadFeatureOntology(featureOncologyLocation):
    global _FeatureOntology
    # pickleLocation = "featureontology.pickle"
    # if os.path.isfile(pickleLocation):
    #     with open(pickleLocation, 'rb') as pk:
    #         _FeatureOntology = pickle.load(pk)
    #     return

    with open(featureOncologyLocation, encoding="utf-8") as dictionary:
        for line in dictionary:
            node = OntologyNode()
            node.SetRule(line)
            if node.openWordID != -1:
                _FeatureOntology.append(node)

    # with open(pickleLocation, 'wb') as pk:
    #     pickle.dump(_FeatureOntology, pk)


def SearchFeatureOntology(featureID):    #Can be organized to use OpenWordID (featureID), for performance gain.
    for node in _FeatureOntology:
        if node.openWordID == featureID:
            return node
    return None

@lru_cache(maxsize=1000)
def GetFeatureID(feature):
    if re.search(u'[\u4e00-\u9fff]', feature):
        return -1   # Chinese is not a feature.
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

@lru_cache(maxsize=1000)
def GetFeatureName(featureID):

    if 0 <= featureID < len(_FeatureList):
        return _FeatureList[featureID]
    else:
        logging.warning("Wrong to get Feature Name: Searching for ID[" + str(featureID) + "] but it is not right. len(_FeatureList)=" + str(len(_FeatureList)))
        # raise(Exception("error"))
        return ""


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
                #logging.debug(node.word)
            oldWord = blocks[0]

    # Apply the features of stem/norm into it's variants.
    logging.debug("Start applying features for variants")
    for lexicon in _LexiconDict:
        node = _LexiconDict[lexicon]
        _ApplyWordVariant(node, node)

    logging.debug("Finish loading lexicon")
    # with open(pickleLocation, 'wb') as pk:
    #     pickle.dump(_LexiconDict, pk)
    #     pickle.dump(_CommentDict, pk)


def _ApplyWordVariant(NewNode, lexiconnode):
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

    if NewNode.word != lexiconnode.norm and lexiconnode.norm in _LexiconDict:
        normnode = _LexiconDict[lexiconnode.norm]
        NewNode.features.update(normnode.features)
        if VBFeatureID in NewNode.features:
            if NewNode.word == normnode.word + "ed" or NewNode.word == normnode.word + "d":
                    NewNode.features.remove(VBFeatureID)
                    NewNode.features.add(VedFeatureID)
            if NewNode.word == normnode.word + "ing":
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


def ApplyLexicon(node):
    node.lexicon = SearchLexicon(node.word)
    if node.lexicon is None:
        node.features.add(GetFeatureID('NNP'))
    else:
        node.features.update(node.lexicon.features)
        _ApplyWordVariant(node, node.lexicon)
    return node

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

    elif command == "CreateFeatureOntology":
        LoadFullFeatureList(dir_path + '/../../fsa/extra/featurelist.txt')
        LoadFeatureOntology(dir_path + '/../../fsa/Y/feature.txt')
        PrintFeatureOntology()
        PrintMissingFeatureSet()

    elif command == "CreateLexicon":
        LoadFullFeatureList(dir_path + '/../../fsa/extra/featurelist.txt')
        LoadFeatureOntology(dir_path + '/../../fsa/Y/feature.txt')
        para = dir_path + '/../../fsa/X/LexX.txt'
        LoadLexicon(para)
        if "LexX" in para:
            flag = False
        else:
            flag = True
        PrintLexicon(flag)
        PrintMissingFeatureSet()

    else:
        print("Usage: python FeatureOntology.py CreateFeatureList/CreateFeatureOntology/CreateLexicon > outputfile.txt")
        exit(0)

