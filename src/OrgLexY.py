# Organize lexY and LEXICON_1
# Organize compound_Y and LEXICON_2
from Lexicon import *
import os
from shutil import copyfile
_lexYdict = {}
_lexYCommentdict = {}
_lexY3colonsdict = {}
_lexY3colonsCommentdict = {}
_lexYformsdict = {}
_lexYformsCommentdict = {}
_lexicon1dict = {}
_lexicon1Commentdict = {}

_allLexdict = {}

_compoundYdict = {}
_compoundYCommentdict = {}
_lexicon2dict = {}
_lexicon2Commentdict = {}

_FeatureNotCopy = set()
_MissingStem = set()

YDirLocation = os.path.dirname(os.path.realpath(__file__))
tmpDirPath = YDirLocation + '/../../fsa/tmp/'
if not os.path.exists(tmpDirPath):
    os.mkdir(tmpDirPath)

lexYLocation = YDirLocation + '/../../fsa/Y/lexY.txt'
tmpLexY = tmpDirPath + 'lexYCopy.txt'
lexY3colonsLocation = YDirLocation + '/../../fsa/Y/lexY_3colons.txt'
tmpLexY3colons = tmpDirPath + 'lexY_3colonsCopy.txt'
lexYformsLocation = YDirLocation + '/../../fsa/Y/lexY_forms.txt'
tmpLexYforms = tmpDirPath + 'lexY_formsCopy.txt'
lexicon1Location = YDirLocation + "/../../fsa/Y/LEXICON_1.txt"
tmpLexicon1 = tmpDirPath + 'Lexicon1Copy.txt'
compoundYLocation = YDirLocation + '/../../fsa/Y/compoundY.txt'
tmpCompound = tmpDirPath + 'compoundYCopy.txt'
lexicon2Location = YDirLocation + '/../../fsa/Y/LEXICON_2.txt'
tmpLexicon2 = tmpDirPath + 'Lexicon2Copy.txt'

paraFeatureNotCopy = YDirLocation + "/../../fsa/Y/FeatureNotCopy.txt"

_lexLocationList = [lexYLocation, lexY3colonsLocation,lexYformsLocation, lexicon1Location, compoundYLocation, lexicon2Location]
_lexDictList = [_lexYdict,_lexY3colonsdict,_lexYformsdict,  _lexicon1dict, _compoundYdict, _lexicon2dict]
_lexCommentList = [_lexYCommentdict, _lexY3colonsCommentdict, _lexYformsCommentdict, _lexicon1Commentdict, _compoundYCommentdict, _lexicon2Commentdict]


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

            if "ChinesePunctuate" in lexiconLocation and "：" in code:
                code = code.replace("：", ":")
            if ":::" in code:
                code = code.replace(":::", ":")
            if "::" in code:
                code = code.replace("::", ":")

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

            features, node = SplitFeaturesWithSemicolon(blocks[1],node)  # blocks[1].split()
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
                        if not feature.startswith("\\"):
                            node.missingfeature += "\\" + feature
                        else:
                            node.missingfeature = feature


                    node.features.add(featureID)
                    ontologynode = SearchFeatureOntology(featureID)
                    if ontologynode:
                        ancestors = ontologynode.ancestors
                        if ancestors:
                            node.features.update(ancestors)
                            if featureID in node.stemFeatures:
                                node.stemFeatures.update(ancestors)
                            elif featureID in node.origFeatures:
                                node.origFeatures.update(ancestors)

            if newNode:
                _LexiconDict.update({node.text: node})
                # logging.debug(node.word)
            oldWord = blocks[0]

    logging.info("Finish loading lexicon" + lexiconLocation)


def SplitFeaturesWithSemicolon(FeatureString, node):
    StemPart = None
    stemMatch = re.match("(.*)(\'.+\')(.*)", FeatureString)
    # if re.search('\'.*\'$', FeatureString):
    if stemMatch and stemMatch.lastindex == 3:
        StemPart = stemMatch.group(2)
        FeatureString = stemMatch.group(1) + stemMatch.group(3)

    NormPart = None
    normMatch = re.match("(.*)(/.+/)(.*)", FeatureString)
    # if re.search('\'.*\'$', FeatureString):
    if normMatch and normMatch.lastindex == 3:
        NormPart = normMatch.group(2)
        FeatureString = normMatch.group(1) + normMatch.group(3)

    # Added by Xiaochen, for English lexicon, ";" exists to distinguish features from stem or original word
    if ";" in FeatureString:
        origFeatures = FeatureString[0:FeatureString.index(";")]
        origFeaturesSet = set(origFeatures.split())
        for feature in origFeaturesSet:
            node.origFeatures.add(GetFeatureID(feature))

        stemFeatures = FeatureString[FeatureString.index(";")+1:]
        stemFeaturesSet = set(stemFeatures.split())
        for feature in stemFeaturesSet:
            node.stemFeatures.add(GetFeatureID(feature))

        FeatureString = FeatureString.replace(";", " ")

    else:
        origFeatures = FeatureString.split()
        for feature in origFeatures:
            node.origFeatures.add(GetFeatureID(feature))


    features = FeatureString.split()
    if StemPart:
        features += [StemPart]
    if NormPart:
        features += [NormPart]
    return features,node

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



def FeatureNotCopy():
    with open(paraFeatureNotCopy, encoding='utf-8') as file:
        for line in file:
            if line.startswith("//"):
                continue
            line = line.strip()
            line = GetFeatureID(line)
            _FeatureNotCopy.add(line)


def GetStemFeatures(word):
    copyFeatures = None
    for d in _lexDictList:
        if word in d.keys():
            node = d.get(word)
            features = node.features
            copyFeatures = features.copy()

            for ID in features:
                if ID in _FeatureNotCopy:
                    copyFeatures.remove(ID)
                    # print ("feature not copy " + GetFeatureName(ID))

    logging.debug("stem does not exist" + word)
    _MissingStem.add(word)
    return copyFeatures


def enrichFeature(_lexDict):
    for word in _lexDict.keys():
        node = _lexDict.get(word)
        atom = node.atom
        norm = node.norm
        feature = node.features

        if atom != word:
            atomfeatures = GetStemFeatures(atom)
            if atomfeatures:
                node.stemFeatures.update(atomfeatures)
                temp = feature.union(atomfeatures)
                node.features = temp
                _lexDict.update({word: node})
        elif norm != word:
            normfeatures = GetStemFeatures(norm)
            if normfeatures:
                node.stemFeatures.update(normfeatures)
                temp = feature.union(normfeatures)
                node.features = temp
                _lexDict.update({word: node})


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
            # output += _lexDict.get(word).entry() + "\n"
            output += getOutput(_lexDict.get(word)) + "\n"
            oldWord = word
        if newloc == lexY3colonsLocation:
            output = output.replace(":",":::")
        elif newloc == lexYformsLocation:
            output = output.replace(":", "::")
        file.write(output+"\n")


def getOutput(node):
    output = node.text + ": "
    # word = node.text
    # atom = node.atom
    # norm = node.norm
    # feature = node.features
    # diffSet = set()  #diffSet contains original feature of the node
    #
    # if atom != word:
    #     atomfeatures = GetStemFeatures(atom)
    #     if atomfeatures:
    #         diffSet = feature.difference(atomfeatures)
    # elif norm != word:
    #     normfeatures = GetStemFeatures(norm)
    #     if normfeatures:
    #         diffSet = feature.difference(normfeatures)

    # featuresCopy = CopyFeatureLeaves(node.features)

    origFeaturesCopy = CopyFeatureLeaves(node.origFeatures)
    stemFeaturesCopy = CopyFeatureLeaves(node.stemFeatures)

    for feature in stemFeaturesCopy:
        if feature in origFeaturesCopy:
            origFeaturesCopy.remove(feature)

    # diffSetCopy = CopyFeatureLeaves(diffSet)
    #
    # featuresCopy = set(featuresCopy).difference(set(diffSetCopy))
    #
    # diffSorted = set()
    # for f in diffSetCopy:
    #     featureName = GetFeatureName(f)
    #     if featureName:
    #         diffSorted.add(featureName)
    #     else:
    #         logging.warning("Can't find feature of " + node.text)
    #
    # diffSorted = sorted(diffSorted)
    #
    # if diffSorted:
    #     output += " ".join(diffSorted)
    #     output += "; "



    featureSorted = set()
    for f in origFeaturesCopy:
        featureName = GetFeatureName(f)
        if featureName:
            featureSorted.add(featureName)
        else:
            logging.warning("Can't find feature of " + node.text)

    featureSorted = sorted(featureSorted)


    output += " ".join(featureSorted) + ";"


    featureSorted = set()
    for f in stemFeaturesCopy:
        featureName = GetFeatureName(f)
        if featureName:
            featureSorted.add(featureName)
        else:
            logging.warning("Can't find feature of " + node.text)

    featureSorted = sorted(featureSorted)


    output += " ".join(featureSorted) + " "

    if node.norm != node.text:
        output += "'" + node.norm + "' "
    if node.atom != node.text:
        output += "/" + node.atom + "/ "
    if node.missingfeature != "":
        output += node.missingfeature
    if hasattr(node, "comment"):
        output += node.comment

    return output

if __name__ == "__main__":

    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    # make copy of original lexicons
    copyfile(lexYLocation, tmpLexY)
    copyfile(lexY3colonsLocation, tmpLexY3colons)
    copyfile(lexYformsLocation, tmpLexYforms)
    copyfile(lexicon1Location, tmpLexicon1)
    copyfile(compoundYLocation, tmpCompound)
    copyfile(lexicon2Location, tmpLexicon2)
    LoadFeatureOntology(YDirLocation + '/../../fsa/Y/feature.txt')
    # load each lexicon file and store into NODE structure
    for i in range(0, len(_lexDictList)):
        LoadLex(_lexLocationList[i], _lexCommentList[i], _lexDictList[i])

    FeatureNotCopy()

    # deal with feature enrichment
    for i in range(0, len(_lexDictList)):
        enrichFeature( _lexDictList[i])

    # compare the corresponding lexicons of same level
    compareLex(_lexYdict,_lexicon1dict)
    compareLex(_compoundYdict, _lexicon2dict)

    printNewLex(lexYLocation,_lexYdict,_lexYCommentdict)
    printNewLex(lexY3colonsLocation, _lexY3colonsdict, _lexY3colonsCommentdict)
    printNewLex(lexYformsLocation, _lexYformsdict, _lexYformsCommentdict)
    printNewLex(lexicon1Location,_lexicon1dict,_lexicon1Commentdict)
    printNewLex(compoundYLocation, _compoundYdict,_compoundYCommentdict)
    printNewLex(lexicon2Location, _lexicon2dict,_lexicon2Commentdict)





