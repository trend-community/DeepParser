#!/bin/python
#read in the lookup dictionary. It is mainly used for segmenation (combining multiple tokens into one word/token)
# defLexX.txt sample: 也就: EX advJJ preXV pv rightB /就/

import string

import utils
from FeatureOntology import *


_LexiconDict = {}
_LexiconLookupSet = dict()
_LexiconLookupSet[LexiconLookupSource.Exclude] = set()
_LexiconLookupSet[LexiconLookupSource.defLex] = set()
_LexiconLookupSet[LexiconLookupSource.External] = set()
_LexiconSegmentDict = {}    # from main2017. used for segmentation onln. there is no feature.
_LexiconSegmentSlashDict = {}   #
_LexiconCuobieziDict = {}
_LexiconFantiDict = {}

#_LexiconLookupDict = {}     # extra dictionary for lookup purpose.
                            # the same node is also saved in _LexiconDict
#_LexiconBlacklist = []
_CommentDict = {}

C1ID = None
C2ID = None
C3ID = None
C4ID = None
C4plusID = None


class LexiconNode(object):
    def __init__(self, word=''):
        self.text = word
        self.norm = word
        self.atom = word
        self.features = set()
        self.missingfeature = ""
        #self.forLookup = False

    def __str__(self):
        output = self.text + ": "
        for feature in self.features:
            f = GetFeatureName(feature)
            if f:
                output += f + ","
            else:
                logging.warning("Can't get feature name of " + self.text + " for id " + str(feature))
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
        if self.missingfeature !="":
            output +=  self.missingfeature
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


def RealLength(x):
    index = 0
    occurance = 0
    while index < len(x):
        index = x.find(' ', index)
        if index!=-1:
            occurance += 1
            index += 1
        else:
            break
    if " " in x:
        return len(x) - occurance
    return len(x)


def OutputLexicon(EnglishFlag = False):
    # print("//***Lexicon***")
    Output = ""
    if _CommentDict.get("firstCommentLine"):
        Output += _CommentDict.get("firstCommentLine") + "\n"
    oldWord = None
    if EnglishFlag:
        s=sorted(_LexiconDict.keys())
    else :
        s = sorted(_LexiconDict.keys(), key=lambda x: (RealLength(x), x))
    for word in s:
        if oldWord in _CommentDict.keys():
            Output += _CommentDict[oldWord]
            oldWord = word

        Output += _LexiconDict.get(word).entry() + "\n"
        oldWord = word

    return Output


def OutputLexiconFile(FolderLocation):
    if FolderLocation.startswith("."):
        FolderLocation = os.path.join(os.path.dirname(os.path.realpath(__file__)),  FolderLocation)
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


def LoadSegmentLexicon():
    global _LexiconSegmentDict
    # _LexiconSegmentDict = defaultdict(lambda:1, _LexiconSegmentDict)
    # _LexiconSegmentDict.update(list(_LexiconLookupSet[LexiconLookupSource.External])[:5])

    #_LexiconSegmentDict.update(_LexiconLookupSet[LexiconLookupSource.External])

    XLocation = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../fsa/X/')
    lexiconLocation = XLocation + 'main2017.txt'
    with open(lexiconLocation, encoding='utf-8') as dictionary:
        for line in dictionary:
            word, _ = SeparateComment(line)
            if word:
                word = word.replace("/", "")
                _LexiconSegmentDict[word] = 0.9
    logging.info("Size of SegmentLexicon: " + str(len(_LexiconSegmentDict)))

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

    lexiconLocation = XLocation + 'SegmentSlash.txt'
    with open(lexiconLocation, encoding='utf-8') as dictionary:
        for line in dictionary:
            word, _ = SeparateComment(line)
            if word:
                combinedword = word.replace("/", "")
                _LexiconSegmentSlashDict[combinedword] = word
                _LexiconSegmentDict[combinedword] = 1.2     #these words from main2017 and 60ngramMain.txt also join segmentation.
    logging.info("Size of SegmentSlash: " + str(len(_LexiconSegmentSlashDict)))


# for Cuobiezi and Fanti. The format is: good: bad1 bad2 bad3
def LoadExtraReference(lexiconLocation, thedict):
    with open(lexiconLocation, encoding='utf-8') as dictionary:
        for line in dictionary:
            code, _ = SeparateComment(line)
            if code and ":" in code:
                goodword, badwords = code.split(":", 1)
                for badword in badwords.split():
                    thedict[badword] = goodword
    logging.info("Size of thedict: " + str(len(thedict)))


def LoadLexicon(lexiconLocation, lookupSource = LexiconLookupSource.Exclude):
    global _LexiconDict, _LexiconLookupSet
    global _CommentDict
    if lexiconLocation.startswith("."):
        lexiconLocation = os.path.join(os.path.dirname(os.path.realpath(__file__)),  lexiconLocation)

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

            code = code.replace("\:", utils.IMPOSSIBLESTRING)
            blocks = [x.strip() for x in re.split(":", code) if x]
            if not blocks:
                continue
            newNode = False
            word = blocks[0].replace(utils.IMPOSSIBLESTRING, ":").lower()
            #Ditionary is case insensitive: make the words lowercase.
            word = word.replace(" ", "").replace("~", "")

            #if InLexiconBlacklist(word):
            #    continue
            ### This checking is only for external dictionary.
            ### So let's apply it to them when generating (offline)

            node = SearchLexicon(word, 'origin')
            #node = None
            if not node:
                newNode = True
                node = LexiconNode(word)
                if comment:
                    node.comment = comment
            if len(blocks) == 2:
                # there should be no "\:" on the right side.
                features = SplitFeatures(blocks[1]) # blocks[1].split()
                for feature in features:
                    if re.match('^\'.*\'$', feature):
                        node.norm = feature.strip('\'')
                    elif re.match('^/.*/$', feature):
                        node.atom = feature.strip('/')
                    elif ChinesePattern.search(feature):    #Chinese
                        node.norm = feature
                    else:
                        featureID = GetFeatureID(feature)
                        if featureID==-1:
                            logging.debug("Missing Feature: " + feature)
                            node.missingfeature += "\\" + feature
                        else:
                            node.features.add(featureID)
                            ontologynode = SearchFeatureOntology(featureID)
                            if ontologynode:
                                ancestors = ontologynode.ancestors
                                if ancestors:
                                    node.features.update(ancestors)

            if newNode:
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
    #VFeatureID = GetFeatureID("deverbal")
    VBFeatureID = GetFeatureID("VB")
    VedFeatureID = GetFeatureID("Ved")
    VingFeatureID = GetFeatureID("Ving")

    if NewNode.text != lexiconnode.norm and lexiconnode.norm in _LexiconDict:
        normnode = _LexiconDict[lexiconnode.norm]
        #NewNode.features.update(normnode.features)
        if VBFeatureID in NewNode.features:
            if NewNode.text == normnode.text + "ed" or NewNode.text == normnode.text + "d":
                    NewNode.features.remove(VBFeatureID)
                    NewNode.features.add(VedFeatureID)
            if NewNode.text == normnode.text + "ing":
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

    if ChinesePattern.search(word):
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


def SearchFeatures(word):
    lexicon = SearchLexicon(word)
    if lexicon is None:
        return {}   #return empty feature set
    return lexicon.features


def ApplyLexiconToNodes(NodeList):
    node = NodeList.head
    while node:
        ApplyLexicon(node)
        node = node.next
    return NodeList


def ApplyWordLengthFeature(node):
    global C1ID, C2ID, C3ID, C4ID, C4plusID
    if IsAscii(node.text):
        return
    if not C1ID:
        C1ID = GetFeatureID('c1')
        C2ID = GetFeatureID('c2')
        C3ID = GetFeatureID('c3')
        C4ID = GetFeatureID('c4')
        C4plusID = GetFeatureID('c4plus')

    # Below is for None-English only:
    if C1ID in node.features:
        node.features.remove(C1ID)
    elif C2ID in node.features:
        node.features.remove(C2ID)
    elif C3ID in node.features:
        node.features.remove(C3ID)
    elif C4ID in node.features:
        node.features.remove(C4ID)
    elif C4plusID in node.features:
        node.features.remove(C4plusID)

    wordlength = len(node.text)
    if wordlength<1:
        pass
    elif wordlength == 1:
        node.features.add(C1ID)
    elif wordlength == 2:
        node.features.add(C2ID)
    elif wordlength == 3:
        node.features.add(C3ID)
    elif wordlength == 4:
        node.features.add(C4ID)
    else:
        node.features.add(C4plusID)

    return


def ApplyLexicon(node, lex=None):
    OOVFeatureSet = { utils.FeatureID_JM, utils.FeatureID_JM2, utils.FeatureID_JS, utils.FeatureID_JS2,
                      C1ID, C2ID, C3ID, C4ID, C4plusID
                      #utils.FeatureID_0
                      }
    if not lex:
        lex = SearchLexicon(node.text)
    # if not node.lexicon:    # If lexicon is assigned before, then don't do the search
    #                         #  because the node.word is not as reliable as stem.
    #     node.lexicon = SearchLexicon(node.word)
    if lex is None:
        if IsCD(node.text):
            node.features.add(utils.FeatureID_CD)
        elif node.text in string.punctuation:
            node.features.add(utils.FeatureID_SYM)
        elif node.text == " ":
            node.features.add(utils.FeatureID_CM)
                #not to apply NNP/OOV to space.
        else:
            node.features.add(utils.FeatureID_NNP)
            node.features.add(utils.FeatureID_OOV)
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
            node.features.add(utils.FeatureID_OOV)

    ApplyWordLengthFeature(node)
    node.features.add(utils.FeatureID_0)
    return node


#Lookup will be used right after segmentation.
# Dynamic programming?
def LexiconLookup(strTokens, lookupsource):
    sentenceLenth = strTokens.size
    bestScore = [1 for _ in range(sentenceLenth+1)]

    i = 0

    logging.info("LexiconLookup " + lookupsource.name + "  size:" + str(len(_LexiconLookupSet[lookupsource])))

    pi = strTokens.head
    while pi.next:
        i += 1
        j = i
        pi = pi.next
        pj = pi
        combinedText = pj.text
        combinedCount = 1
        while pj.next:
            j += 1
            pj = pj.next
            if not pj.text:
                continue
            combinedText += pj.text
            combinedCount += 1
            if combinedText in _LexiconLookupSet[lookupsource]:
                logging.debug( " combinedCount = " + str(combinedCount) + " combinedText=" + combinedText + " in dict.")
                bestScore[j] = combinedCount

    logging.debug("After one iteration, the bestScore list is:" + str(bestScore))

    i = strTokens.size - 1
    while i>0:
        if bestScore[i]>1:
            NewNode = strTokens.combine(i-bestScore[i]+1, bestScore[i], -1)
            i = i - bestScore[i]
            ApplyLexicon(NewNode)
            NewNode.sons = []   #For lookup, eliminate the sons
            logging.debug("NewNodeAfterLexiconLookup:" + str(strTokens.get(i)))
        else:
            i = i - 1


if __name__ == "__main__":
    dir_path = os.path.dirname(os.path.realpath(__file__))
    logging.basicConfig( level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

    LoadFeatureOntology(dir_path + '/../../fsa/Y/feature.txt')
    # LoadLexicon('../../fsa/X/LexX.txt')
    # LoadLexicon('../../fsa/X/LexXplus.txt')
    # LoadLexicon('../../fsa/X/brandX.txt')
    # LoadLexicon('../../fsa/X/idiom4X.txt')
    # LoadLexicon('../../fsa/X/idiomX.txt')
    # LoadLexicon('../../fsa/X/locX.txt')
    # LoadLexicon('../../fsa/X/perX.txt')
    # LoadLexicon('../../fsa/X/defPlus.txt')
    LoadLexicon('../../fsa/X/ChinesePunctuate.txt', lookupSource=LexiconLookupSource.defLex)
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


