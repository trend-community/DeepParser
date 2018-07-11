#!/bin/python
# read in the lookup dictionary. It is mainly used for segmenation (combining multiple tokens into one word/token)
# defLexX.txt sample: 也就: EX advJJ preXV pv rightB /就/

import string

import utils
from FeatureOntology import *

_LexiconDict = {}
_StemDict = {}
_LexiconLookupSet = dict()
_LexiconLookupSet[LexiconLookupSource.Exclude] = set()
_LexiconLookupSet[LexiconLookupSource.defLex] = set()
_LexiconLookupSet[LexiconLookupSource.External] = set()
_LexiconLookupSet[LexiconLookupSource.oQcQ] = set()
_LexiconSegmentDict = {}  # from main2017. used for segmentation onln. there is no feature.
_LexiconSegmentSlashDict = {}  #
_LexiconCuobieziDict = {}
_LexiconFantiDict = {}

CompositeKG  = []
CompositeKGSetADict = {}

# _LexiconLookupDict = {}     # extra dictionary for lookup purpose.
# the same node is also saved in _LexiconDict
# _LexiconBlacklist = []
_CommentDict = {}

C1ID = None


class LexiconNode(object):
    def __init__(self, word=''):
        self.text = word
        self.norm = word
        self.atom = word
        self.features = set()
        self.missingfeature = ""
        self.origFeatures = set()
        self.stemFeatures = set()
        # self.forLookup = False

    def __str__(self):
        output = self.text + ": "
        output += ",".join([GetFeatureName(feature) for feature in self.features])
        return output

    def entry(self):
        output = self.text + ": "
        featuresCopy = CopyFeatureLeaves(self.features)
        featureSorted = set()
        for feature in featuresCopy:
            featureName = GetFeatureName(feature)
            if featureName:
                featureSorted.add(featureName)
            else:
                logging.warning("Can't find feature of " + self.text)

        featureSorted = sorted(featureSorted)

        output += " ".join(featureSorted) + " "

        if self.norm != self.text:
            output += "'" + self.norm + "' "
        if self.atom != self.text:
            output += "/" + self.atom + "/ "
        if self.missingfeature != "":
            output += self.missingfeature
        if hasattr(self, "comment"):
            output += self.comment

        return output


def CopyFeatureLeaves(features):
    copy = features.copy()
    # remove redundant ancestors.
    for feature in features:
        nodes = SearchFeatureOntology(feature)
        if nodes:
            ancestors = nodes.ancestors
            if ancestors:
                c = ancestors.intersection(copy)
                if c:
                    for a in c:
                        copy.remove(a)
    return copy


def SplitFeatures(FeatureString):
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
        FeatureString = FeatureString.replace(";"," ")

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
        if index != -1:
            occurance += 1
            index += 1
        else:
            break
    if " " in x:
        if occurance != x.count(" "):
            logging.error("Error in RealLength!")
        return len(x) - occurance
    return len(x)


def OutputLexicon(EnglishFlag=False):
    # print("//***Lexicon***")
    Output = ""
    if "firstCommentLine" in _CommentDict:
        Output += _CommentDict["firstCommentLine"] + "\n"
    oldWord = None
    if EnglishFlag:
        s = sorted(_LexiconDict.keys())
    else:
        s = sorted(_LexiconDict.keys(), key=lambda x: (RealLength(x), x))
    for word in s:
        if oldWord in _CommentDict.keys():
            Output += _CommentDict[oldWord]
            oldWord = word

        Output += _LexiconDict[word].entry() + "\n"
        oldWord = word

    return Output


def OutputLexiconFile(FolderLocation):
    if FolderLocation.startswith("."):
        FolderLocation = os.path.join(os.path.dirname(os.path.realpath(__file__)), FolderLocation)
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


def LoadMainLexicon(lexiconLocation):
    global _LexiconSegmentDict
    with open(lexiconLocation, encoding='utf-8') as dictionary:
        for line in dictionary:
            word, _ = SeparateComment(line)
            if word:
                word = word.replace("/", "").lower()
                _LexiconSegmentDict[word] = 0.9
    logging.info("Finish loading lexicon file " + lexiconLocation + "\n\t Total Size:" + str(len(_LexiconSegmentDict)))
    # logging.info("Size of SegmentLexicon: " + str(len(_LexiconSegmentDict)))


def LoadSegmentSlash(lexiconLocation):
    global _LexiconSegmentDict
    with open(lexiconLocation, encoding='utf-8') as dictionary:
        for line in dictionary:
            word, _ = SeparateComment(line)
            if word:
                combinedword = word.replace("/", "")
                _LexiconSegmentSlashDict[combinedword] = word
                if combinedword not in _LexiconSegmentDict:
                    _LexiconSegmentDict[combinedword] = 1.2  # these words from main2017 and 60ngramMain.txt also join segmentation.
    logging.info("Finish loading lexicon file " + lexiconLocation + "\n\t Total Size:" + str(len(_LexiconSegmentDict)))


def LoadSegmentLexicon():
    global _LexiconSegmentDict

    XLocation = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../fsa/X/')
    # lexiconLocation = XLocation + 'main2017.txt'
    # with open(lexiconLocation, encoding='utf-8') as dictionary:
    #     for line in dictionary:
    #         word, _ = SeparateComment(line)
    #         if word:
    #             word = word.replace("/", "").lower()
    #             _LexiconSegmentDict[word] = 0.9
    # logging.info("Size of SegmentLexicon: " + str(len(_LexiconSegmentDict)))

    if _LexiconDict:
        for word in _LexiconDict:
            if word not in _LexiconLookupSet[LexiconLookupSource.defLex] \
                    and word not in _LexiconLookupSet[LexiconLookupSource.External]:
                _LexiconSegmentDict[word] = 1.2
    else:
        lexiconLocation = XLocation + 'AllLexicon.txt'
        with open(lexiconLocation, encoding='utf-8') as dictionary:
            for line in dictionary:
                code, _ = SeparateComment(line)
                if code:
                    word = code.split(":")[0]
                    word = word.replace("/", "")
                    _LexiconSegmentDict[word] = 1.2
    logging.info("Size of SegmentLexicon: " + str(len(_LexiconSegmentDict)))

    for word in _LexiconLookupSet[LexiconLookupSource.External]:
        _LexiconSegmentDict[word] = 1
    #    _LexiconSegmentDict.update(_LexiconLookupSet[LexiconLookupSource.External])
    logging.info("Size of SegmentLexicon: " + str(len(_LexiconSegmentDict)))

    # lexiconLocation = XLocation + 'SegmentSlash.txt'
    # with open(lexiconLocation, encoding='utf-8') as dictionary:
    #     for line in dictionary:
    #         word, _ = SeparateComment(line)
    #         if word:
    #             combinedword = word.replace("/", "")
    #             _LexiconSegmentSlashDict[combinedword] = word
    #             if combinedword not in _LexiconSegmentDict:
    #                 _LexiconSegmentDict[combinedword] = 1.2  # these words from main2017 and 60ngramMain.txt also join segmentation.

    for word in list(_LexiconSegmentDict):
        if IsAlphaLetter(word):
            del _LexiconSegmentDict[word] #remove English words. They should be separate natually by space or numbers or punc.
            continue
        if word.lower() != word:
            _LexiconSegmentDict[word.lower()] = _LexiconSegmentDict[word]
        if word.upper() != word:
            _LexiconSegmentDict[word.upper()] = _LexiconSegmentDict[word]

    logging.info("Size of SegmentSlash: " + str(len(_LexiconSegmentSlashDict)))
    #logging.warning("4g:" + str(_LexiconSegmentDict["4g"]) + "4G:" + str(_LexiconSegmentDict["4G"]) )
    #logging.warning("u盘:" + str(_LexiconSegmentDict["u盘"]) + "U盘:" + str(_LexiconSegmentDict["U盘"]) )


# for Cuobiezi and Fanti. The format is: good: bad1 bad2 bad3
def LoadExtraReference(lexiconLocation, thedict):
    with open(lexiconLocation, encoding='utf-8') as dictionary:
        for line in dictionary:
            code, _ = SeparateComment(line)
            if "：" in code:
                code = code.replace("：", ":")
            if code and ":" in code:
                goodword, badwords = code.split(":", 1)
                for badword in badwords.split():
                    thedict[badword] = goodword
    logging.info("Size of thedict: " + str(len(thedict)))


def ApplyCompositeKG(NodeList):
    TextSet = set()
    node = NodeList.head
    nodestack = set()
    #Collect all the text into a TextSet.
    while node:
        TextSet.add(node.text.lower())

        if node.sons:
            if node.next:
                nodestack.add(node.next)
            node = node.sons[0]
        else:
            node = node.next
            if node == None and nodestack:
                node = nodestack.pop()

    node = NodeList.head
    while node:
        if node.text.lower() in CompositeKGSetADict:
            for ID in CompositeKGSetADict[node.text.lower()]:
                if len(CompositeKG[ID][1]) == 1:
                    logging.info("CompositeKG Winner! Only has one composite set. ")
                    node.norm = CompositeKG[ID][0]
                    node.ApplyFeature(utils.FeatureID_comPair)
                    break
                PassAllSets = True
                for Set in CompositeKG[ID][1][1:]:
                    if not TextSet.intersection(Set):
#                        logging.info("Do not have any of Set in TextSet. This condition failed")
                        PassAllSets = False
                        break
                if PassAllSets:
                    node.norm = CompositeKG[ID][0]
                    node.ApplyFeature(utils.FeatureID_comPair)
                    logging.info("CompositeKG Winner after tring  " + str(len(CompositeKG[ID][1])) + " conditions.:" + CompositeKG[ID][0])
                    break
        if node.sons:
            if node.next:
                nodestack.add(node.next)
            node = node.sons[0]
        else:
            node = node.next
            if node == None and nodestack:
                node = nodestack.pop()


def LoadCompositeKG(lexiconLocation):
    CompositeKG.clear()
    CompositeKGSetADict.clear()
    with open(lexiconLocation, encoding='utf-8') as dictionary:
        for line in dictionary:
            code, _ = SeparateComment(line)
            if code and "=" in code:
                try:
                    KGKey, Sets = code.split("=")
                    CompositeConditions = []
                    if "：" in Sets:
                        Sets = Sets.replace("：", ":")

                    for Set in Sets.split(":"):
                        CompositeConditions.append([x.strip().lower() for x in Set.split("|")])
                    CompositeKG.append((KGKey, CompositeConditions))
                    for A in [x for x in CompositeConditions[0]]:
                        if A not in CompositeKGSetADict:
                            CompositeKGSetADict[A] = [len(CompositeKG)-1]
                        else:
                            CompositeKGSetADict[A].append(len(CompositeKG)-1)
                except ValueError:
                    logging.warning("This line is not correctly format to have 2 colons:" + code)
                    continue

    logging.info("Size of the CompositeKG: " + str(len(CompositeKG)))
    # for i in range(len(CompositeKG)):
    #     print("[" + str(i) + "]" + CompositeKG[i][0] + " = " + str(CompositeKG[i][1]) )
    # for key in CompositeKGSetADict:
    #     print(" Set A:" + key + " as in CompositeKG: " + str(CompositeKGSetADict[key]))

#(O.O)
def LoadLexicon(lexiconLocation, lookupSource=LexiconLookupSource.Exclude):
    global _LexiconDict, _LexiconLookupSet, _StemDict
    global _CommentDict
    if lexiconLocation.startswith("."):
        lexiconLocation = os.path.join(os.path.dirname(os.path.realpath(__file__)), lexiconLocation)

    logging.debug("Start Loading Lexicon " + os.path.basename(lexiconLocation))

    with open(lexiconLocation, encoding='utf-8') as dictionary:
        oldWord = "firstCommentLine"
        for line in dictionary:
            if line.startswith("//"):
                if oldWord in _CommentDict:
                    _CommentDict.update({oldWord: _CommentDict[oldWord] + line})
                else:
                    _CommentDict.update({oldWord: line})
                continue
            code, comment = SeparateComment(line)

            code = code.replace("\:", utils.IMPOSSIBLESTRING)

            # convert Chinese colon to English colon
            if "ChinesePunctuate" not in lexiconLocation and "：" in code:
                code = code.replace("：", ":")
            if  ":::" in code:
                code = code.replace(":::", ":")
            if "::" in code :
                code = code.replace("::",":")

            blocks = [x.strip() for x in re.split(":", code) if x]
            if not blocks:
                continue
            newNode = False
            word = blocks[0].replace(utils.IMPOSSIBLESTRING, ":").lower()
            # Ditionary is case insensitive: make the words lowercase.
            word = word.replace(" ", "")
            if "Punctuate" not in lexiconLocation:
                word = word.replace("/", "")
                word = word.replace("~", "")

            # if InLexiconBlacklist(word):
            #    continue
            ### This checking is only for external dictionary.
            ### So let's apply it to them when generating (offline)

            node = SearchLexicon(word, 'origin')

            # for stemming feature
            newStemNode = False
            stem_node = SearchStem(word)
            if lookupSource == LexiconLookupSource.stemming and not stem_node:
                newStemNode = True
                node = LexiconNode(word)
                if comment:
                    node.comment = comment


            # node = None
            if not node:
                newNode = True
                node = LexiconNode(word)
                if comment:
                    node.comment = comment
            if len(blocks) == 2:
                # there should be no "\:" on the right side.
                features = SplitFeatures(blocks[1].replace(utils.IMPOSSIBLESTRING, ":"))  # blocks[1].split()
                for feature in features:
                    if re.match('^\'.*\'$', feature):
                        node.norm = feature[1:-1]
                        if not node.atom:
                            node.atom = node.norm
                        if "Punctuate" in lexiconLocation:
                            if node.norm in _LexiconDict:
                                normnode = _LexiconDict[node.norm]
                                node.features.update(normnode.features)
                            else:
                                logging.warning("This punctuate is not listed:" + node.norm + " for: " + node.text)
                    elif re.match('^/.*/$', feature):
                        node.atom = feature.strip('/')
                    elif ChinesePattern.search(feature):  # Chinese
                        node.norm = feature
                    else:
                        featureID = GetFeatureID(feature)
                        if featureID == -1:
                            logging.debug("Missing Feature: " + feature)
                            node.missingfeature += "\\" + feature
                        else:
                            node.features.add(featureID)
                            ontologynode = SearchFeatureOntology(featureID)
                            if ontologynode:
                                ancestors = ontologynode.ancestors
                                if ancestors:
                                    node.features.update(ancestors)

            if newStemNode:
                _StemDict.update({node.text: node})
            if newNode:
                if lookupSource != LexiconLookupSource.oQcQ:
                    _LexiconDict.update({node.text: node})
                if lookupSource != LexiconLookupSource.Exclude:
                    _LexiconLookupSet[lookupSource].add(node.text)
                elif "_" in node.text:
                    _LexiconLookupSet[LexiconLookupSource.defLex].add(node.text)

            oldWord = blocks[0]

    # Apply the features of stem/norm into it's variants.
    #   Only use "stem" to apply. Not norm.
    logging.debug("Start applying features for variants")
    for lexicon in _LexiconDict:
        node = _LexiconDict[lexicon]
        _ApplyWordStem(node, node)

    logging.info("Finish loading lexicon file " + lexiconLocation + "\n\t Total Size:" + str(len(_LexiconDict)))


def _ApplyWordStem(NewNode, lexiconnode):
    if NewNode.text != lexiconnode.norm and lexiconnode.norm in _LexiconDict:
        normnode = _LexiconDict[lexiconnode.norm]
        #NewNode.features.update(normnode.features)
        #not comfortable to copy the feature blindly. Use an "F" to do that in orgLex.py offline.
        #   only do that for punctuate signs in the function of LoadLexicon()
        if utils.FeatureID_VB in NewNode.features:
            if NewNode.text == normnode.text + "ed" or NewNode.text == normnode.text + "d":
                NewNode.features.remove(utils.FeatureID_VB)
                NewNode.features.add(utils.FeatureID_Ved)
            if NewNode.text == normnode.text + "ing":
                NewNode.features.remove(utils.FeatureID_VB)
                NewNode.features.add(utils.FeatureID_Ving)


#   If the SearchType is not flexible, then search the origin word only.
# Otherwise, after failed for the origin word, search for case-insensitive, _ed _ing _s...
def SearchLexicon(word, SearchType='flexible'):
    # word = word.lower()
    if word in _LexiconDict:
        return _LexiconDict[word]

    if SearchType != 'flexible':
        return None

    if ChinesePattern.search(word):
        return None

    word = word.lower()
    if word in _LexiconDict.keys():
        return _LexiconDict[word]

    word_ed = re.sub("ed$", '', word)
    if word_ed in _LexiconDict.keys():
        return _LexiconDict[word_ed]
    word_d = re.sub("d$", '', word)
    if word_d in _LexiconDict.keys():
        return _LexiconDict[word_d]
    word_ing = re.sub("ing$", '', word)
    if word_ing in _LexiconDict.keys():
        return _LexiconDict[word_ing]
    word_s = re.sub("s$", '', word)
    if word_s in _LexiconDict.keys():
        return _LexiconDict[word_s]
    word_es = re.sub("es$", '', word)
    if word_es in _LexiconDict.keys():
        return _LexiconDict[word_es]

    return None

def SearchStem(word):
    if word in _StemDict:
        return _StemDict[word]
    return None


def SearchFeatures(word):
    lexicon = SearchLexicon(word)
    if lexicon is None:
        return None  # return empty feature set
    return lexicon.features


def ApplyLexiconToNodes(NodeList):
    node = NodeList.head
    while node:
        ApplyLexicon(node)
        node = node.next

    return NodeList


def InitLengthSet():
    global C1ID, C2ID, C3ID, C4ID, C4plusID
    global C5ID, C5plusID, C6ID, C6plusID, C7ID, C7plusID, C8ID, C8plusID
    global D1ID, D2ID, D3ID, D4ID, D4plusID
    global L1ID, L2ID, L3ID, L4ID, L4plusID

    global LengthSet
    if not C1ID:
        C1ID = GetFeatureID('c1')
        C2ID = GetFeatureID('c2')
        C3ID = GetFeatureID('c3')
        C4ID = GetFeatureID('c4')
        C4plusID = GetFeatureID('c4plus')
        C5ID = GetFeatureID('c5')
        C5plusID = GetFeatureID('c5plus')
        C6ID = GetFeatureID('c6')
        C6plusID = GetFeatureID('c6plus')
        C7ID = GetFeatureID('c7')
        C7plusID = GetFeatureID('c7plus')
        C8ID = GetFeatureID('c8')
        C8plusID = GetFeatureID('c8plus')

        D1ID = GetFeatureID('d1')
        D2ID = GetFeatureID('d2')
        D3ID = GetFeatureID('d3')
        D4ID = GetFeatureID('d4')
        D4plusID = GetFeatureID('d4plus')

        L1ID = GetFeatureID('l1')
        L2ID = GetFeatureID('l2')
        L3ID = GetFeatureID('l3')
        L4ID = GetFeatureID('l4')
        L4plusID = GetFeatureID('l4plus')

        LengthSet = {
            C1ID, C2ID, C3ID, C4ID, C4plusID,
            C5ID, C5plusID, C6ID, C6plusID, C7ID, C7plusID, C8ID, C8plusID,
            D1ID, D2ID, D3ID, D4ID, D4plusID,
            L1ID, L2ID, L3ID, L4ID, L4plusID
        }


def ApplyWordLengthFeature(node):
    if not C1ID:
        InitLengthSet()
    # Below is for None-English only:
    interset = LengthSet.intersection(node.features)
    node.features -= interset

    wordlength = len(node.text)
    if wordlength < 1:
        pass
    elif wordlength == 1:
        if node.text.isnumeric():
            node.ApplyFeature(D1ID)
        if IsAlphaLetter(node.text):
            node.ApplyFeature(L1ID)
        if not IsAscii(node.text):
            node.ApplyFeature(C1ID)
    elif wordlength == 2:
        if node.text.isnumeric():
            node.ApplyFeature(D2ID)
        if IsAlphaLetter(node.text):
            node.ApplyFeature(L2ID)
        if not IsAscii(node.text):
            node.ApplyFeature(C2ID)
    elif wordlength == 3:
        if node.text.isnumeric():
            node.ApplyFeature(D3ID)
        if IsAlphaLetter(node.text):
            node.ApplyFeature(L3ID)
        if not IsAscii(node.text):
            node.ApplyFeature(C3ID)
    elif wordlength == 4:
        if node.text.isnumeric():
            node.ApplyFeature(D4ID)
        if IsAlphaLetter(node.text):
            node.ApplyFeature(L4ID)
        if not IsAscii(node.text):
            node.ApplyFeature(C4ID)
    elif wordlength == 5:
        if node.text.isnumeric():
            node.ApplyFeature(D4plusID)
        if IsAlphaLetter(node.text):
            node.ApplyFeature(L4plusID)
        if not IsAscii(node.text):
            node.ApplyFeature(C5ID)
            node.ApplyFeature(C4plusID)
    elif wordlength == 6:
        if node.text.isnumeric():
            node.ApplyFeature(D4plusID)
        if IsAlphaLetter(node.text):
            node.ApplyFeature(L4plusID)
        if not IsAscii(node.text):
            node.ApplyFeature(C6ID)
            node.ApplyFeature(C4plusID)
    elif wordlength == 7:
        if node.text.isnumeric():
            node.ApplyFeature(D4plusID)
        if IsAlphaLetter(node.text):
            node.ApplyFeature(L4plusID)
        if not IsAscii(node.text):
            node.ApplyFeature(C7ID)
            node.ApplyFeature(C4plusID)
            node.ApplyFeature(C6plusID)
    elif wordlength == 8:
        if node.text.isnumeric():
            node.ApplyFeature(D4plusID)
        if IsAlphaLetter(node.text):
            node.ApplyFeature(L4plusID)
        if not IsAscii(node.text):
            node.ApplyFeature(C8ID)
            node.ApplyFeature(C4plusID)
            node.ApplyFeature(C6plusID)
    else:
        if node.text.isnumeric():
            node.ApplyFeature(D4plusID)
        if IsAlphaLetter(node.text):
            node.ApplyFeature(L4plusID)
        if not IsAscii(node.text):
            node.ApplyFeature(C4plusID)
            node.ApplyFeature(C6plusID)
            node.ApplyFeature(C8plusID)
    return


def ApplyLexicon(node, lex=None):
    if not C1ID:
        InitLengthSet()

    OOVFeatureSet = {utils.FeatureID_JM, utils.FeatureID_JM2, utils.FeatureID_JS, utils.FeatureID_JS2 }
    OOVFeatureSet |= LengthSet

    if not lex:
        lex = SearchLexicon(node.text)
    # if not node.lexicon:    # If lexicon is assigned before, then don't do the search
    #                         #  because the node.word is not as reliable as stem.
    #     node.lexicon = SearchLexicon(node.word)
    if lex is None:
        if IsCD(node.text):
            node.ApplyFeature(utils.FeatureID_CD)
        elif node.text in string.punctuation:
            node.ApplyFeature(utils.FeatureID_SYM)
        elif node.norm == " ":
            node.ApplyFeature(utils.FeatureID_CM)
            # not to apply NNP/OOV to space.
        else:
            node.ApplyFeature(utils.FeatureID_NNP)
            node.ApplyFeature(utils.FeatureID_OOV)
    else:
        node.norm = lex.norm
        node.atom = lex.atom
        if utils.FeatureID_NEW in lex.features:
            node.features = set()
            node.features.update(lex.features)
            node.features.remove(utils.FeatureID_NEW)
        else:
            node.features.update(lex.features)
        _ApplyWordStem(node, lex)
        if len(node.features) == 0 or \
                len(node.features - OOVFeatureSet) == 0:
            node.ApplyFeature(utils.FeatureID_OOV)
            # node.features.add(utils.FeatureID_OOV)

    ApplyWordLengthFeature(node)
    node.ApplyFeature(utils.FeatureID_0)
    return node

# (O.O)
'''
    Somewhere, do this:
    stemmed_word = apply_rule(word)
    if stemmed_word in one_of_the_stem_files:
        add features of stem to word (probaby in this function somehow)
    else:
        mark it as OOV?? (according to infY.txt)

    Ask:
    - how do I even access the word
    - how do I apply the rule to the word
    - if one rule applies will it still attempt to apply other rules
    - do I create a new entry or... will the added features be attached to the temporary word?
    - am I supposed to do anything else past adding features to the word?
    - how do I mark it as OOV

    call rule on the word, elaborates -> elaborate

    "Stemming:" -> LoadLexicon(stemming feature) ->

    Call LoadRule on InfY.txt

    Don't use LoadStem, use LoadLexicon.
    Just focus on finishing all the Loading features, we'll do the actual Lookup things later (e.g. cutting off
                                suffixes and searching up the cut word in the StemDict)

'''


# Lookup will be used right after segmentation.
# Dynamic programming?
def LexiconLookup(strTokens, lookupsource):
    if lookupsource == LexiconLookupSource.oQcQ:
        return _LexiconoQoCLookup(strTokens)

    sentenceLenth = strTokens.size
    bestScore = [1 for _ in range(sentenceLenth + 1)]

    i = 0

    pi = strTokens.head
    while pi.next:
        i += 1
        j = i
        pi = pi.next
        pj = pi
        combinedText = pi.text.lower()
        combinedCount = 1
        while pj.next:
            j += 1
            pj = pj.next
            if not pj.text:
                continue
            combinedText += pj.text.lower()
            combinedCount += 1
            if bestScore[j] < combinedCount and combinedText in _LexiconLookupSet[lookupsource]:
                logging.debug(" combinedCount = " + str(combinedCount) + " combinedText=" + combinedText + " in dict.")
                bestScore[j] = combinedCount

    #logging.debug("After one iteration, the bestScore list is:" + str(bestScore))

    i = strTokens.size - 1
    while i > 0:
        if bestScore[i] > 1:
            NewNode = strTokens.combine(i - bestScore[i] + 1, bestScore[i], -1)
            i = i - bestScore[i]
            ApplyLexicon(NewNode)
            if lookupsource == LexiconLookupSource.External:
                NewNode.ApplyFeature(utils.FeatureID_External)
            NewNode.sons = []  # For lookup, eliminate the sons
            #logging.debug("NewNodeAfterLexiconLookup:" + str(strTokens.get(i)))
        else:
            i = i - 1


def _LexiconoQoCLookup(strTokens, lookupsource=LexiconLookupSource.oQcQ):
    if lookupsource!=LexiconLookupSource.oQcQ:
        logging.error("This is only for oQcQ source.")
    sentenceLenth = strTokens.size
    bestScore = [1 for _ in range(sentenceLenth + 1)]

    i = 0

    pi = strTokens.head
    while pi.next:
        i += 1
        j = i
        pi = pi.next
        pj = pi
        combinedText = pi.text.lower()
        combinedCount = 1
        while pj.next:
            j += 1
            pj = pj.next
            if not pj.text:
                continue
            combinedText += pj.text.lower()
            combinedCount += 1
            if bestScore[j] < combinedCount and combinedText in _LexiconLookupSet[lookupsource]:
                logging.debug(" combinedCount = " + str(combinedCount) + " combinedText=" + combinedText + " in dict.")
                bestScore[j] = combinedCount

    #logging.debug("After one iteration, the bestScore list is:" + str(bestScore))

    i = strTokens.size - 1
    while i > 0:
        if bestScore[i] > 1:
            FirstNodeID = i - bestScore[i] + 1
            LastNodeID = i
            strTokens.get(FirstNodeID-1).ApplyFeature(GetFeatureID("oBR"))
            strTokens.get(FirstNodeID).ApplyFeature(GetFeatureID("oQ"))
            strTokens.get(LastNodeID).ApplyFeature(GetFeatureID("cQ"))
            strTokens.get(LastNodeID+1).ApplyFeature(GetFeatureID("cBR"))

            i = i - bestScore[i]
        else:
            i = i - 1


if __name__ == "__main__":
    dir_path = os.path.dirname(os.path.realpath(__file__))
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

    LoadFeatureOntology(dir_path + '/../../fsa/Y/feature.txt')
    # LoadLexicon('../../fsa/X/LexX.txt')
    # LoadLexicon('../../fsa/X/LexXplus.txt')
    # LoadLexicon('../../fsa/X/brandX.txt')
    # LoadLexicon('../../fsa/X/idiom4X.txt')
    # LoadLexicon('../../fsa/X/idiomX.txt')
    # LoadLexicon('../../fsa/X/locX.txt')
    # LoadLexicon('../../fsa/X/perX.txt')
    # LoadLexicon('../../fsa/X/defPlus.txt')
    LoadLexicon('../../fsa/X/defPlus.txt', lookupSource=LexiconLookupSource.defLex)
    # LoadLexicon('../../fsa/X/perX.txt', lookupSource=LexiconLookupSource.External)
    #
    #
    # para = dir_path + '/../../fsa/X/perX.txt'
    # LoadLexicon(para)
    # para = dir_path + '/../../fsa/X/defLexX.txt'
    # LoadLexicon(para, lookupSource=LexiconLookupSource.defLex)
    # if "/fsa/X" in para:
    #     Englishflag = False
    # else:
    #     Englishflag = True
    # print(OutputLexicon(Englishflag))
    print(OutputMissingFeatureSet())
