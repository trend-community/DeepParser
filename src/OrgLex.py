import shutil
from FeatureOntology import *
from Lexicon import *

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

_CommentDictDefX = {}
_LexiconDictDefX = {}

_LexiconDictPlus = {}
_CommentDictPlus = {}

_LexiconDictDefPlus = {}

_LexiconDictDefPlusX = {}
_LexiconDictLexPlusX = {}

dictList = [_LexiconDictLexX,_LexiconDictL,_LexiconDictDefX,_LexiconDictB,_LexiconDictI,_LexiconDictI4,_LexiconDictP]

dir_path = os.path.dirname(os.path.realpath(__file__))
paraLex = dir_path + '/../../fsa/X/LexX.txt'
paraDef = dir_path + '/../../fsa/X/defLexX.txt'
paraMain = dir_path + '/../../fsa/X/main2017.txt'
newPlus = dir_path + "/../../fsa/X/LexXplus.txt"
paraDefPlus = dir_path + "/../../fsa/X/defPlus.txt"

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
            code, comment = SeparateComment(line)
            blocks = [x.strip() for x in re.split(":", code) if x]
            if len(blocks) != 2:
                continue
            newNode = False
            node = SearchLexicon(blocks[0], 'origin')
            #node = None
            if not node:
                newNode = True
                node = LexiconNode(blocks[0])
                if "_" in node.word:            #TODO: to confirm.
                    node.forLookup = True       #for those combination words.
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
                        node.missingfeature += "\\" + feature
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



    logging.debug("Finish loading lexicon")

def compareLex(_LexiconDict1,_LexiconDict2, lexXandOther = False):

    removeWord = set()
    for word in _LexiconDict1.keys():
        output = word
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

            if _LexiconDict1==_LexiconDictDefX:
                # logging.debug("def " + word)
                _LexiconDictDefPlusX.update({word:node1})
            else:
                # logging.debug("lexx " + word)
                _LexiconDictLexPlusX.update({word:node1})

            removeWord.add(word)

    for word in removeWord:
        if not lexXandOther:
            del _LexiconDict1[word]
        del _LexiconDict2[word]



def AlignMain():
    newloc = "outputMain.txt"
    with open(newloc, 'w',encoding='utf-8') as file:
        with open(paraMain, encoding='utf-8') as dictionary:
            for line in dictionary:
                if line.startswith("//"):
                    file.write(line)
                    continue
                code, comment = SeparateComment(line)
                if (code not in _LexiconDictB.keys()) and (code not in _LexiconDictP.keys()) and ((code not in _LexiconDictL.keys())) and ((code not in _LexiconDictI.keys())) and ((code not in _LexiconDictI4.keys())) and (code not in _LexiconDictLexX.keys()) and (code not in _LexiconDictDefX.keys()):
                    file.write(code + comment + "\n")
    shutil.move(newloc,paraMain)




def AddDefandLexX():
    logging.debug(len(_LexiconDictDefX))
    for word in _LexiconDictDefPlusX.keys():
        _LexiconDictDefX.update({word:_LexiconDictDefPlusX.get(word)})
    logging.debug(len(_LexiconDictDefX))
    logging.debug(len(_LexiconDictLexX))
    for word in _LexiconDictLexPlusX.keys():
        _LexiconDictLexX.update({word:_LexiconDictLexPlusX.get(word)})
    logging.debug(len(_LexiconDictLexX))


def printNewLex(_CommentDictTemp, _LexiconDictTemp, newloc):
    s = sorted(_LexiconDictTemp.keys(), key=lambda x: (RealLength(x), x))
    with open(newloc, 'w',encoding='utf-8') as file:
        output = ""
        if _CommentDictTemp.get("firstCommentLine"):
            output += _CommentDictTemp.get("firstCommentLine") + "\n"
        oldWord = None
        logging.debug("the size of lexX is: " + str(len(_LexiconDictTemp)))
        for word in s:
            if oldWord in _CommentDictTemp.keys():
                output += _CommentDictTemp[oldWord]
                oldWord = word
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
            features = featureSorted
            if len(featureSorted) >= 4:
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
                _LexiconDictLexX.update({word:node})
                removeWord.add(word)

    for word in removeWord:
        del _LexiconDictDefX[word]


    #printLexSum()

def GenerateLexPlus():
    cpbID = GetFeatureID("cPB")
    canPBID = GetFeatureID("canPB")
    cannotPBID = GetFeatureID("cannotPB")
    notDeID = GetFeatureID("notDe")
    orQID = GetFeatureID("orQ")
    perfectID = GetFeatureID("perfect")
    abID = GetFeatureID("ab")
    aabbID = GetFeatureID("aabb")
    xyID = GetFeatureID("xy")
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
                newNode = LexiconNode(word)
                newNode.stem = first + second

                # canPB feature
                featuresID.remove(cpbID)
                featuresID.add(canPBID)
                newWord = first + "得" + second
                newNode.word = newWord
                newNode.features = featuresID
                newNode.norm = newWord
                if len(newWord) >= 5:
                    _LexiconDictPlus.update({newWord: newNode})
                else:
                    _LexiconDictDefPlus.update({newWord: newNode})

                if len(word)==2 and word[1]=="出":
                    newWord = word[0] + "得" + word[1] + "来"
                    newNode.features = featuresID
                    newNode.norm = newWord
                    _LexiconDictDefPlus.update({newWord: newNode})

                newWord = first + "不" + first + "得" + second
                featuresID.add(orQID)
                newNode.word = newWord
                newNode.features = featuresID
                newNode.norm = newWord
                _LexiconDictPlus.update({newWord: newNode})

                newWord = first + "不" + first + "的" + second
                newNode.word = newWord
                newNode.norm = newWord
                _LexiconDictPlus.update({newWord: newNode})

                newWord = first + "没" + first + "得" + second
                featuresID.add(perfectID)
                newNode.word = newWord
                newNode.features = featuresID
                newNode.norm = newWord
                _LexiconDictPlus.update({newWord: newNode})

                newWord = first + "没" + first + "的" + second
                newNode.word = newWord
                newNode.norm = newWord
                _LexiconDictPlus.update({newWord: newNode})

                # cannotPB feature
                newWord = first + "不" + second
                featuresID.remove(canPBID)
                featuresID.remove(orQID)
                featuresID.remove(perfectID)
                featuresID.add(cannotPBID)
                newNode.word = newWord
                newNode.features = featuresID
                newNode.norm = newWord
                if len(newWord) >= 5:
                    _LexiconDictPlus.update({newWord: newNode})
                else:
                    _LexiconDictDefPlus.update({newWord: newNode})

                if len(word)==2 and word[1]=="出":
                    newWord = word[0] + "不" + word[1] + "来"
                    newNode.word = newWord
                    newNode.features = featuresID
                    newNode.norm = newNode.word
                    _LexiconDictDefPlus.update({newWord: newNode})

                if notDeID not in featuresID:
                    featuresID.remove(cannotPBID)
                    featuresID.add(canPBID)
                    newWord = first + "的" + second
                    newNode.word = newWord
                    newNode.features = featuresID
                    newNode.norm = newWord
                    if len(newWord) >= 5:
                        _LexiconDictPlus.update({newWord: newNode})
                    else:
                        _LexiconDictDefPlus.update({newWord: newNode})
                    if len(word) == 2 and word[1] == "出":
                        newWord = word[0] + "的" + word[1] + "来"
                        newNode.word = newWord
                        newNode.features = featuresID
                        newNode.norm = newNode.word
                        _LexiconDictDefPlus.update({newWord: newNode})

            if abID in featuresID and len(word)==2:
                first = word[0]
                second = word[1]
                newWord = first + first + second + second
                newNode = LexiconNode(newWord)
                featuresID.remove(abID)
                featuresID.add(aabbID)
                newNode.features = featuresID
                _LexiconDictPlus.update({newWord: newNode})

            if xyID in featuresID and len(word) == 2:
                first = word[0]
                second = word[1]
                startwithFirstDict =  LexStartWithChar(first)
                startwithSecondDict =  LexStartWithChar(second)
                commonpart = set(startwithFirstDict.keys()).intersection(set(startwithSecondDict.keys()))
                for char in commonpart:
                    newWord = word + char
                    newNode = LexiconNode(newWord)
                    newNode.stem = first + char + second + char
                    newNode.features = startwithFirstDict.get(char).features
                    _LexiconDictDefPlus.update({newWord: newNode})

                    newWord = word[1] + word[0] + char
                    newNode = LexiconNode(newWord)
                    newNode.stem = first + char + second + char
                    newNode.features = startwithFirstDict.get(char).features
                    _LexiconDictDefPlus.update({newWord: newNode})



    logging.debug("lexx plus size is " + str(len(_LexiconDictPlus)))
    logging.debug("def lexx plus size is " + str(len(_LexiconDictDefPlus)))


def LexStartWithChar(startingChar):
    res = {}
    for lexDic in dictList:
        for word in lexDic.keys():
            if len(word) == 2 and word[0] == startingChar and word[1]!= startingChar:
                newNode = LexiconNode(word[1])
                newNode.features = lexDic.get(word).features
                res.update({word[1]:newNode})
    return res

def printLexPlus(loc, _LexiconDictTemp):
    s = sorted(_LexiconDictTemp.keys(), key=lambda x: (RealLength(x), x))
    with open(loc, 'w',encoding='utf-8') as file:
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
            if node.stem != node.word:
                output += "'" + node.stem + "' "
            if node.norm != node.word:
                output += "/" + node.norm + "/ "
            if node.missingfeature != "":
                output += node.missingfeature
            if hasattr(node, "comment"):
                output += node.comment
            file.write(output + "\n")






if __name__ == "__main__":

    logging.basicConfig( level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

    if len(sys.argv) != 1:
        print("Usage: python OrgLex.py")
        exit(0)
    command = sys.argv[0]

    LoadFeatureOntology(dir_path + '/../../fsa/Y/feature.txt')
    paraB = dir_path + '/../../fsa/X/brandX.txt'
    OrganizeLex(paraB, _CommentDictB,_LexiconDictB)
    paraP = dir_path + '/../../fsa/X/perX.txt'
    OrganizeLex(paraP, _CommentDictP, _LexiconDictP)
    paraL = dir_path + '/../../fsa/X/locX.txt'
    OrganizeLex(paraL, _CommentDictL, _LexiconDictL)
    paraI = dir_path + '/../../fsa/X/idiomX.txt'
    OrganizeLex(paraI, _CommentDictI, _LexiconDictI)
    paraI4 = dir_path + '/../../fsa/X/idiom4X.txt'
    OrganizeLex(paraI4, _CommentDictI4, _LexiconDictI4)
    OrganizeLex(paraLex, _CommentDictLexX, _LexiconDictLexX)
    OrganizeLex(paraDef, _CommentDictDefX, _LexiconDictDefX)

    AlignMain()


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


    # printNewLex(paraB, _LexiconDictB, newB)
    # printNewLex(paraP, _LexiconDictP, newP)
    # printNewLex(paraL, _LexiconDictL, newL)
    # printNewLex(paraI, _LexiconDictI, newI)
    # printNewLex(paraI4, _LexiconDictI4, newI4)


    compareLex(_LexiconDictLexX, _LexiconDictB, lexXandOther=True)
    compareLex(_LexiconDictLexX, _LexiconDictP, lexXandOther=True)
    compareLex(_LexiconDictLexX, _LexiconDictL, lexXandOther=True)
    compareLex(_LexiconDictLexX, _LexiconDictI, lexXandOther=True)
    compareLex(_LexiconDictLexX, _LexiconDictI4, lexXandOther=True)
    #
    #
    compareLex(_LexiconDictDefX, _LexiconDictB, lexXandOther=True)
    compareLex(_LexiconDictDefX, _LexiconDictP, lexXandOther=True)
    compareLex(_LexiconDictDefX, _LexiconDictL, lexXandOther=True)
    compareLex(_LexiconDictDefX, _LexiconDictI, lexXandOther=True)
    compareLex(_LexiconDictDefX, _LexiconDictI4, lexXandOther=True)
    compareLex(_LexiconDictDefX, _LexiconDictLexX, lexXandOther=True)



    AddDefandLexX()

    FeaturesMorethanFour()
    printNewLex(_CommentDictB, _LexiconDictB, paraB)

    printNewLex(_CommentDictP,_LexiconDictP, paraP)

    printNewLex(_CommentDictL,_LexiconDictL, paraL)

    printNewLex(_CommentDictI,_LexiconDictI, paraI)

    printNewLex(_CommentDictI4,_LexiconDictI4, paraI4)

    printNewLex(_CommentDictLexX, _LexiconDictLexX, paraLex)
    printNewLex(_CommentDictDefX, _LexiconDictDefX, paraDef)

    GenerateLexPlus()
    printLexPlus(newPlus, _LexiconDictPlus)
    printLexPlus(paraDefPlus, _LexiconDictDefPlus)






