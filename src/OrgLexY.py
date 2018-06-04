# Organize lexY and LEXICON_1
# Organize compound_Y and LEXICON_2
import os
from Lexicon import *
from shutil import copyfile

_lexYdict = {}
_lexYCommentdict = {}
_lexicon1dict = {}
_lexicon1Commentdict = {}

_allLexdict = {}

_compoundYdict = {}
_compoundYCommentdict = {}
_lexicon2dict = {}
_lexicon2Commentdict = {}

YDirLocation = os.path.dirname(os.path.realpath(__file__))
tmpDirPath = YDirLocation + '/../../fsa/tmp/'
if not os.path.exists(tmpDirPath):
    os.mkdir(tmpDirPath)

lexYLocation = YDirLocation + '/../../fsa/Y/lexY.txt'
tmpLexY = tmpDirPath + 'lexYCopy.txt'
lexicon1Location = YDirLocation + "/../../fsa/Y/LEXICON_1.txt"
tmpLexicon1 = tmpDirPath + 'Lexicon1Copy.txt'
compoundYLocation = YDirLocation + '/../../fsa/Y/compoundY.txt'
tmpCompound = tmpDirPath + 'compoundYCopy.txt'
lexicon2Location = YDirLocation + '/../../fsa/Y/LEXICON_2.txt'
tmpLexicon2 = tmpDirPath + 'Lexicon2Copy.txt'

_lexLocationList = [lexYLocation, lexicon1Location, compoundYLocation, lexicon2Location]
_lexDictList = [_lexYdict, _lexicon1dict, _compoundYdict, _lexicon2dict]
_lexCommentList = [_lexYCommentdict, _lexicon1Commentdict, _compoundYCommentdict, _lexicon2Commentdict]


def LoadLex(lexiconLocation, _CommentDict, _LexiconDict):
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
                continue
            newNode = False

            if blocks[0] in _LexiconDict.keys():
                node = _LexiconDict.get(blocks[0])
                print ("repeated word " + blocks[0] + " in lexicon " + lexiconLocation)
            else:
                node = None
            if not node:
                newNode = True
                node = LexiconNode(blocks[0])
                if "_" in node.text:
                    node.forLookup = True       # for those combination words.
                if comment:
                    node.comment = comment
            # else:
            #     logging.debug("This word is repeated in lexicon: %s" % blocks[0])

            features = SplitFeatures(blocks[1])  # blocks[1].split()
            for feature in features:
                if re.match('^\'.*\'$', feature):
                    node.norm = feature.strip('\'')
                elif re.match('^/.*/$', feature):
                    node.atom = feature.strip('/')
                elif re.search(u'[\u4e00-\u9fff]', feature):
                    node.norm = feature
                    continue
                else:
                    featureID = GetFeatureID(feature)

                    if featureID == -1:
                        logging.debug("Missing Feature: " + feature)
                        node.missingfeature += "\\" + feature

                    node.features.add(featureID)
                    ontologynode = SearchFeatureOntology(featureID)
                    if ontologynode:
                        ancestors = ontologynode.ancestors
                        if ancestors:
                            node.features.update(ancestors)

            if newNode:
                _LexiconDict.update({node.text: node})
                # logging.debug(node.word)
            oldWord = blocks[0]

    logging.info("Finish loading lexicon" + lexiconLocation)


def compareLex(_LexiconDict1,_LexiconDict2):
    removeWord = set()
    for word in _LexiconDict1.keys():
        if word in _LexiconDict2.keys():
            node1 = _LexiconDict1.get(word)
            feature1 = node1.features
            node2 = _LexiconDict2.get(word)
            feature2 = node2.features
            temp = feature1.union(feature2)
            featuresCopy = temp.copy()

            for feature in temp:

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
                    featureSorted.add(feature)

            featureSorted = sorted(featureSorted)
            node1.features = featureSorted

            _LexiconDict1.update({word:node1})
            removeWord.add(word)

    for word in removeWord:
        del _LexiconDict2[word]


def searchAtomOrNorm(atom):
    if atom in _lexYdict.keys():
        features = _lexYdict.get(atom).features
        return features
    if atom in _lexicon1dict.keys():
        features = _lexicon1dict.get(atom).features
        return features
    if atom in _compoundYdict.keys():
        features = _compoundYdict.get(atom).features
        return features
    if atom in _lexicon2dict.keys():
        features = _lexicon2dict.get(atom).features
        return features

    return None


def enrichFeature():
    for word in _lexYdict.keys():
        node = _lexYdict.get(word)
        atom = node.atom
        norm = node.norm
        feature = node.features

        if atom != word:
            atomfeatures = searchAtomOrNorm(atom)
            if atomfeatures:
                temp = feature.union(atomfeatures)
                node.features = temp
                _lexYdict.update({word: node})
        elif norm != word:
            normfeatures = searchAtomOrNorm(norm)
            if normfeatures:
                temp = feature.union(normfeatures)
                node.features = temp
                _lexYdict.update({word: node})


def printNewLex(newloc, _lexDict,_CommentDict):
    s = sorted(_lexDict.keys())
    with open(newloc, 'w',encoding='utf-8') as file:
        output = ""
        if _CommentDict.get("firstCommentLine"):
            output += _CommentDict.get("firstCommentLine") + "\n"
        oldWord = None
        logging.debug("the size of lexX is: " + str(len(_lexDict)))
        for word in s:
            if oldWord in _CommentDict.keys():
                output += _CommentDict[oldWord]
            output += _lexDict.get(word).entry() + "\n"
            oldWord = word
        file.write(output+"\n")


if __name__ == "__main__":

    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    # make copy of original lexicons
    copyfile(lexYLocation, tmpLexY)
    copyfile(lexicon1Location, tmpLexicon1)
    copyfile(compoundYLocation, tmpCompound)
    copyfile(lexicon2Location, tmpLexicon2)
    LoadFeatureOntology(YDirLocation + '/../../fsa/Y/feature.txt')
    # load each lexicon file and store into NODE structure
    for i in range(0, len(_lexDictList)):
        LoadLex(_lexLocationList[i], _lexCommentList[i], _lexDictList[i])

    # deal with feature enrichment
    enrichFeature()

    # compare the corresponding lexicons of same level
    compareLex(_lexYdict,_lexicon1dict)
    compareLex(_compoundYdict, _lexicon2dict)

    printNewLex(lexYLocation,_lexYdict,_lexYCommentdict)
    printNewLex(lexicon1Location,_lexicon1dict,_lexicon1Commentdict)
    printNewLex(compoundYLocation, _compoundYdict,_compoundYCommentdict)
    printNewLex(lexicon2Location, _lexicon2dict,_lexicon2Commentdict)





