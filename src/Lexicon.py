#!/bin/python
# read in the lookup dictionary. It is mainly used for segmentation (combining multiple tokens into one word/token)
# defLexX.txt sample: 也就: EX advJJ preXV pv rightB /就/

import string, copy

from FeatureOntology import *
from FeatureOntology import _AppendixLists

_LexiconDict = {}
_LexiconSensitiveDict = {}
_StemDict = {}  # not all stems are lexicon.
_LexiconLookupSet = dict()
for source in utils.LexiconLookupSource:
    _LexiconLookupSet[source] = set()
    # _LexiconLookupSet[utils.LexiconLookupSource.DEFLEX] = set()
    # _LexiconLookupSet[utils.LexiconLookupSource.EXTERNAL] = set()
    # _LexiconLookupSet[utils.LexiconLookupSource.COMPOUND] = set()
    # _LexiconLookupSet[utils.LexiconLookupSource.COMPOUND_SENSITIVE] = set()
    # _LexiconLookupSet[utils.LexiconLookupSource.STEMMING] = set()
    # _LexiconLookupSet[utils.LexiconLookupSource.DOCUMENT] = set()
_LexiconSegmentDict = {}  # from main2017. used for segmentation only. there is no feature.
_LexiconSegmentSlashDict = {}  #
_LexiconSpellingDict = {}
_LexiconlinkDisplay = {}
#_LexiconFantiDict = {}

# CompositeKG  = []
# CompositeKGSetADict = {}

# DocumentLexicon = {}        # this lexicon is updated from the ruel GLOBAL action, and reset from webservice ResetGlobalValue.

# _LexiconLookupDict = {}     # extra dictionary for lookup purpose.
# the same node is also saved in _LexiconDict
# _LexiconBlacklist = []
_CommentDict = {}

C1ID = None

#(O.O)
# _StemDict = {}
# _SuffixList = []
# _InfFile = ""
_SuffixDict = {}
_PrefixDict = {}
_SuffixList = []
_PrefixList = []


class LexiconNode(object):
    def __init__(self, word=''):
        self.text = word
        self.norm = word
        self.atom = word
        self.features = set()
        self.missingfeature = ""
        self.origFeatures = set()
        self.stemFeatures = set()
        self.headid = -1    # used in Stem Compound
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
    _copy = features.copy()
    # remove redundant ancestors.
    for feature in features:
        nodes = SearchFeatureOntology(feature)
        if nodes:
            ancestors = nodes.ancestors
            if ancestors:
                c = ancestors.intersection(_copy)
                if c:
                    for a in c:
                        _copy.remove(a)
    return _copy


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
    # if FolderLocation.startswith("."):
    #     FolderLocation = os.path.join(os.path.dirname(__file__), FolderLocation)
    FileLocation = os.path.join(FolderLocation, "lexicon.txt")

    with open(FileLocation, "w", encoding="utf-8") as writer:
        writer.write(OutputLexicon())


# def LoadLexiconBlacklist(BlacklistLocation):
#     if BlacklistLocation.startswith("."):
#         BlacklistLocation = os.path.join(os.path.dirname(__file__),  BlacklistLocation)
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
            word, _ = utils.SeparateComment(line)
            if word:
                if "/" in word:
                    combinedword = word.replace("/", "")
                    _LexiconSegmentSlashDict[combinedword] = word
                    if combinedword not in _LexiconSegmentDict:
                        _LexiconSegmentDict[combinedword] = 1.2  # these words from main2017 and 60ngramMain.txt also join segmentation.
                else:
                    word = word.lower()
                    _LexiconSegmentDict[word] = 0.9
    logging.info("Finish loading main lexicon file " + lexiconLocation + "\n\t Total Size:" + str(len(_LexiconSegmentDict)))
    # logging.info("Size of SegmentLexicon: " + str(len(_LexiconSegmentDict)))


def LoadSegmentSlash_ORIGIN(lexiconLocation):
    global _LexiconSegmentDict
    with open(lexiconLocation, encoding='utf-8') as dictionary:
        for line in dictionary:
            word, _ = utils.SeparateComment(line)
            if word:
                combinedword = word.replace("/", "")
                _LexiconSegmentSlashDict[combinedword] = word
                if combinedword not in _LexiconSegmentDict:
                    _LexiconSegmentDict[combinedword] = 1.2  # these words from main2017 and 60ngramMain.txt also join segmentation.
    logging.info("Finish loading segmentslash lexicon file " + lexiconLocation + "\n\t Total Size:" + str(len(_LexiconSegmentDict)))



def LoadSegmentSlash():
    """
    Get the segmentslash info from:
        1, slash in main2017.txt;   #already done in LoadMainLexicon()
        2, 5ngramKG.txt, 6ngramMain.txt
    :return:
    """
    global _LexiconSegmentDict
    import Rules
    for rulefiles in Rules.RuleGroupDict:
        if rulefiles.endswith("5ngramKG.txt") or rulefiles.endswith("6ngramMain.txt") :
            rulegroup = Rules.RuleGroupDict[rulefiles]
            for rule in rulegroup.RuleList:
                slashword = "/".join([n for n in rule.norms if n])
                combinedword = slashword.replace("/", "")
                _LexiconSegmentSlashDict[combinedword] = slashword
                if combinedword not in _LexiconSegmentDict:
                    _LexiconSegmentDict[combinedword] = 1.2  # these words  also join segmentation.


def ApplyStemFeatures():
    global _SuffixList, _PrefixList

    for x in _LexiconDict:
        if x != _LexiconDict[x].atom:
            _LexiconDict[x].features.update(StemFeatures(_LexiconDict[x].atom))

    _SuffixList = sorted(_SuffixDict.keys(), key=lambda ss: len(ss), reverse=True)
    _PrefixList = sorted(_PrefixDict.keys(), key=lambda ss: len(ss), reverse=True)


# this function is called after all lexicons are loaded from files.
# this function is to rearrange the _LexiconSegmentDict for segmentation.
def LoadSegmentLexicon():
    global _LexiconSegmentDict

    # lexiconLocation = XLocation + 'main2017.txt'
    # with open(lexiconLocation, encoding='utf-8') as dictionary:
    #     for line in dictionary:
    #         word, _ = SeparateComment(line)
    #         if word:
    #             word = word.replace("/", "").lower()
    #             _LexiconSegmentDict[word] = 0.9
    # logging.info("Size of SegmentLexicon: " + str(len(_LexiconSegmentDict)))
    LoadSegmentSlash()  # new one.

    if _LexiconDict:
        for word in _LexiconDict:
            if word not in _LexiconLookupSet[utils.LexiconLookupSource.DEFLEX] \
                    and word not in _LexiconLookupSet[utils.LexiconLookupSource.EXTERNAL]\
                    and word not in _LexiconLookupSet[utils.LexiconLookupSource.COMPOUND]:
                _LexiconSegmentDict[word] = 1.2

            # 20201024: If SegmentSlashDict word is already in _LexiconDict, then remove it from SegmentSlashDict.
            # if the word is from DefLex, don't remove it. Slash it so that the other steps before Lookup DefLex still has the chance to perform.
            if word in _LexiconSegmentSlashDict:
                if word not in _LexiconLookupSet[utils.LexiconLookupSource.DEFLEX]:
                    del _LexiconSegmentSlashDict[word]
    else:       #this part is for other usage, not real application.
        XLocation = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../fsa/X/')

        lexiconLocation = XLocation + 'AllLexicon.txt'
        with open(lexiconLocation, encoding='utf-8') as dictionary:
            for line in dictionary:
                code, _ = utils.SeparateComment(line)
                if code:
                    word = code.split(":")[0]
                    word = word.replace("/", "")
                    _LexiconSegmentDict[word] = 1.2

    for word in _LexiconLookupSet[utils.LexiconLookupSource.EXTERNAL]:
        _LexiconSegmentDict[word] = 1
    #    _LexiconSegmentDict.update(_LexiconLookupSet[utils.LexiconLookupSource.External])
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
        if utils.IsAlphaLetter(word):
            del _LexiconSegmentDict[word] #remove English words for segment. They should be separate natually by space or numbers or punc.
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
            code, _ = utils.SeparateComment(line)
            if "：" in code:
                #code = code.replace("：", ":")
                logging.warning(f"This line has \：{line}")
            if code and ":" in code:
                goodword, badwords = code.split(":", 1)
                goodword = goodword.strip().replace("\\SPACE", " ")
                for badword in badwords.split():
                    badword = badword.replace("\\SPACE", " ")
                    thedict[badword] = goodword
    thedict = sorted(thedict, key=len, reverse=True)    # for longest principle
    logging.info("Size of thedict: " + str(len(thedict)))



#20200821: Add regex in this function.
#def ReplaceCuobieziAndFanti(sentence):
def SpellingCheckingAsian(sentence):
    """
    Can be used for spelling checking, or Tradition/Simplified Chinese conversion
    Can use regex for spelling checking.
    For Western: need to verify it is the whole word, not just character replacement. can't be done here.
    :param sentence:
    :return: replaced string
    """
    if not hasattr(SpellingCheckingAsian, "regexdict"):
        SpellingCheckingAsian.regexdict = {}
        for k, v in _LexiconSpellingDict.items():
            if v.startswith("#"):
                SpellingCheckingAsian.regexdict[k] = v[1:]

    if utils.LanguageType == "asian":
        for k in _LexiconSpellingDict:
            if k in sentence:     #non-regex way
                sentence = sentence.replace(k, _LexiconSpellingDict[k])
    else:
        pass # I don't find a good way to replace in this level. The words has to be tokenized before replacing.
        # will do it after tokenization.
        # for sign in " .,\"":
        #     tokens = sentence.split(sign)
        #     for i in range(len(tokens)):
        #         for k in _LexiconSpellingDict:
        #             if tokens[i] == k:  # non-regex way
        #                 tokens[i] = _LexiconSpellingDict[k]
        #                 break   # no longer checking this tokens[i].
        #     sentence = sign.join(tokens) # get back.

    for k, v in SpellingCheckingAsian.regexdict.items():
        sentence = re.sub(k, v, sentence)

    return sentence


def SpellingCheckingWestern(strTokens):
    if not hasattr(SpellingCheckingWestern, "regexdict"):
        SpellingCheckingWestern.regexdict = {}
        for k, v in _LexiconSpellingDict.items():
            if v.startswith("#"):
                SpellingCheckingWestern.regexdict[k] = v[1:]

    p = strTokens.head
    while p:
        for k, v in SpellingCheckingWestern.regexdict.items():
            p.text = re.sub(k, v, p.text)

        for k in _LexiconSpellingDict:
            if p.text == k:  # non-regex way
                p.text = _LexiconSpellingDict[k]
                break
        p = p.next


 # ExtraInfo should be from "Lookup Customer 应急预案.txt  NEW yingjiyuan N nc"
def LoadLexicon(lexiconLocation, lookupSource=utils.LexiconLookupSource.EXCLUDE, ExtraInfo = '', Sensitive=False):
    global _CommentDict
    # if lexiconLocation.startswith("."):
    #     lexiconLocation = os.path.join(os.path.dirname(__file__), lexiconLocation)

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
            code, comment = utils.SeparateComment(line)

            code = code.replace("\:", utils.IMPOSSIBLESTRING)

            # convert Chinese colon to English colon
            if "ChinesePunctuate" not in lexiconLocation and "：" in code:
                logging.warning(f"This line has \：{line}")
                #code = code.replace("：", ":")
            if  ":::" in code:
                code = code.replace(":::", ":")
            if "::" in code :
                code = code.replace("::",":")

            if code.count(':') > 1:
                blocks = code.rsplit(':',1)
            else:
                blocks = [x.strip() for x in re.split(":", code) if x]
            if not blocks:
                continue
            newNode = False
            word = blocks[0].replace(utils.IMPOSSIBLESTRING, ":")
            if not Sensitive:
                word = word.lower()
            # Dictionary is case insensitive: make the words lowercase.
            word = word.replace(" ", "")
            if "Punctuate" not in lexiconLocation:
                word = word.replace("/", "")
                word = word.replace("~", "")

            if "^" in word:
                headid = word.split('^', 1)[0].count('_')  # How Many _ before `
                word = word.replace("^", "")
            else:
                headid = -1

            # if InLexiconBlacklist(word):
            #    continue
            ### This checking is only for external dictionary.
            ### So let's apply it to them when generating (offline)
            if lookupSource == utils.LexiconLookupSource.STEMMING:
                if word in _StemDict:
                    node = _StemDict[word]
                else:
                    node = None
            else:
                node = SearchLexicon(word, 'origin')

            # node = None
            if not node:
                newNode = True
                node = LexiconNode(word)
                node.headid = headid    # if there is ` sign, then headid != -1
                if comment:
                    node.comment = comment

            if ExtraInfo:
                if len(blocks) == 2:
                    blocks[1] += " " + ExtraInfo
                else:
                    blocks.append(ExtraInfo)

            if len(blocks) == 2:
                # there should be no "\:" on the right side.
                features = SplitFeatures(blocks[1].replace(utils.IMPOSSIBLESTRING, ":"))  # blocks[1].split()
                if "NEW" in features:
                    node.features.clear()   #remove existing features from the node.
                    features.remove("NEW")
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
                    elif utils.ChinesePattern.fullmatch(feature):  # Chinese
                        node.norm = feature
                        # if not node.atom:     # 20200729: feel like this should be enabled.
                        #     node.atom = node.norm
                    else:
                        featureID = GetFeatureID(feature)
                        if featureID == -1:
                            logging.info("Missing Feature: {} in line {}".format(feature, line))
                            node.missingfeature += "\\" + feature
                        else:
                            ApplyFeature(node.features, featureID)
                            # node.features.add(featureID)
                            # ontologynode = SearchFeatureOntology(featureID)
                            # if ontologynode:
                            #     ancestors = ontologynode.ancestors
                            #     if ancestors:
                            #         node.features.update(ancestors)
            #
            if Sensitive:
                if newNode:
                    _LexiconSensitiveDict.update({node.text: node})
                    if "_" in node.text:
                        _LexiconLookupSet[utils.LexiconLookupSource.COMPOUND_SENSITIVE].add(node.text)

            else:
                if lookupSource == utils.LexiconLookupSource.STEMMING:
                    _StemDict.update({node.text: node})
                    if "_" in node.text:
                        _LexiconLookupSet[utils.LexiconLookupSource.STEMCOMPOUND].add(node.text)
                else:
                    if lookupSource != utils.LexiconLookupSource.EXCLUDE:
                        _LexiconLookupSet[lookupSource].add(node.text)

                    SignNeedToLookupInDefLex = ".-/&"
                    if newNode:
                        _LexiconDict.update({node.text: node})
                        if "_" in node.text:
                            _LexiconLookupSet[utils.LexiconLookupSource.COMPOUND].add(node.text)
                        elif  True in [c in node.text for c in SignNeedToLookupInDefLex]:
                            _LexiconLookupSet[utils.LexiconLookupSource.DEFLEX].add(node.text)

            oldWord = blocks[0]


    # Apply the features of stem/norm into it's variants.
    #   Only use /stem/ to apply. Not norm.
    # logging.debug("Start applying features for variants")
    # for lexicon in _LexiconDict:
    #     node = _LexiconDict[lexicon]
    #     # _ApplyWordStem(node, node) (o.o)

    logging.info("Finish loading lexicon file " + lexiconLocation + "\n\t Total Size:" + str(len(_LexiconDict)))


def AddDocumentTempLexicon(text, features):
    node = LexiconNode(text)
    corefeatures = features.intersection(_AppendixLists['CoreGlobalList'])    # only copy the ontology core feature into the node
    #corefeatures = features
    node.features.update(corefeatures)
    ExistedInDocumentLexicon = False
    for n in _LexiconLookupSet[utils.LexiconLookupSource.DOCUMENT]:
        if n.text == node.text:
            ExistedInDocumentLexicon = True
            n.features.update(corefeatures)     # update the feature of the existing node in DocumentLexicon
            break
    if not ExistedInDocumentLexicon:
        _LexiconLookupSet[utils.LexiconLookupSource.DOCUMENT].add(node)
    if node.text in _LexiconDict:
        _LexiconDict[node.text].features.update(corefeatures)
    else:
        _LexiconDict[node.text] = copy.deepcopy(node)
    _LexiconSegmentDict[node.text] = 1.2


def ResetDocumentTempLexicon():
    for n in _LexiconLookupSet[utils.LexiconLookupSource.DOCUMENT]:
        for f in n.features:
            _LexiconDict[n.text].features.remove(f)

        # if the left feature is empty, then this word was not existed before it was added in this document. Remove it.
        if len(_LexiconDict[n.text].features) == 0:
            del _LexiconDict[n.text]
            del _LexiconSegmentDict[n.text]

    _LexiconLookupSet[utils.LexiconLookupSource.DOCUMENT] = set()


#   If the SearchType is not flexible, then search the origin word only.
# Otherwise, after failed for the origin word, search for case-insensitive, _ed _ing _s...
def SearchLexicon(word, SearchType='flexible'):
    # word = word.lower()
    if word in _LexiconSensitiveDict:
        return _LexiconSensitiveDict[word]

    if word in _LexiconDict:
        return _LexiconDict[word]

    if SearchType != 'flexible':
        return None

    if utils.ChinesePattern.fullmatch(word):
        return None

    word = word.lower()
    if word in _LexiconDict.keys():
        return _LexiconDict[word]


    # word_ed = re.sub("ed$", '', word)
    # if word_ed in _LexiconDict.keys():
    #     return _LexiconDict[word_ed]
    # word_d = re.sub("d$", '', word)
    # if word_d in _LexiconDict.keys():
    #     return _LexiconDict[word_d]
    # word_ing = re.sub("ing$", '', word)
    # if word_ing in _LexiconDict.keys():
    #     return _LexiconDict[word_ing]
    # word_s = re.sub("s$", '', word)
    # if word_s in _LexiconDict.keys():
    #     return _LexiconDict[word_s]
    # word_es = re.sub("es$", '', word)
    # if word_es in _LexiconDict.keys():
    #     return _LexiconDict[word_es]


    return None



#   If the SearchType is not flexible, then search the origin word only.
# Otherwise, after failed for the origin word, search for case-insensitive, _ed _ing _s...
def SearchOrCreateLexicon(word, SearchType='flexible'):
    # word = word.lower()
    node = SearchLexicon(word, SearchType)
    if not node:
        node = LexiconNode(word)
        _LexiconDict.update({node.text: node})

    return node


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


def ResetAllLexicons():
    _LexiconDict.clear()
    _LexiconLookupSet.clear()
    _LexiconLookupSet[utils.LexiconLookupSource.EXCLUDE] = set()
    _LexiconLookupSet[utils.LexiconLookupSource.DEFLEX] = set()
    _LexiconLookupSet[utils.LexiconLookupSource.EXTERNAL] = set()
    _LexiconLookupSet[utils.LexiconLookupSource.STEMMING] = None
    _LexiconLookupSet[utils.LexiconLookupSource.COMPOUND] = set()
    _LexiconLookupSet[utils.LexiconLookupSource.DOCUMENT] = set()
    _LexiconSegmentDict.clear() # from main2017. used for segmentation only. there is no feature.
    _LexiconSegmentSlashDict.clear() #
    _LexiconSpellingDict.clear()
    _CommentDict.clear()


def InitLengthSet():
        _LengthFeatures=['d1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd4plus', 'd5plus', 'd6plus',
                        'c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7', 'c8', 'c4plus', 'c5plus', 'c6plus', 'c7plus', 'c8plus',
                        'l1', 'l2', 'l3', 'l4', 'l4plus']
        _LengthDict = {}
        for f in _LengthFeatures:
            _LengthDict[f] = GetFeatureID(f)

        return _LengthDict

def ApplyWordLengthFeature(node):
    if not hasattr(ApplyWordLengthFeature, "LengthDict"):
        ApplyWordLengthFeature.LengthDict = InitLengthSet()
        ApplyWordLengthFeature.LengthSet = set(ApplyWordLengthFeature.LengthDict.values())
    # Below is for None-English only:
    interset = ApplyWordLengthFeature.LengthSet.intersection(node.features)
    node.features -= interset   # First, remove existing length features from the node

    wordlength = len(node.text)
    if wordlength < 1:
        pass
    elif wordlength == 1:
        if node.text.isnumeric():
            node.ApplyFeature(ApplyWordLengthFeature.LengthDict['d1'])
        if utils.IsAlphaLetter(node.text):
            node.ApplyFeature(ApplyWordLengthFeature.LengthDict['l1'])
        if not utils.IsAscii(node.text):
            node.ApplyFeature(ApplyWordLengthFeature.LengthDict['c1'])
    elif wordlength == 2:
        if node.text.isnumeric():
            node.ApplyFeature(ApplyWordLengthFeature.LengthDict['d2'])
        if utils.IsAlphaLetter(node.text):
            node.ApplyFeature(ApplyWordLengthFeature.LengthDict['l2'])
        if not utils.IsAscii(node.text):
            node.ApplyFeature(ApplyWordLengthFeature.LengthDict['c2'])
    elif wordlength == 3:
        if node.text.isnumeric():
            node.ApplyFeature(ApplyWordLengthFeature.LengthDict['d3'])
        if utils.IsAlphaLetter(node.text):
            node.ApplyFeature(ApplyWordLengthFeature.LengthDict['l3'])
        if not utils.IsAscii(node.text):
            node.ApplyFeature(ApplyWordLengthFeature.LengthDict['c3'])
    elif wordlength == 4:
        if node.text.isnumeric():
            node.ApplyFeature(ApplyWordLengthFeature.LengthDict['d4'])
        if utils.IsAlphaLetter(node.text):
            node.ApplyFeature(ApplyWordLengthFeature.LengthDict['l4'])
        if not utils.IsAscii(node.text):
            node.ApplyFeature(ApplyWordLengthFeature.LengthDict['c4'])
    elif wordlength == 5:
        if node.text.isnumeric():
            node.ApplyFeature(ApplyWordLengthFeature.LengthDict['d5'])
        if utils.IsAlphaLetter(node.text):
            node.ApplyFeature(ApplyWordLengthFeature.LengthDict['l4plus'])
        if not utils.IsAscii(node.text):
            node.ApplyFeature(ApplyWordLengthFeature.LengthDict['c5'])
    elif wordlength == 6:
        if node.text.isnumeric():
            node.ApplyFeature(ApplyWordLengthFeature.LengthDict['d6'])
        if utils.IsAlphaLetter(node.text):
            node.ApplyFeature(ApplyWordLengthFeature.LengthDict['l4plus'])
        if not utils.IsAscii(node.text):
            node.ApplyFeature(ApplyWordLengthFeature.LengthDict['c6'])
    elif wordlength == 7:
        if node.text.isnumeric():
            node.ApplyFeature(ApplyWordLengthFeature.LengthDict['d6plus'])
        if utils.IsAlphaLetter(node.text):
            node.ApplyFeature(ApplyWordLengthFeature.LengthDict['l4plus'])
        if not utils.IsAscii(node.text):
            node.ApplyFeature(ApplyWordLengthFeature.LengthDict['c7'])
    elif wordlength == 8:
        if node.text.isnumeric():
            node.ApplyFeature(ApplyWordLengthFeature.LengthDict['d6plus'])
        if utils.IsAlphaLetter(node.text):
            node.ApplyFeature(ApplyWordLengthFeature.LengthDict['l4plus'])
        if not utils.IsAscii(node.text):
            node.ApplyFeature(ApplyWordLengthFeature.LengthDict['c8'])
    else:
        if node.text.isnumeric():
            node.ApplyFeature(ApplyWordLengthFeature.LengthDict['d6plus'])
        if utils.IsAlphaLetter(node.text):
            node.ApplyFeature(ApplyWordLengthFeature.LengthDict['l4plus'])
        if not utils.IsAscii(node.text):
            node.ApplyFeature(ApplyWordLengthFeature.LengthDict['c8plus'])
    return


def StemFeatures(stem):
    # for western, check the stem dict for features. Otherwise, check the lex dict for features.
    if utils.LanguageType == 'western':
        if stem in _StemDict:
            return _StemDict[stem].features
        else:
            return []
    else:
        atomlex = SearchLexicon(stem)
        if atomlex:
            return atomlex.features
        else:
            return []


def Stemming(word):
    lex, features = Stemming_stem(word)
    if not lex:
        return Stemming_longest_surfixprefix(word)
    else:
        return lex, features


# if stem is found: the longest stem win.
# if no stem is found: the longest suffix/prefix win.
# if in first level, the action must be "endingM"
def Stemming_stem(word, firstlevel = True):
    import Tokenization, LogicOperation
    longest_stem = None
    longest_features = []
    longest_num = 0

    for suffix in _SuffixList:
        if word.endswith(suffix):
            #logging.info("stemming: {} has suffix of {}".format(word, suffix))
            rules = _SuffixDict[suffix]
            tempstem = word[:-len(suffix)]
            wordtoken = Tokenization.SentenceNode(tempstem)
            wordtoken.features.update(StemFeatures(tempstem))
            for rule in rules:
                if firstlevel:
                    if utils.ProjectName == "E":
                        if "endingM" not in rule.Tokens[0].action:
                            continue    # bypass this rule for not having endingM.

                if LogicOperation.LogicMatch_notpointer(wordtoken, rule.Tokens[0]) and \
                    tempstem in _StemDict:
                    wordtoken.ApplyActions(rule.Tokens[0].action, None)
                    if len(tempstem) > longest_num:
                        longest_num = len(tempstem)
                        longest_stem = wordtoken
                        longest_features = copy.copy(wordtoken.features)

                else:
                    lex, features = Stemming_stem(tempstem, firstlevel=False)
                    if lex:
                        temptoken = Tokenization.SentenceNode(lex.text) # a temp token to check if it fit the rules.
                        temptoken.features.update(features)
                        temptoken.features.update(wordtoken.features)
                        if LogicOperation.LogicMatch_notpointer(temptoken, rule.Tokens[0]):
                            temptoken.ApplyActions(rule.Tokens[0].action, None)
                            if len(lex.text) > longest_num:
                                longest_num = len(lex.text)
                                longest_stem = lex
                                longest_features = copy.copy(temptoken.features)
                                #logging.debug("\tsuffix word is {}, len={}, rule={} ".format(word, longest_num, rule))

    for prefix in _PrefixList:
        if word.startswith(prefix):
            #logging.info("stemming: {} has suffix of {}".format(word, suffix))
            rules = _PrefixDict[prefix]
            tempstem = word[len(prefix):]
            wordtoken = Tokenization.SentenceNode(tempstem)
            wordtoken.features.update(StemFeatures(tempstem))
            for rule in rules:
                if LogicOperation.LogicMatch_notpointer(wordtoken, rule.Tokens[0]) and \
                    tempstem in _StemDict:
                    wordtoken.ApplyActions(rule.Tokens[0].action, None)
                    if len(tempstem) > longest_num:
                        longest_num = len(tempstem)
                        longest_stem = wordtoken
                        longest_features = copy.copy(wordtoken.features)

                else:
                    lex, features = Stemming_stem(tempstem, firstlevel=False)
                    if lex:
                        temptoken = Tokenization.SentenceNode(tempstem) # a temp token to check if it fit the rules.
                        temptoken.features.update(features)
                        temptoken.features.update(wordtoken.features)
                        if LogicOperation.LogicMatch_notpointer(temptoken, rule.Tokens[0]):
                            temptoken.ApplyActions(rule.Tokens[0].action, None)
                            if len(lex.text) > longest_num:
                                longest_num = len(lex.text)
                                longest_stem = lex
                                longest_features = temptoken.features
                                #logging.info("\tprefix word is {}, len={}, rule={} ".format(word, longest_num, rule))

    return longest_stem, longest_features


# lex, stemming_features = Stemming(word)
# below is a good one for seaching for longest suffix. but not good for longest stem. need revise.
def Stemming_longest_surfixprefix(word, firstlevel=True):
    import Tokenization, LogicOperation
    for suffix in _SuffixList:
        if word.endswith(suffix):
            #logging.info("stemming: {} has suffix of {}".format(word, suffix))
            rules = _SuffixDict[suffix]
            tempstem = word[:-len(suffix)]
            wordtoken = Tokenization.SentenceNode(tempstem)
            wordtoken.features.update(StemFeatures(tempstem))
            for rule in rules:
                if firstlevel:
                    if utils.ProjectName == "E":
                        if "endingM" not in rule.Tokens[0].action:
                            continue    # bypass this rule for not having endingM.
                if LogicOperation.LogicMatch_notpointer(wordtoken, rule.Tokens[0]):
                    wordtoken.ApplyActions(rule.Tokens[0].action, None)
                    return wordtoken, wordtoken.features
                else:
                    lex, features = Stemming_longest_surfixprefix(tempstem, firstlevel=False)
                    if features:
                        temptoken = Tokenization.SentenceNode(tempstem)
                        temptoken.features.update(features)
                        temptoken.features.update(wordtoken.features)
                        if LogicOperation.LogicMatch_notpointer(temptoken, rule.Tokens[0]):
                            temptoken.ApplyActions(rule.Tokens[0].action, None)
                            return lex, temptoken.features

    for prefix in _PrefixList:
        if word.startswith(prefix):
            #logging.info("stemming: {} has suffix of {}".format(word, suffix))
            rules = _PrefixDict[prefix]
            tempstem = word[len(prefix):]
            wordtoken = Tokenization.SentenceNode(tempstem)
            wordtoken.features.update(StemFeatures(tempstem))
            for rule in rules:
                if LogicOperation.LogicMatch_notpointer(wordtoken, rule.Tokens[0]):
                    wordtoken.ApplyActions(rule.Tokens[0].action, None)
                    return wordtoken, wordtoken.features
                else:
                    lex, features = Stemming_longest_surfixprefix(tempstem, firstlevel=False)
                    if features:
                        temptoken = Tokenization.SentenceNode(tempstem)
                        temptoken.features.update(features)
                        temptoken.features.update(wordtoken.features)
                        if LogicOperation.LogicMatch_notpointer(temptoken, rule.Tokens[0]):
                            temptoken.ApplyActions(rule.Tokens[0].action, None)
                            return lex, temptoken.features
    return None, []


#stemming_version can be "stem" or "suffix", this determines which side gets the longest-rule
def ApplyLexicon(node):
    global _SuffixDict

    if not hasattr(ApplyWordLengthFeature, "LengthDict"):
        ApplyWordLengthFeature.LengthDict = InitLengthSet()
        ApplyWordLengthFeature.LengthSet = set(ApplyWordLengthFeature.LengthDict.values())

    OOVFeatureSet = {utils.FeatureID_JM, utils.FeatureID_JM2, utils.FeatureID_JS, utils.FeatureID_JS2 }
    OOVFeatureSet |= ApplyWordLengthFeature.LengthSet

    lex = SearchLexicon(node.text)
    # if not node.lexicon:    # If lexicon is assigned before, then don't do the search
    #                         #  because the node.word is not as reliable as stem.
    #     node.lexicon = SearchLexicon(node.word)

    #attempt stemming if lexicon fails (O.O)
    word = node.text.lower()
    if lex is None and len(word) >= 4:
        lex, stemming_features = Stemming(word)
        if lex:
            logging.info("From word {}, found stem {}".format(word, lex))

        # not to use this one, because we don't need to get parents of these features.
        # for f in stemming_features:
        #       node.ApplyFeature(f)

        node.features.update(stemming_features)

    if lex is None:
        if utils.IsCD(node.text):
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

        #to have correct stem, e.g. carries -> carrie -> carry

        node.atom = lex.atom
        if utils.FeatureID_NEW in lex.features:
            node.features = set()
            node.features.update(lex.features)
            node.features.remove(utils.FeatureID_NEW)
        else:
            node.features.update(lex.features)
        # _ApplyWordStem(node, lex) (o.o)
        if len(node.features) == 0 or \
                len(node.features - OOVFeatureSet) == 0:
            node.ApplyFeature(utils.FeatureID_OOV)
            # node.features.add(utils.FeatureID_OOV)


    ApplyWordLengthFeature(node)
    node.ApplyFeature(utils.FeatureID_0)
    return node


from enum import Enum
class FoundSuffixPrefix(Enum):
    NotFound = 0     # all "normal lexicons". Including Lookup Lex, Customer
    Suffix = 1      # for combining tokens (without space)
    Prefix = 2    # not quite trusted, lower weight.

def LoadPrefixSuffix(inf_location):
    global _SuffixDict, _PrefixDict
    import Rules
    suffix = ''
    prefix = ''
    for rule in Rules.RuleGroupDict[inf_location].RuleList:
        Found = FoundSuffixPrefix.NotFound
        for token in rule.Tokens:
            if token.AndText:
                if token.AndText.startswith("-"):
                    suffix = token.AndText.lstrip("-")
                    token.AndText = ""
                    Found = FoundSuffixPrefix.Suffix
                elif token.AndText.endswith("-"):
                    prefix = token.AndText.rstrip("-")
                    token.AndText = ""
                    Found = FoundSuffixPrefix.Prefix

            for action in token.action.split():
                StemFeatureIDSet.add(GetFeatureID(action))

        if Found == FoundSuffixPrefix.Suffix:
            if suffix in _SuffixDict:
                _SuffixDict[suffix].append(rule)
            else:
                _SuffixDict[suffix] = [rule]  #   a list
        elif Found == FoundSuffixPrefix.Prefix:
            if prefix in _PrefixDict:
                _PrefixDict[prefix].append(rule)
            else:
                _PrefixDict[prefix] = [rule]  # a list


def ApplyCaseFeatureToNodes(NodeList):
    node = NodeList.head
    while node:
        ApplyCaseFeature(node)
        node = node.next
    return


def ApplyCaseFeature(node):
    word = node.text
    case = "caseaB"
    if word.islower():
        case = "caseab"
    elif word.isupper():
        case = "caseAB"
    elif word[1:].islower():
        if word[0].isupper():
            case = "caseAb"
    node.features.add(GetFeatureID(case))
    return


# Lookup will be used right after segmentation.
# Dynamic programming?
def LexiconLookup(strTokens, lookupsource):
    if lookupsource == utils.LexiconLookupSource.STEMCOMPOUND:
        LexiconLookupStemCompound(strTokens)
        return

    if not hasattr(LexiconLookup, "MaxCompoundLength"):
        LexiconLookup.MaxCompoundLength = {}
    if lookupsource not in LexiconLookup.MaxCompoundLength:
        LexiconLookup.MaxCompoundLength[lookupsource] = 0
        for c in _LexiconLookupSet[lookupsource]:
            if lookupsource in [utils.LexiconLookupSource.COMPOUND, utils.LexiconLookupSource.COMPOUND_SENSITIVE]:
                compoundlength = c.count("_")
            else:
                compoundlength = len(c)
            if compoundlength > LexiconLookup.MaxCompoundLength[lookupsource]:
                LexiconLookup.MaxCompoundLength[lookupsource] = compoundlength

        logging.info("LexiconLookup.MaxCompoundLength[{}] = {}".format(lookupsource, LexiconLookup.MaxCompoundLength[lookupsource]))

    sentenceLenth = strTokens.size
    bestScore = [1 for _ in range(sentenceLenth + 1)]

    i = 0

    pi = strTokens.head
    while pi.next:
        if pi.text == '':
            pi = pi.next
            i += 1
            continue

        j = i
        #pi = pi.next
        pj = pi.next
        if lookupsource == utils.LexiconLookupSource.COMPOUND_SENSITIVE:
            combinedText = pi.text
        else:
            combinedText = pi.text.lower()
        combinedCount = 1
        while pj:
            j += 1
            if j > i+LexiconLookup.MaxCompoundLength[lookupsource]:
                break   # no need to add more.
            if not pj.text:
                break
            if lookupsource in [utils.LexiconLookupSource.COMPOUND , utils.LexiconLookupSource.COMPOUND_SENSITIVE]:
                combinedText += "_"

            if lookupsource == utils.LexiconLookupSource.COMPOUND_SENSITIVE:
                combinedText += pj.text
            else:
                combinedText += pj.text.lower()
            combinedCount += 1

            if bestScore[j] < combinedCount and combinedText in _LexiconLookupSet[lookupsource]:
                logging.debug("LexiconLookup() combinedCount = " + str(combinedCount) + " combinedText=" + combinedText + " in dict.")
                bestScore[j] = combinedCount
            pj = pj.next

        pi = pi.next
        i += 1
    #logging.debug("After one iteration, the bestScore list is:" + str(bestScore))

    i = strTokens.size - 1
    while i > 0:
        if bestScore[i] > 1:
            compound = False
            if lookupsource in [utils.LexiconLookupSource.COMPOUND , utils.LexiconLookupSource.COMPOUND_SENSITIVE]:
                compound = True
            NewNode = strTokens.combine(i - bestScore[i] + 1, bestScore[i], -1, compound)
            i = i - bestScore[i]
            ApplyLexicon(NewNode)
            #strTokens._setnorms()
            if lookupsource == utils.LexiconLookupSource.EXTERNAL:
                NewNode.ApplyFeature(utils.FeatureID_External)
            NewNode.sons = []  # For lookup, eliminate the sons
            #logging.debug("NewNodeAfterLexiconLookup:" + str(strTokens.get(i)))
        else:
            i = i - 1

# For the longstring can be 'brulajho+N_efik+N'
# the output is [brulajho_efik, brulajho+N_efik, brulajho_efik+N, brulajho+N_efik+N]
def WithOrWithoutPlus(longstring):
    output = ['']
    for word in longstring.split("_"):
        if "+" not in word:
            output = [(s + "_" + word).strip("_") for s in output]
        else:
            originword, _ = word.split("+", 1)
            output2 = [(s + "_" + originword).strip("_") for s in output]
            output2 += [(s + "_" + word).strip("_") for s in output]
            output = output2

    return output


# Lookup will be used right after segmentation.
# Dynamic programming?
def LexiconLookupStemCompound(strTokens):
    if not hasattr(LexiconLookupStemCompound, "MaxStemCompoundLength"):
        LexiconLookupStemCompound.MaxStemCompoundLength = 0
        for c in _LexiconLookupSet[utils.LexiconLookupSource.STEMCOMPOUND]:
            compoundlength = c.count("_")
            if compoundlength > LexiconLookupStemCompound.MaxStemCompoundLength:
                LexiconLookupStemCompound.MaxStemCompoundLength = compoundlength

        logging.info("At maximum there are {} words in one stem (MaxStemCompoundLength)".format(LexiconLookupStemCompound.MaxStemCompoundLength))

    sentenceLenth = strTokens.size
    bestScore = [1 for _ in range(sentenceLenth + 1)]

    i = 0


    pi = strTokens.head
    while pi.next:
        if pi.atom == '':
            pi = pi.next
            i += 1
            continue
        j = i
        pj = pi.next
        combinedText = pi.atom


        combinedCount = 1
        while pj:
            j += 1
            if j > i+LexiconLookupStemCompound.MaxStemCompoundLength:
                break   # no need to add more.
            if not pj.atom:
                break   # we don't do things across an empty token.
            combinedText += "_"
            combinedText += pj.atom
            combinedCount += 1

            if bestScore[j] < combinedCount:
                posiblecombinations = WithOrWithoutPlus(combinedText)   # Check all combinations
                for c in posiblecombinations:
                    if c in _LexiconLookupSet[utils.LexiconLookupSource.STEMCOMPOUND]:
                        logging.info("LexiconLookupStemCompound() combinedCount = {} combinedText={} in dict.".format(combinedCount, c))
                        bestScore[j] = combinedCount
                        break
            pj = pj.next
        pi = pi.next
        i += 1

    stemcompoundnode = None
    i = strTokens.size - 1
    while i > 0:
        if bestScore[i] > 1:
            tempnewnode, _, _ = strTokens.newnode(i - bestScore[i] + 1, bestScore[i], compound=True)
            logging.info("After stemcompound, the atom is:{}".format(tempnewnode.atom))
            posiblecombinations = WithOrWithoutPlus(tempnewnode.atom)  # Check all combinations

            for c in posiblecombinations:
                if c in _LexiconLookupSet[utils.LexiconLookupSource.STEMCOMPOUND]:
                    stemcompoundnode = _StemDict[c]
                    break
            if stemcompoundnode.headid == -1:    # default, last one
                headnode = strTokens.get(i - bestScore[i] + 1 + bestScore[i] +stemcompoundnode.headid)
            else:
                headnode = strTokens.get(i - bestScore[i] + 1+stemcompoundnode.headid)

            NewNode = strTokens.combine(i - bestScore[i] + 1, bestScore[i], -1, compound=True)
            i = i - bestScore[i]

            NewNode.features.update(stemcompoundnode.features)
            NewNode.features.update(headnode.features)

            # for f in stemcompoundnode.features:
            #     NewNode.ApplyFeature(f)
            # for f in headnode.features:
            #     if f in StemFeatureIDSet:
            #         NewNode.ApplyFeature(f)

            NewNode.sons = []  # For lookup, eliminate the sons
            # logging.debug("NewNodeAfterLexiconLookup:" + str(strTokens.get(i)))
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
    LoadLexicon('../../fsa/X/defPlus.txt', lookupSource=utils.LexiconLookupSource.DefLex)
    # LoadLexicon('../../fsa/X/perX.txt', lookupSource=utils.LexiconLookupSource.External)
    #
    #
    # para = dir_path + '/../../fsa/X/perX.txt'
    # LoadLexicon(para)
    # para = dir_path + '/../../fsa/X/defLexX.txt'
    # LoadLexicon(para, lookupSource=utils.LexiconLookupSource.DefLex)
    # if "/fsa/X" in para:
    #     Englishflag = False
    # else:
    #     Englishflag = True
    # print(OutputLexicon(Englishflag))
    print(OutputMissingFeatureSet())
