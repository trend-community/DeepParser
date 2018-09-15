import shutil
from Lexicon import *
from shutil import copyfile
import utils

_CommentDictZidian = {}
_LexiconDictZidian = {}
_CommentDictB = {}
_LexiconDictB = {}
_CommentDictP = {}
_LexiconDictP = {}
_CommentDictL = {}
_LexiconDictL = {}
_CommentDictI = {}
_LexiconDictI = {}
_CommentDictI4 = {}
_LexiconDictI4 = {}

_CommentDictLexX = {}
_LexiconDictLexX = {}
_CommentDictLexXc2c3 = {}
_LexiconDictLexXc2c3 = {}

_LexiconDictLexXOrig = {}
_LexiconDictLexXc2c3Orig = {}
_LexiconDictDefXOrig = {}

_CommentDictDefX = {}
_LexiconDictDefX = {}

_LexiconDictPlus = {}
_CommentDictPlus = {}

_LexiconDictDefPlus = {}

_LexiconDictDefPlusX = {}
_LexiconDictLexPlusX = {}
_LexiconDictLexc2c3PlusX = {}


_MissingStem = set()
_FeatureNotCopy = set()
dictList = [_LexiconDictZidian, _LexiconDictLexX, _LexiconDictLexXc2c3, _LexiconDictL, _LexiconDictDefX, _LexiconDictB, _LexiconDictI, _LexiconDictI4, _LexiconDictP]

dir_path = os.path.dirname(os.path.realpath(__file__))


paraMain = dir_path + '/../../fsa/X/main2017.txt'
newPlus = dir_path + "/../../fsa/X/LexXplus.txt"
paraDefPlus = dir_path + "/../../fsa/X/defPlus.txt"
paraFeatureNotCopy = dir_path + "/../../fsa/Y/FeatureNotCopy.txt"

def OrganizeLex(lexiconLocation, _CommentDict, _LexiconDict):
    with open(lexiconLocation, encoding='utf-8') as dictionary:
        oldWord = "firstCommentLine"
        for line in dictionary:
            if line.startswith("//"):
                if _CommentDict.get(oldWord):
                    _CommentDict.update({oldWord:_CommentDict.get(oldWord)+line})
                else:
                    _CommentDict.update({oldWord: line})
                continue
            code, comment = utils.SeparateComment(line)
            blocks = [x.strip() for x in re.split(":", code) if x]
            if len(blocks) != 2:
                continue
            newNode = False

            node = SearchLexicon(blocks[0], 'origin')
            # node = None
            if not node:
                newNode = True
                node = LexiconNode(blocks[0])
                if "_" in node.text:
                    node.forLookup = True       #for those combination words.
                if comment:
                    node.comment = comment
            # else:
            #     logging.debug("This word is repeated in lexicon: %s" % blocks[0])
            features, node = SplitFeaturesWithSemicolon(blocks[1], node)
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
                        logging.info("Missing Feature: " + feature)
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

            if newNode:
                _LexiconDict.update({node.text: node})
                # logging.debug(node.word)
            oldWord = blocks[0]

    logging.info("Finish loading lexicon" + lexiconLocation)


def FeatureNotCopy():
    with open(paraFeatureNotCopy, encoding='utf-8') as file:
        for line in file:
            if line.startswith("//"):
                continue
            line = line.strip()
            line = GetFeatureID(line)
            _FeatureNotCopy.add(line)

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

    else:
        origFeatures = FeatureString.split()
        for feature in origFeatures:
            node.origFeatures.add(GetFeatureID(feature))

    if ";" in FeatureString:
        FeatureString = FeatureString.replace(";", " ")

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
            temp = set(feature1).union(set(feature2))
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

            if _LexiconDict1 == _LexiconDictDefX:
                # logging.debug("def " + word)
                _LexiconDictDefPlusX.update({word:node1})
            elif _LexiconDict1 == _LexiconDictLexX:
                # logging.debug("lexx " + word)
                _LexiconDictLexPlusX.update({word:node1})
            elif _LexiconDict1 == _LexiconDictLexXc2c3:
                _LexiconDictLexc2c3PlusX.update({word:node1})

            removeWord.add(word)

    # print (len(removeWord))

    for word in removeWord:
        print ("repeated word is " + word)
        del _LexiconDict2[word]



def EnrichFeature( _LexiconDict):

    for word in _LexiconDict.keys():
        node = _LexiconDict.get(word)
        features = node.features
        featureID = GetFeatureID('F')
        if featureID in features:
            stem = node.norm
            norm = node.atom
            # logging.debug("words to be enriched " + word + ", stem is " + stem + ", norm is " + norm)
            stemFeatures = None
            if stem != word:
                stemFeatures = GetStemFeatures(stem)
            elif norm != word:
                stemFeatures = GetStemFeatures(norm)
            # else:
                # logging.debug("no stem or norm is labeled to enrich features" + word)
            if stemFeatures:
                node.stemFeatures = set()
                node.stemFeatures.update(stemFeatures)
                res = features.union(stemFeatures)
                node.features = res
                _LexiconDict.update({word:node})


    return _LexiconDict

def GetStemFeatures(word):
    for d in dictList:
        if word in d.keys():
            node = d.get(word)
            features = node.stemFeatures
            copyFeatures = features.copy()

            for ID in features:
                if ID in _FeatureNotCopy:
                    copyFeatures.remove(ID)
                    # ontologynode = SearchFeatureOntology(ID)
                    # if ontologynode:
                    #     ancestors = ontologynode.ancestors
                    #     if ancestors:
                    #         copyFeatures = copyFeatures.difference(ancestors)

            return copyFeatures
    # logging.debug("stem does not exist" + word)
    _MissingStem.add(word)
    return None

def AlignMain():
    newloc = "outputMain.txt"
    with open(newloc, 'w',encoding='utf-8') as file:
        with open(paraMain, encoding='utf-8') as dictionary:
            for line in dictionary:
                if line.startswith("//"):
                    file.write(line)
                    continue
                code, comment = utils.SeparateComment(line)
                if (code not in _LexiconDictB.keys()) and (code not in _LexiconDictP.keys()) and (code not in _LexiconDictL.keys()) and (code not in _LexiconDictI.keys()) and (code not in _LexiconDictI4.keys()) and (code not in _LexiconDictLexX.keys()) and (code not in _LexiconDictDefX.keys()):
                    file.write(code + " " + comment + "\n")
    shutil.move(newloc,paraMain)


def AddDefandLexX():

    for word in _LexiconDictDefPlusX.keys():
        _LexiconDictDefX.update({word:_LexiconDictDefPlusX.get(word)})
    logging.debug(len(_LexiconDictDefX))

    for word in _LexiconDictLexPlusX.keys():
        _LexiconDictLexX.update({word:_LexiconDictLexPlusX.get(word)})
    logging.debug(len(_LexiconDictLexX))

    for word in _LexiconDictLexc2c3PlusX.keys():
        _LexiconDictLexXc2c3.update({word:_LexiconDictLexc2c3PlusX.get(word)})
    logging.debug(len(_LexiconDictLexXc2c3))


def printNewLex(_CommentDictTemp, _LexiconDictTemp, newloc):
    s = sorted(_LexiconDictTemp.keys(), key=lambda x: (RealLength(x), x))
    with open(newloc, 'w',encoding='utf-8') as file:
        output = ""
        if _CommentDictTemp.get("firstCommentLine"):
            output += _CommentDictTemp.get("firstCommentLine") + "\n"
        oldWord = None
        logging.debug("the size of " + newloc + " is: " + str(len(_LexiconDictTemp)))
        for word in s:
            if oldWord in _CommentDictTemp.keys():
                output += _CommentDictTemp[oldWord]
            output += _LexiconDictTemp.get(word).entry() + "\n"
            oldWord = word
        file.write(output+"\n")


def FeaturesMorethanFour():
    lexList = [_LexiconDictB, _LexiconDictI, _LexiconDictI4, _LexiconDictP, _LexiconDictL]

    for lex in lexList:

        removeWord = set()
        for word in lex.keys():
            node = lex.get(word)
            features = sorted(node.features)
            featuresCopy = features.copy()
            # remove redundant ancestors.
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

            featureSorted = sorted(featureSorted)

            if len(featureSorted) >= 5:
                logging.debug("length is larger than 4 " + word)
                _LexiconDictLexX.update({word: lex.get(word)})
                removeWord.add(word)
        for word in removeWord:
            del lex[word]

    removeWord = set()
    for word in _LexiconDictDefX.keys():
        node = _LexiconDictDefX.get(word)
        featuresCopy = node.features.copy()
        for feature in node.features:
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

        featureSorted = sorted(featureSorted)

        for feature in featureSorted:
            if ("A" in featureSorted and "NNP" in featureSorted) or ("V" in featureSorted and "NNP" in featureSorted) or ("NN" in featureSorted and "NNP" in featureSorted) :
                featureSorted.remove("NNP")
                featureID = GetFeatureID("NNP")
                featuresCopy.remove(featureID)
                node.features = featuresCopy
                if word in _LexiconDictLexX.keys():
                    _LexiconDictLexX.update({word:node})
                else:
                    _LexiconDictLexXc2c3.update({word: node})
                removeWord.add(word)

    for word in removeWord:
        del _LexiconDictDefX[word]


def GenerateLexPlus():
    logging.debug("size of original def is " + str(len(_LexiconDictDefXOrig)))
    logging.debug("size of original lex is " + str(len(_LexiconDictLexXOrig)))
    cpbID = GetFeatureID("cPB")
    canPBID = GetFeatureID("canPB")
    cannotPBID = GetFeatureID("cannotPB")
    notDeID = GetFeatureID("notDe")
    orQID = GetFeatureID("orQ")
    perfectID = GetFeatureID("perfect")
    abID = GetFeatureID("ab")
    aabbID = GetFeatureID("aabb")
    xyID = GetFeatureID("xy")
    neutralID = GetFeatureID("NEUTRAL")
    for lexDic in dictList:
        for word in lexDic.keys():
            node = lexDic.get(word)
            featuresID = node.features

            if cpbID in featuresID:
                if " " in word:

                    first = word[0:word.index(" ")]
                    second = word[word.index(" ")+1 : len(word)]
                else:
                    first = word[0:1]
                    second = word[1:len(word)]

                # canPB feature
                newWord = first + "得" + second
                if (newWord not in _LexiconDictB.keys()) and (newWord not in _LexiconDictP.keys()) and (newWord not in _LexiconDictL.keys()) and (newWord not in _LexiconDictI.keys()) and (newWord not in _LexiconDictI4.keys()) and (newWord not in _LexiconDictLexXOrig.keys()) and (newWord not in _LexiconDictLexXc2c3Orig.keys()) and (newWord not in _LexiconDictDefXOrig.keys()):
                    copyFeatures = set(featuresID.copy())
                    copyFeatures.remove(cpbID)
                    copyFeatures.add(canPBID)
                    newNode = LexiconNode(newWord)
                    newNode.atom = first + second
                    newNode.text = newWord
                    newNode.features = copyFeatures
                    newNode.norm = newWord
                    if len(newWord) >= 5:
                        _LexiconDictPlus.update({newWord: newNode})
                    else:
                        _LexiconDictDefPlus.update({newWord: newNode})
                else:
                    logging.debug("duplicate1 :" + newWord)

                if len(word) == 2 and word[1] == "出":
                    newWord = word[0] + "得" + word[1] + "来"
                    if (newWord not in _LexiconDictB.keys()) and (newWord not in _LexiconDictP.keys()) and (
                    newWord not in _LexiconDictL.keys()) and (newWord not in _LexiconDictI.keys()) and (
                    newWord not in _LexiconDictI4.keys()) and (newWord not in _LexiconDictLexXOrig.keys()) and (
                        newWord not in _LexiconDictDefXOrig.keys()):
                        copyFeatures = set(featuresID.copy())
                        if cpbID in copyFeatures:
                            copyFeatures.remove(cpbID)
                        copyFeatures.add(canPBID)
                        newNode = LexiconNode(newWord)
                        newNode.atom = first + second
                        newNode.text= newWord
                        newNode.features = copyFeatures
                        newNode.norm = newWord
                        _LexiconDictDefPlus.update({newWord: newNode})
                    else:
                        logging.debug("duplicate2 :" + newWord)

                newWord = first + "不" + first + "得" + second
                if (newWord not in _LexiconDictB.keys()) and (newWord not in _LexiconDictP.keys()) and (newWord not in _LexiconDictL.keys()) and (newWord not in _LexiconDictI.keys()) and (newWord not in _LexiconDictI4.keys()) and (newWord not in _LexiconDictLexXOrig.keys()) and (newWord not in _LexiconDictLexXc2c3Orig.keys())and (newWord not in _LexiconDictDefXOrig.keys()):
                    copyFeatures = set(featuresID.copy())
                    if cpbID in copyFeatures:
                        copyFeatures.remove(cpbID)
                    copyFeatures.add(canPBID)
                    copyFeatures.add(orQID)
                    newNode = LexiconNode(newWord)
                    newNode.atom = first + second
                    newNode.text = newWord
                    newNode.features = copyFeatures
                    newNode.norm = newWord
                    _LexiconDictPlus.update({newWord: newNode})
                else:
                    logging.debug("duplicate3 :" + newWord)

                newWord = first + "不" + first + "的" + second
                if (newWord not in _LexiconDictB.keys()) and (newWord not in _LexiconDictP.keys()) and (newWord not in _LexiconDictL.keys()) and (newWord not in _LexiconDictI.keys()) and (newWord not in _LexiconDictI4.keys()) and (newWord not in _LexiconDictLexXOrig.keys()) and (newWord not in _LexiconDictLexXc2c3Orig.keys())and (newWord not in _LexiconDictDefXOrig.keys()):
                    copyFeatures = set(featuresID.copy())
                    if cpbID in copyFeatures:
                        copyFeatures.remove(cpbID)
                    copyFeatures.add(canPBID)
                    copyFeatures.add(orQID)
                    newNode = LexiconNode(newWord)
                    newNode.atom = first + second
                    newNode.text = newWord
                    newNode.norm = newWord
                    newNode.features = copyFeatures
                    _LexiconDictPlus.update({newWord: newNode})
                else:
                    logging.debug("duplicate4 :" + newWord)

                newWord = first + "没" + first + "得" + second
                if (newWord not in _LexiconDictB.keys()) and (newWord not in _LexiconDictP.keys()) and (newWord not in _LexiconDictL.keys()) and (newWord not in _LexiconDictI.keys()) and (newWord not in _LexiconDictI4.keys()) and (newWord not in _LexiconDictLexXOrig.keys()) and (newWord not in _LexiconDictLexXc2c3Orig.keys())and (newWord not in _LexiconDictDefXOrig.keys()):
                    copyFeatures = set(featuresID.copy())
                    if cpbID in copyFeatures:
                        copyFeatures.remove(cpbID)
                    copyFeatures.add(canPBID)
                    copyFeatures.add(orQID)
                    copyFeatures.add(perfectID)
                    newNode = LexiconNode(newWord)
                    newNode.atom = first + second
                    newNode.text = newWord
                    newNode.features = copyFeatures
                    newNode.norm = newWord
                    _LexiconDictPlus.update({newWord: newNode})
                else:
                    logging.debug("duplicate5 :" + newWord)

                newWord = first + "没" + first + "的" + second
                if (newWord not in _LexiconDictB.keys()) and (newWord not in _LexiconDictP.keys()) and (newWord not in _LexiconDictL.keys()) and (newWord not in _LexiconDictI.keys()) and (newWord not in _LexiconDictI4.keys()) and (newWord not in _LexiconDictLexXOrig.keys()) and (newWord not in _LexiconDictLexXc2c3Orig.keys())and (newWord not in _LexiconDictDefXOrig.keys()):
                    copyFeatures = set(featuresID.copy())
                    if cpbID in copyFeatures:
                        copyFeatures.remove(cpbID)
                    copyFeatures.add(canPBID)
                    copyFeatures.add(orQID)
                    copyFeatures.add(perfectID)
                    newNode = LexiconNode(newWord)
                    newNode.atom = first + second
                    newNode.text = newWord
                    newNode.norm = newWord
                    newNode.features = copyFeatures
                    _LexiconDictPlus.update({newWord: newNode})
                else:
                    logging.debug("duplicate6 :" + newWord)

                newWord = first + "不" + second
                if (newWord not in _LexiconDictB.keys()) and (newWord not in _LexiconDictP.keys()) and (newWord not in _LexiconDictL.keys()) and (newWord not in _LexiconDictI.keys()) and (newWord not in _LexiconDictI4.keys()) and (newWord not in _LexiconDictLexXOrig.keys()) and (newWord not in _LexiconDictLexXc2c3Orig.keys())and (newWord not in _LexiconDictDefXOrig.keys()):
                    copyFeatures = set(featuresID.copy())
                    if cpbID in copyFeatures:
                        copyFeatures.remove(cpbID)
                    copyFeatures.add(cannotPBID)
                    newNode = LexiconNode(newWord)
                    newNode.atom = first + second
                    newNode.text = newWord
                    newNode.features = copyFeatures
                    newNode.norm = newWord
                    if len(newWord) >= 5:
                        _LexiconDictPlus.update({newWord: newNode})
                    else:
                        _LexiconDictDefPlus.update({newWord: newNode})
                else:
                    logging.debug("duplicate7 :" + newWord)

                newWord = first + "也" + first + "不" + second
                if (newWord not in _LexiconDictB.keys()) and (newWord not in _LexiconDictP.keys()) and (
                    newWord not in _LexiconDictL.keys()) and (newWord not in _LexiconDictI.keys()) and (
                    newWord not in _LexiconDictI4.keys()) and (newWord not in _LexiconDictLexXOrig.keys()) and (newWord not in _LexiconDictLexXc2c3Orig.keys()) and (
                    newWord not in _LexiconDictDefXOrig.keys()):
                    copyFeatures = set(featuresID.copy())
                    if cpbID in copyFeatures:
                        copyFeatures.remove(cpbID)
                    copyFeatures.add(cannotPBID)
                    newNode = LexiconNode(newWord)
                    newNode.atom = first + second
                    newNode.text = newWord
                    newNode.features = copyFeatures
                    newNode.norm = newWord
                    _LexiconDictPlus.update({newWord: newNode})
                else:
                    logging.debug("duplicate7 :" + newWord)

                newWord = first + "都" + first + "不" + second
                if (newWord not in _LexiconDictB.keys()) and (newWord not in _LexiconDictP.keys()) and (
                            newWord not in _LexiconDictL.keys()) and (newWord not in _LexiconDictI.keys()) and (
                            newWord not in _LexiconDictI4.keys()) and (newWord not in _LexiconDictLexXOrig.keys()) and (newWord not in _LexiconDictLexXc2c3Orig.keys()) and (
                            newWord not in _LexiconDictDefXOrig.keys()):
                    copyFeatures = set(featuresID.copy())
                    if cpbID in copyFeatures:
                        copyFeatures.remove(cpbID)
                    copyFeatures.add(cannotPBID)
                    newNode = LexiconNode(newWord)
                    newNode.atom = first + second
                    newNode.text = newWord
                    newNode.features = copyFeatures
                    newNode.norm = newWord
                    _LexiconDictPlus.update({newWord: newNode})
                else:
                    logging.debug("duplicate7 :" + newWord)


                if len(word) == 2 and word[1] == "出":
                    newWord = word[0] + "不" + word[1] + "来"
                    if (newWord not in _LexiconDictB.keys()) and (newWord not in _LexiconDictP.keys()) and (
                    (newWord not in _LexiconDictL.keys())) and (newWord not in _LexiconDictI.keys()) and (
                    (newWord not in _LexiconDictI4.keys())) and (newWord not in _LexiconDictLexXOrig.keys())  and (newWord not in _LexiconDictLexXc2c3Orig.keys()) and (
                        newWord not in _LexiconDictDefXOrig.keys()):
                        copyFeatures = set(featuresID.copy())
                        if cpbID in copyFeatures:
                            copyFeatures.remove(cpbID)
                        copyFeatures.add(cannotPBID)
                        newNode = LexiconNode(newWord)
                        newNode.atom = first + second
                        newNode.text = newWord
                        newNode.features = copyFeatures
                        newNode.norm = newNode.text
                        _LexiconDictDefPlus.update({newWord: newNode})
                    else:
                        logging.debug("duplicate8 :" + newWord)

                if notDeID in featuresID:
                    copyFeatures = set(featuresID.copy())
                    copyFeatures.add(canPBID)
                    newWord = first + "的" + second
                    if (newWord not in _LexiconDictB.keys()) and (newWord not in _LexiconDictP.keys()) and (
                    newWord not in _LexiconDictL.keys()) and (newWord not in _LexiconDictI.keys()) and (
                    newWord not in _LexiconDictI4.keys()) and (newWord not in _LexiconDictLexXOrig.keys()) and (newWord not in _LexiconDictLexXc2c3Orig.keys()) and (
                        newWord not in _LexiconDictDefXOrig.keys()):
                        newNode = LexiconNode(newWord)
                        newNode.atom = first + second
                        newNode.text = newWord
                        newNode.features = copyFeatures
                        newNode.norm = newWord
                        if len(newWord) >= 5:
                            _LexiconDictPlus.update({newWord: newNode})
                        else:
                            _LexiconDictDefPlus.update({newWord: newNode})
                    else:
                        logging.debug("duplicate9 :" + newWord)

                    if len(word) == 2 and word[1] == "出":
                        newWord = word[0] + "的" + word[1] + "来"
                        if (newWord not in _LexiconDictB.keys()) and (newWord not in _LexiconDictP.keys()) and (
                        newWord not in _LexiconDictL.keys()) and (newWord not in _LexiconDictI.keys()) and (
                        newWord not in _LexiconDictI4.keys()) and (newWord not in _LexiconDictLexXOrig.keys()) and (newWord not in _LexiconDictLexXc2c3Orig.keys()) and (
                            newWord not in _LexiconDictDefXOrig.keys()):
                            newNode = LexiconNode(newWord)
                            newNode.atom = first + second
                            newNode.text = newWord
                            newNode.features = copyFeatures
                            newNode.norm = newNode.text
                            _LexiconDictDefPlus.update({newWord: newNode})
                        else:
                            logging.debug("duplicate10 :" + newWord)

            if abID in featuresID and len(word) == 2:
                copyFeatures = set(featuresID.copy())
                first = word[0]
                second = word[1]
                newWord = first + first + second + second
                if (newWord not in _LexiconDictB.keys()) and (newWord not in _LexiconDictP.keys()) and (newWord not in _LexiconDictL.keys()) and (newWord not in _LexiconDictI.keys()) and (newWord not in _LexiconDictI4.keys()) and (newWord not in _LexiconDictLexXOrig.keys()) and (newWord not in _LexiconDictLexXc2c3Orig.keys()) and (newWord not in _LexiconDictDefXOrig.keys()):
                    newNode = LexiconNode(newWord)
                    copyFeatures.remove(abID)
                    copyFeatures.add(aabbID)
                    newNode.features = copyFeatures
                    _LexiconDictPlus.update({newWord: newNode})

            if xyID in featuresID and len(word) == 2:
                first = word[0]
                second = word[1]
                startwithFirstDict = LexStartWithChar(first)
                startwithSecondDict = LexStartWithChar(second)
                commonpart = set(startwithFirstDict.keys()).intersection(set(startwithSecondDict.keys()))
                for char in commonpart:
                    newWord = word + char
                    if (newWord not in _LexiconDictB.keys()) and (newWord not in _LexiconDictP.keys()) and (newWord not in _LexiconDictL.keys()) and (newWord not in _LexiconDictI.keys()) and (newWord not in _LexiconDictI4.keys()) and (newWord not in _LexiconDictLexXOrig.keys()) and (newWord not in _LexiconDictLexXc2c3Orig.keys()) and (newWord not in _LexiconDictDefXOrig.keys()):

                        newNode = LexiconNode(newWord)
                        newNode.text = newWord
                        newNode.norm = first + char + second + char
                        newNode.features = startwithFirstDict.get(char).features
                        newNode.features.add(neutralID)
                        _LexiconDictDefPlus.update({newWord: newNode})

                    # newWord = word[1] + word[0] + char
                    # if (newWord not in _LexiconDictB.keys()) and (newWord not in _LexiconDictP.keys()) and (newWord not in _LexiconDictL.keys()) and (newWord not in _LexiconDictI.keys()) and (newWord not in _LexiconDictI4.keys()) and (newWord not in _LexiconDictLexXOrig.keys()) and (newWord not in _LexiconDictDefXOrig.keys()):
                    #     newNode = LexiconNode(newWord)
                    #     newNode.word = newWord
                    #     newNode.stem = first + char + second + char
                    #     newNode.features = startwithFirstDict.get(char).features
                    #     _LexiconDictDefPlus.update({newWord: newNode})

    logging.debug("lexx plus size is " + str(len(_LexiconDictPlus)))
    logging.debug("def lexx plus size is " + str(len(_LexiconDictDefPlus)))


def LexStartWithChar(startingChar):
    res = {}
    for lexDic in dictList:
        for word in lexDic.keys():
            if len(word) == 2 and word[0] == startingChar and word[1] != startingChar:
                newNode = LexiconNode(word[1])
                newNode.features = lexDic.get(word).features
                res.update({word[1]: newNode})
    return res


def printLexPlus(loc, _LexiconDictTemp):
    s = sorted(_LexiconDictTemp.keys(), key=lambda x: (RealLength(x), x))
    with open(loc, 'w', encoding='utf-8') as file:
        for word in s:
            output = word + ": "
            node = _LexiconDictTemp.get(word)
            featuresCopy = node.features.copy()
            for feature in node.features:
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
            featureSorted = sorted(featureSorted)
            for feature in featureSorted:
                output += feature + " "
            if node.norm != node.text:
                output += "'" + node.norm + "' "
            if node.atom != node.text:
                output += "/" + node.atom + "/ "
            if node.missingfeature != "":
                output += node.missingfeature
            if hasattr(node, "comment"):
                output += node.comment
            file.write(output + "\n")

def printMissingStem():
    loc = dir_path + '/../../fsa/X/missingStem.txt'
    with open(loc, 'w', encoding='utf-8') as file:
        for word in _MissingStem:
            file.write(word + "\n")

def printSummaryLex():
    loc = dir_path + '/../../fsa/X/summaryLex.txt'
    summary = [_LexiconDictZidian, _LexiconDictLexX, _LexiconDictL, _LexiconDictDefX, _LexiconDictB, _LexiconDictI, _LexiconDictI4, _LexiconDictP,_LexiconDictPlus, _LexiconDictDefPlus]
    with open(loc, 'w', encoding='utf-8') as file:
        for dict in summary:
            if dict == _LexiconDictLexX:
                origLoc = "LexX"
            elif dict == _LexiconDictL:
                origLoc = "locX"
            elif dict == _LexiconDictDefX:
                origLoc = "defLexX"
            elif dict == _LexiconDictB:
                origLoc = "brandX"
            elif dict == _LexiconDictI:
                origLoc = "idiomX"
            elif dict == _LexiconDictI4:
                origLoc = "idiom4X"
            elif dict == _LexiconDictP:
                origLoc = "perX"
            elif dict == _LexiconDictPlus:
                origLoc = "LexXplus"
            elif dict == _LexiconDictDefPlus:
                origLoc = "defPlus"
            else:
                origLoc = "unknown"
            for word in dict.keys():
                file.write(word + "\t" + origLoc + "\n")

def printSenti(posloc, negloc):
    summary = [_LexiconDictLexX, _LexiconDictL, _LexiconDictDefX, _LexiconDictB, _LexiconDictI, _LexiconDictI4,
               _LexiconDictP, _LexiconDictPlus, _LexiconDictDefPlus]
    pCID = GetFeatureID("pC")
    nCID = GetFeatureID("nC")
    with open(posloc, 'w', encoding='utf-8') as file:
        for d in summary:
            for word in d.keys():
                node = d.get(word)
                features = node.features
                if pCID in features:
                    file.write(word + "\n")
    with open(negloc, 'w', encoding='utf-8') as file:
        for d in summary:
            for word in d.keys():
                node = d.get(word)
                features = node.features
                if nCID in features:
                    file.write(word + "\n")

#
# def OrgDanzi():
#     for i in range(1, len(dictList)):
#     #     danziSet = set()
#         dict = dictList[i]
#         for word in dict.keys():
#             if len(word) == 1:
#                 node = dict.get(word)
#                 print ("words that will be put in danzi " + word)
#                 _LexiconDictZidian.update({word: node})
#                 # danziSet.add(word)




if __name__ == "__main__":
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    if len(sys.argv) != 1:
        print("Usage: python OrgLex.py")
        exit(0)
    command = sys.argv[0]

    paraZidian = dir_path + '/../../fsa/X/LexX-zidian.txt'
    paraZidianTemp = dir_path + '/../../temp/X/LexX-zidian_copy.txt'

    # if not os.path.exists(paraZidian):
    #     with open(paraZidian,'w'): pass
    #
    #
    if not os.path.exists(dir_path + '/../../temp/X/'):
        os.mkdir(dir_path + '/../../temp/' )
        os.mkdir(dir_path + '/../../temp/X/')

    paraB = dir_path + '/../../fsa/X/LexX-brandX.txt'
    paraBTemp = dir_path + '/../../temp/X/LexX-brandX_copy.txt'

    paraP = dir_path + '/../../fsa/X/LexX-perX.txt'
    paraPTemp = dir_path + '/../../temp/X/LexX-perX_copy.txt'

    paraL = dir_path + '/../../fsa/X/LexX-locX.txt'
    paraLTemp = dir_path + '/../../temp/X/LexX-locX_copy.txt'

    paraI = dir_path + '/../../fsa/X/LexX-idiomX.txt'
    paraITemp = dir_path + '/../../temp/X/LexX-idiomX_copy.txt'

    paraI4 = dir_path + '/../../fsa/X/LexX-idiomXdomain.txt'
    paraI4Temp = dir_path + '/../../temp/X/LexX-idiomXdomain_copy.txt'

    paraLex = dir_path + '/../../fsa/X/LexX.txt'
    paraLexTemp = dir_path + '/../../temp/X/LexX_copy.txt'

    paraLexc2c3 = dir_path + '/../../fsa/X/LexXc2c3.txt'
    paraLexc2c3Temp = dir_path + '/../../temp/X/LexXc2c3_copy.txt'

    paraDef = dir_path + '/../../fsa/X/defLexX.txt'
    paraDefTemp = dir_path + '/../../temp/X/defLexX_copy.txt'

    copyfile(paraZidian, paraZidianTemp)
    copyfile(paraB, paraBTemp)
    copyfile(paraP, paraPTemp)
    copyfile(paraL, paraLTemp)
    copyfile(paraI, paraITemp)
    copyfile(paraI4, paraI4Temp)
    copyfile(paraLex, paraLexTemp)
    copyfile(paraLexc2c3, paraLexc2c3Temp)
    copyfile(paraDef, paraDefTemp)


    LoadFeatureOntology(dir_path + '/../../fsa/Y/feature.txt')
    FeatureNotCopy()

    OrganizeLex(paraZidian, _CommentDictZidian, _LexiconDictZidian)
    OrganizeLex(paraB, _CommentDictB, _LexiconDictB)
    OrganizeLex(paraP, _CommentDictP, _LexiconDictP)
    OrganizeLex(paraL, _CommentDictL, _LexiconDictL)
    OrganizeLex(paraI, _CommentDictI, _LexiconDictI)
    OrganizeLex(paraI4, _CommentDictI4, _LexiconDictI4)
    OrganizeLex(paraLex, _CommentDictLexX, _LexiconDictLexX)
    OrganizeLex(paraLexc2c3, _CommentDictLexXc2c3, _LexiconDictLexXc2c3)
    OrganizeLex(paraDef, _CommentDictDefX, _LexiconDictDefX)

    _LexiconDictZidian = EnrichFeature(_LexiconDictZidian)
    _LexiconDictI = EnrichFeature(_LexiconDictI)
    _LexiconDictB = EnrichFeature(_LexiconDictB)
    _LexiconDictP = EnrichFeature(_LexiconDictP)
    _LexiconDictI4 = EnrichFeature(_LexiconDictI4)
    _LexiconDictL = EnrichFeature(_LexiconDictL)
    _LexiconDictLexX = EnrichFeature(_LexiconDictLexX)
    _LexiconDictLexXc2c3 = EnrichFeature(_LexiconDictLexXc2c3)
    _LexiconDictDefX = EnrichFeature(_LexiconDictDefX)


    AlignMain()
    compareLex(_LexiconDictZidian, _LexiconDictB)
    compareLex(_LexiconDictZidian, _LexiconDictP)
    compareLex(_LexiconDictZidian, _LexiconDictL)
    compareLex(_LexiconDictZidian, _LexiconDictI)
    compareLex(_LexiconDictZidian, _LexiconDictI4)

    compareLex(_LexiconDictB, _LexiconDictP)
    compareLex(_LexiconDictB, _LexiconDictL)
    compareLex(_LexiconDictB, _LexiconDictI)
    compareLex(_LexiconDictB, _LexiconDictI4)

    compareLex(_LexiconDictP, _LexiconDictL)
    compareLex(_LexiconDictP, _LexiconDictI)
    compareLex(_LexiconDictP, _LexiconDictI4)

    compareLex(_LexiconDictL, _LexiconDictI)
    compareLex(_LexiconDictL, _LexiconDictI4)

    compareLex(_LexiconDictI, _LexiconDictI4)

    compareLex(_LexiconDictLexX, _LexiconDictB)
    compareLex(_LexiconDictLexX, _LexiconDictP)
    compareLex(_LexiconDictLexX, _LexiconDictL)
    compareLex(_LexiconDictLexX, _LexiconDictI)
    compareLex(_LexiconDictLexX, _LexiconDictI4)

    compareLex(_LexiconDictLexXc2c3, _LexiconDictB)
    compareLex(_LexiconDictLexXc2c3, _LexiconDictP)
    compareLex(_LexiconDictLexXc2c3, _LexiconDictL)
    compareLex(_LexiconDictLexXc2c3, _LexiconDictI)
    compareLex(_LexiconDictLexXc2c3, _LexiconDictI4)

    compareLex(_LexiconDictZidian, _LexiconDictLexXc2c3)
    compareLex(_LexiconDictZidian, _LexiconDictLexX)
    compareLex(_LexiconDictLexX, _LexiconDictLexXc2c3)


    compareLex(_LexiconDictDefX,_LexiconDictB)
    compareLex(_LexiconDictDefX, _LexiconDictP)
    compareLex(_LexiconDictDefX, _LexiconDictL)
    compareLex(_LexiconDictDefX,_LexiconDictI)
    compareLex(_LexiconDictDefX, _LexiconDictI4)
    compareLex(_LexiconDictDefX, _LexiconDictLexX)
    compareLex(_LexiconDictDefX, _LexiconDictLexXc2c3)
    compareLex(_LexiconDictDefX, _LexiconDictZidian)


    _LexiconDictDefXOrig = _LexiconDictDefX.copy()
    _LexiconDictLexXOrig = _LexiconDictLexX.copy()
    _LexiconDictLexXc2c3Orig = _LexiconDictLexXc2c3.copy()

    AddDefandLexX()

    FeaturesMorethanFour()

    printNewLex(_CommentDictZidian, _LexiconDictZidian, paraZidian)

    printNewLex(_CommentDictB, _LexiconDictB, paraB)

    printNewLex(_CommentDictP, _LexiconDictP, paraP)

    printNewLex(_CommentDictL, _LexiconDictL, paraL)

    printNewLex(_CommentDictI, _LexiconDictI, paraI)

    printNewLex(_CommentDictI4, _LexiconDictI4, paraI4)

    printNewLex(_CommentDictLexX, _LexiconDictLexX, paraLex)
    printNewLex(_CommentDictLexXc2c3, _LexiconDictLexXc2c3, paraLexc2c3)
    printNewLex(_CommentDictDefX, _LexiconDictDefX, paraDef)


    GenerateLexPlus()
    printLexPlus(newPlus, _LexiconDictPlus)
    printLexPlus(paraDefPlus, _LexiconDictDefPlus)

    printMissingStem()
    printSummaryLex()

    # parapos = dir_path + '/../../fsa/X/positive.txt'
    # paraneg = dir_path + '/../../fsa/X/negative.txt'
    # printSenti(parapos,paraneg)


