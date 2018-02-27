#!/bin/python
#read a file in main(), then do tokenization.
import requests
import FeatureOntology, Lexicon
import utils    #for the Feature_...
from utils import *

#class EmptyBase(object): pass
#
# def Tokenize(sentence):
#     global DS
#     tokens = nltk.word_tokenize(sentence)
#
#     for token in tokens:
#         Element = EmptyBase()
#         Element.word = token
#         Element.position = 1
#         DS.append(Element)

class SentenceLinkedList:
    def __init__(self):
        self.head = None
        self.tail = None
        self.size = 0

    def append(self, node):    #Add to the tail
        if not self.tail:
            self.head = node
            self.tail = node
        else:
            node.prev = self.tail
            node.next = None
            self.tail.next = node
            self.tail = node
        self.size += 1

    def insert(self, node, position):    #Add to the specific position
        if not self.tail and position == 0:
            self.head = node
            self.tail = node
        elif position == self.size:
            self.tail.next = node
            node.prev = self.tail
            self.tail = node
        else:
            x = self.get(position)
            if x == self.head:
                self.head = node
                node.prev = None
                node.next = x
                x.prev = node
            else:
                x.prev.next = node
                node.prev = x.prev
                node.next = x
                x.prev = node

        self.size += 1

    def remove(self, node):

        if node != self.head:
            node.prev.next = node.next
        else:
            self.head = node.next
        if node != self.tail:
            node.next.prev = node.prev
        else:
            self.tail = node.prev
        self.size -= 1

    def get(self, index):
        if not self.head:
            raise RuntimeError("This SentenceLinkedList is null! Can't get.")
        if index >= self.size or index < 0:
            logging.error(self.__str__())
            raise RuntimeError("Can't get " + str(index) + " from the sentence!")
            #return None

        if index < self.size/2:
            p = self.head
            for i in range(index):
                p = p.next
            return p
        else:   # for
            p = self.tail
            index = self.size - index -1
            for i in range(index):
                p = p.prev
            return p
        # logging.error(self.__str__())
        # raise RuntimeError("SentenceLinkedList.get(" + str(index) + ") should not get to here.")

    def __str__(self):
        output = "[" + str(self.size) + "]"
        p = self.head
        if not p:
            while not p.next:
                output += str(p)
                p = p.next
            output += str(p)
        return output

    # def toJSON(self):
    #     a = JsonClass()
    #     a.text = self.text
    #     if self.norm != self.text:
    #         a.norm = self.norm
    #     if self.atom != self.text:
    #         a.atom = self.atom
    #     a.features = [FeatureOntology.GetFeatureName(f) for f in self.features]
    #
    #     a.StartOffset = self.StartOffset
    #     a.EndOffset = self.EndOffset



    def signature(self, start, limit):
        startnode = self.get(start)
        p = startnode
        sig = [ [] for _ in range(limit)]
        accumulatesig = []
        for i in range(limit):
            accumulatesig.append(p.text)
            accumulatesig.append(p.features)
            sig[i] = accumulatesig
            p = p.next

        return sig

    def newnode(self, start, count):
        #logging.info("new node: start=" + str(start) + " count=" + str(count))
        if not self.head:
            raise RuntimeError("This SentenceLinkedList is null! Can't combine.")
        if start+count > self.size:
            logging.error(self.__str__())
            raise RuntimeError("Can't get " + str(count) + " items start from " + str(start) + " from the sentence!")

        startnode = self.get(start)
        endnode = self.get(start+count-1)
        p = startnode
        NewTextList = []
        sons = []
        for i in range(count):
            NewTextList.append(p.text)
            sons.append(p)
            p = p.next

        if IsAscii(NewTextList):
            NewText = " ".join(NewTextList)
        else:
            NewText = "".join(NewTextList)

        NewNode = SentenceNode(NewText)
        NewNode.sons = sons
        NewNode.StartOffset = startnode.StartOffset
        NewNode.EndOffset = endnode.EndOffset
        return NewNode, startnode, endnode

    def combine(self, start, count, headindex=0):
        if count == 1:
            return  #we don't actually want to just wrap one word as one chunk
        NewNode, startnode, endnode = self.newnode(start, count)

        if headindex >= 0:  # in lex lookup, the headindex=-1 means the feature of the combined word has nothing to do with the sons.
            HeadNode = self.get(start+headindex)
            NewNode.features.update([f for f in HeadNode.features if f not in FeatureOntology.NotCopyList] )
            #FeatureOntology.ProcessBarTags(NewNode.features)
            if utils.FeatureID_0 in HeadNode.features:
                NewNode.Head0Text = HeadNode.text
            else:
                NewNode.Head0Text = HeadNode.Head0Text

        if utils.FeatureID_JS2 in startnode.features:
            NewNode.ApplyFeature(utils.FeatureID_JS2)
        if utils.FeatureID_JM2 in endnode.features:
            NewNode.ApplyFeature(utils.FeatureID_JM2)
        if utils.FeatureID_JM in endnode.features:
            NewNode.ApplyFeature(utils.FeatureID_JM)

        NewNode.prev = startnode.prev
        if startnode != self.head:
            startnode.prev.next = NewNode
        else:
            self.head = NewNode
        NewNode.next = endnode.next
        if endnode != self.tail:
            endnode.next.prev = NewNode
        else:
            self.tail = NewNode

        self.size = self.size - count + 1

        logging.debug("NewNode.text: " + NewNode.text + " features:" + str(NewNode.features))
        logging.debug("combined as:" + str(NewNode))
        return NewNode

    def root(self, KeepOrigin=False):
        if self.size < 1:
            logging.warning("A root with size 0!")
            return None
        length = self.size
        start = 0
        if not KeepOrigin:
            start = 1       #remove the first token (JS)
            if self.tail.text == "":
                length -= 1 #remove the JM token if it is blank

        length = length - start
        r, _, _ = self.newnode(start, length)
        return r


class SentenceNode(object):
    def __init__(self, word):
        self.text = word
        self.norm = word.lower()
        self.atom = word.lower()
        self.features = set()

        self.StartOffset = 0
        self.EndOffset = 0
        self.next = None
        self.prev = None
        self.sons = []
        self.UpperRelationship = ''
        Lexicon.ApplyWordLengthFeature(self)
        self.Head0Text = ''
        self.TempPointer = ''

    #     #From webservice, only word/StartOffset/features are set,
    #     #    and the features are "list", need to change to "set"
    # def populatedefaultvalue(self):
    #     self.text = self.word
    #     self.norm = self.text.lower()
    #     self.atom = self.text.lower()
    #     self.features = set()
    #     for featurename in self.featurenames:
    #         self.ApplyFeature(FeatureOntology.GetFeatureID(featurename))
    #
    #     self.EndOffset = self.StartOffset + len(self.text)
    #     self.sons = []
    #     self.next = None
    #     self.prev = None
    #     self.sons = []
    #     self.UpperRelationship = ''
    #     self.Head0Text = ''

    def __str__(self):
        output = "[" + self.text + "] "
        featureString = self.GetFeatures()
        if featureString:
            output += ":" + featureString
        return output

    def oneliner(self, NoFeature = True):
        output = ""
        if self.sons:
            output += "<"
            for son in self.sons:
                output += son.oneliner() + " "
            output = output.strip() + ">"
        else:
            output = self.text
        if not NoFeature:
            featureString = self.GetFeatures()
            if featureString:
                output += ":" + featureString + ";"
        return output.strip()

    def ApplyFeature(self, featureID):
#        == do the bartag in here?
        self.features.add(featureID)
        FeatureNode = FeatureOntology.SearchFeatureOntology(featureID)
        if FeatureNode and FeatureNode.ancestors:
            self.features.update(FeatureNode.ancestors)

    def ApplyActions(self, actinstring):
        Actions = actinstring.split()
        logging.debug("Word:" + self.text)

        if "NEW" in Actions:
            self.features = set()

        HasBartagAction = False
        for Action in Actions:
            if Action == "NEW":
                continue  # already process before.

            if Action[-1] == "-":
                if Action[0] == "^":

                    if "." in Action:
                        if self.UpperRelationship == Action.split(".", 1)[1][-1]:
                            # TODO:  actually break the token. not just delattr
                            delattr(self, "UpperRelationship")
                            logging.warning(" TODO:  actually break the token. not just delattr Remove Relationship:" + Action)
                    else:
                        logging.warning("This Action is not right:" + Action)
                    continue

                FeatureID = FeatureOntology.GetFeatureID(Action.strip("-"))
                if FeatureID in self.features:
                    self.features.remove(FeatureID)
                continue

            if Action[-1] == "+":
                if Action[-2] == "+":
                    if Action[-3] == "+":    #"+++"
                        self.ApplyFeature(utils.FeatureID_0)
                    else:                   #"X++":
                        #this should be in a chunk, only apply to the new node
                        HasBartagAction = True
                        FeatureID = FeatureOntology.GetFeatureID(Action.strip("++"))
                        self.ApplyFeature(FeatureID)
                else:                       #"X+"
                #MajorPOSFeatures = ["A", "N", "P", "R", "RB", "X", "V"]
                #Feb 20, 2018: use the BarTagIDs[0] as the MajorPOSFeatures.
                    for bar0id in FeatureOntology.BarTagIDs[0]:
                        if bar0id in self.features:
                            self.features.remove(bar0id)

                    FeatureID = FeatureOntology.GetFeatureID(Action.strip("+"))
                    self.ApplyFeature(FeatureID)
                continue

            if Action[0] == "^":
                # TODO: linked the str tokens.
                if "." in Action:
                    self.UpperRelationship = Action.split(".", 1)[1]
                else:
                    logging.error("The Action is wrong: It does not have dot to link to proper pointer")
                    logging.error("  actinstring:" + actinstring)
                    self.UpperRelationship = Action[1:]
                continue

            ActionID = FeatureOntology.GetFeatureID(Action)
            if ActionID != -1:
                self.ApplyFeature(ActionID)
            else:
                logging.warning("Wrong Action to apply:" + Action +  " in action string: " + actinstring)

                # strtokens[StartPosition + i + GoneInStrTokens].features.add(ActionID)
        if HasBartagAction:     #only process bartags if there is new bar tag, or trunking (in the combine() function)
            FeatureOntology.ProcessBarTags(self.features)


    def GetFeatures(self):
        featureString = ""
        for feature in sorted(self.features):
            if feature in FeatureOntology.NotShowList:
                continue
            f = FeatureOntology.GetFeatureName(feature)
            if f:
                if featureString:
                    featureString += ","
                featureString += f
            else:
                logging.warning("Can't get feature name of " + self.text + " for id " + str(feature))
        return featureString

    def CleanOutput(self, KeepOriginFeature=False):
        a = JsonClass()
        a.text = self.text
        if self.norm != self.text:
            a.norm = self.norm
        if self.atom != self.text:
            a.atom = self.atom
        a.features = [FeatureOntology.GetFeatureName(f) for f in self.features if f not in FeatureOntology.NotShowList]

        if KeepOriginFeature:
            a.features = [FeatureOntology.GetFeatureName(f) for f in self.features ]

        a.StartOffset = self.StartOffset
        a.EndOffset = self.EndOffset
        if self.UpperRelationship:
            a.UpperRelationship = self.UpperRelationship

        if self.sons:
            a.sons = [s.CleanOutput(KeepOriginFeature) for s in self.sons]

        return a

    def CleanOutput_FeatureLeave(self):
        a = JsonClass()
        a.text = self.text
        if self.norm != self.text:
            a.norm = self.norm
        if self.atom != self.text:
            a.atom = self.atom
        features = [FeatureOntology.GetFeatureName(f) for f in Lexicon.CopyFeatureLeaves(self.features)
                        if f not in FeatureOntology.NotShowList]
        for f in features:
            # if isinstance(f, int):
            #     f = "L" + str(f)
            setattr(a, f, '')
        a.StartOffset = self.StartOffset
        a.EndOffset = self.EndOffset
        if self.UpperRelationship:
            a.UpperRelationship = self.UpperRelationship
        if self.sons:
            a.sons = [s.CleanOutput_FeatureLeave() for s in self.sons]

        #logging.info("in featureleave" + str(self) + "f:" + str(features))
        return a


class JsonClass(object):
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                         sort_keys=True, ensure_ascii=False)
    def fromJSON(self):
        pass


def _Tokenize_Space(sentence):
    StartToken = True
    StartPosition = 0
    #for i in range(1, len(sentence)):   #ignore the first one.
    i = 1
    segments = []
    while i<len(sentence):
        c = sentence[i]
        prevc = sentence[i-1]
        if c == "'":
            if 0<i<len(sentence)-1 and sentence[i-1].isalpha() and sentence[i+1].isalpha():
                i+=2
                continue    #when ' sign is inside a word, like can't don't

        if (prevc.isalnum() and not c.isalnum()) or (not prevc.isalnum() and not prevc.isspace()):
            segments += [sentence[StartPosition:i]]
            StartToken = False

        if (c.isalnum() and (not prevc.isalnum()) ) or (not c.isalnum() and not c.isspace()):
            StartToken = True
            StartPosition = i
        i += 1

    if StartToken:  #wrap up the last one
        segments += [sentence[StartPosition:]]

    return segments


# for the mix of Chinese/Ascii. Should be called for all sentences.
def Tokenize_CnEnMix(sentence):
    subsentence = []
    subsentence_isascii = []
    isascii = True
    isascii_prev = True     #will be overwritten immediately when i==0
    substart = 0
    sentence = ReplaceCuobieziAndFanti(sentence)

    for i in range(len(sentence)):
        isascii = IsAscii(sentence[i])
        if i == 0:
            isascii_prev = isascii
            continue
        if isascii != isascii_prev:
            subsentence.append( sentence[substart:i])
            substart = i
            subsentence_isascii.append( isascii_prev)
        isascii_prev = isascii

    #last part
    subsentence.append(sentence[substart:])
    subsentence_isascii.append(isascii)

    segmentedlist = []
    for i in range(len(subsentence)):
        if subsentence_isascii[i]:
            segmentedlist += _Tokenize_Space(subsentence[i])
        else:
            segmentedlist += _Tokenize_Lexicon_minseg(subsentence[i])

    TokenList = SentenceLinkedList()
    start = 0
    for t in segmentedlist:
        Element = SentenceNode(t)
        Element.StartOffset = start
        Element.EndOffset = start + len(t)
        TokenList.append(Element)
        start = start + len(t)

    logging.debug(TokenList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
    return TokenList


def ReplaceCuobieziAndFanti(sentence):
    if not hasattr(ReplaceCuobieziAndFanti, "combinedlist"):
        ReplaceCuobieziAndFanti.combineddict = Lexicon._LexiconCuobieziDict
        ReplaceCuobieziAndFanti.combineddict.update(Lexicon._LexiconFantiDict)
        ReplaceCuobieziAndFanti.combinedlist = sorted(ReplaceCuobieziAndFanti.combineddict, key=len, reverse=True)

    for k in ReplaceCuobieziAndFanti.combinedlist:
        if k in sentence:
            sentence = sentence.replace(k, ReplaceCuobieziAndFanti.combineddict[k])

    return sentence


def _Tokenize_Lexicon_maxweight(sentence, lexicononly=False):
#    TokenList = SentenceLinkedList()
    segments = []

    sentLen = len(sentence)
    bestPhrase = []
    bestPhraseLen = [1] * (sentLen+1)
    bestScore = [0.1*i for i in range(sentLen+1) ]

    ## forward path: fill up "best"
    for i in range(2, sentLen + 1):
        for j in range(1, i+1 ):
            if j == i:
                value = 0.1
            else:
                singlevalue = Lexicon._LexiconSegmentDict.get(sentence[j-1:i], 0)
                if  lexicononly and singlevalue < 1.2:
                    continue
                value = singlevalue * (i+1-j)
            if value == 0:
                continue
            if value + bestScore[j-1] > bestScore[i]:
                bestPhraseLen[i] = i+1 - j
                bestScore[i] = value + bestScore[j-1]
            elif value + bestScore[j-1] == bestScore[i]:
                if (i+1-j) == 2 and bestPhraseLen[i] in [1,3] :
                    bestPhraseLen[i] = i + 1 - j
                    bestScore[i] = value + bestScore[j - 1]

    ## backward path: collect "best"
    i = sentLen
    while i > 0:
        segment = sentence[i - bestPhraseLen[i]:i]
        segmentslashed = TrySlash(segment)
        if segmentslashed:
            if Lexicon._LexiconSegmentDict[segment] < 1.2:
                temp_segments = []
                for segmentslashed in segmentslashed:
                    subsegments = _Tokenize_Lexicon_maxweight(segmentslashed, True)
                    temp_segments += subsegments
                segments = temp_segments + segments
            else:
                segments = segmentslashed + segments
        elif bestPhraseLen[i] > 1 and not lexicononly and Lexicon._LexiconSegmentDict[segment] < 1.2:
            #from main2007.txt, not trustworthy
            subsegments = _Tokenize_Lexicon_maxweight(segment, True)
            segments = subsegments + segments
        else:
            segments = [sentence[i - bestPhraseLen[i]:i]] + segments
        i = i - bestPhraseLen[i]

    return segments


def _Tokenize_Lexicon_minseg(sentence, lexicononly=False):
#    TokenList = SentenceLinkedList()
    segments = []

    sentLen = len(sentence)
    bestPhrase = []
    bestPhraseLen = [1] * (sentLen + 1)
    bestScore = [i for i in range(sentLen + 1)]

    ## forward path: fill up "best"
    for i in range(2, sentLen + 1):
        for j in range(1, i+1):
            if j == i:
                singlevalue = 0.1
            else:
                singlevalue = Lexicon._LexiconSegmentDict.get(sentence[j - 1:i], 0)
                if lexicononly and singlevalue < 1.2:
                    continue
            if singlevalue == 0:
                continue
            if 1 + bestScore[j - 1] < bestScore[i]:
                bestPhraseLen[i] = i + 1 - j
                bestScore[i] = 1 + bestScore[j - 1]
            elif 1 + bestScore[j - 1] == bestScore[i]:
                if (i + 1 - j) == 2 and bestPhraseLen[i] in [1, 3]:
                    bestPhraseLen[i] = i + 1 - j
                    bestScore[i] = 1 + bestScore[j - 1]

    ## backward path: collect "best"
    i = sentLen
    while i > 0:
        segment = sentence[i - bestPhraseLen[i]:i]
        segmentslashed = TrySlash(segment)
        if segmentslashed:
            if Lexicon._LexiconSegmentDict[segment] < 1.2:
                temp_segments = []
                for segmentslashed in segmentslashed:
                    subsegments = _Tokenize_Lexicon_minseg(segmentslashed, True)
                    temp_segments += subsegments
                segments = temp_segments + segments
            else:
                segments = segmentslashed + segments
        elif bestPhraseLen[i] > 1 and not lexicononly and Lexicon._LexiconSegmentDict[segment] < 1.2:
            # from main2007.txt, not trustworthy
            subsegments = _Tokenize_Lexicon_maxweight(segment, True)
            segments = subsegments + segments
        else:
            segments = [sentence[i - bestPhraseLen[i]:i]] + segments
        i = i - bestPhraseLen[i]

    return segments
    #
    # segments = []
    #
    # sentLen = len(sentence)
    # bestPhrase = []
    # bestPhraseLen = [1] * (sentLen+1)
    # bestScore = [i for i in range(sentLen+1)]
    #
    # ## forward path: fill up "best"
    # for i in range(2, sentLen + 1):
    #     for j in range(1, i+1 ):
    #         if j == i:
    #             value = 1
    #         else:
    #             singlevalue = Lexicon._LexiconSegmentDict.get(sentence[j-1:i], 0)
    #             if singlevalue == 0:
    #                 continue
    #             if  lexicononly and singlevalue < 1:
    #                 continue
    #             value = (1/singlevalue) * (i+1-j)
    #         if value + bestScore[j-1] < bestScore[i]:
    #             bestPhraseLen[i] = i+1 - j
    #             bestScore[i] = value + bestScore[j-1]
    #
    # ## backward path: collect "best"
    # i = sentLen
    # while i > 0:
    #     segment = sentence[i - bestPhraseLen[i]:i]
    #     segmentslashed = TrySlash(segment)
    #     if segmentslashed:
    #         segments = segmentslashed + segments
    #     elif bestPhraseLen[i] > 1 and not lexicononly and Lexicon._LexiconSegmentDict[segment] < 1:
    #         #from main2007.txt, not trustworthy
    #         subsegments = _Tokenize_Lexicon_maxweight(segment, True)
    #         segments = subsegments + segments
    #     else:
    #         segments = [sentence[i - bestPhraseLen[i]:i]] + segments
    #     i = i - bestPhraseLen[i]
    #
    # return segments


def TrySlash(seg):
    if seg in Lexicon._LexiconSegmentSlashDict:
        return Lexicon._LexiconSegmentSlashDict[seg].split("/")
    else:
        return None


def Tokenize(Sentence):
    return Tokenize_CnEnMix(Sentence.strip())
    #
    # Sentence = Sentence.strip()
    # if utils.IsAscii(Sentence):
    #     TokenList = Tokenize_Space(Sentence)
    #
    #     # if FeatureOntology._FeatureSet:
    #         #this part is to get tokenize from webservice. not actually practical.
    #     # TokenizeURL = url + "/Tokenize"
    #     # ret_t = requests.post(TokenizeURL, data=Sentence)
    #     # nodes_t = jsonpickle.decode(ret_t.text)
    # else:
    #     TokenList = Tokenize_Lexicon(Sentence)
    #     tl = old_Tokenize_cn(Sentence)
    #
    #     print(TokenList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
    #     print(tl.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
    #
    # return TokenList


def old_Tokenize_cn(Sentence):

    TokenizeURL = ParserConfig.get("main", "url_ch") + "/TokenizeJson/"
    #ret_t = requests.get(TokenizeURL + Sentence)

    data = {'Sentence': URLEncoding(Sentence)}
    try:
        ret = requests.get(TokenizeURL, params=data)
    except requests.exceptions.ConnectionError as e:
        #logging.error(str(e))
        logging.error(data)
        return None
    if ret.status_code>399:
        logging.error("Return code:" + str(ret.status_code))
        logging.error(data)
        return None
    segmented = ret.text
    try:
        Tokens = jsonpickle.decode(segmented)
    except ValueError as e:
        logging.error("Can't be process:")
        logging.error(segmented)
        logging.error(data)
        logging.error(str(e))
        return None

    #logging.info("segmented text=\n" + segmented)

    # Tokens = []
    TokenList = SentenceLinkedList()
    for token in Tokens:

        token.populatedefaultvalue()
        TokenList.append(token)

    logging.debug(TokenList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())

    return TokenList

def LoopTest1(n):
    for _ in range(n):
        Tokenize('響著錄中文规则很长 very long , 为啥是不？')


# def LoopTest2(n):
#     for _ in range(n):
#         old_Tokenize_cn('響著錄中文规则很长 very long , 为啥是不？')

if __name__ == "__main__":
    logging.basicConfig( level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

    logging.info("Start")
    # import ProcessSentence
    # ProcessSentence.LoadCommon()  # too heavy to load for debugging

    FeatureOntology.LoadFeatureOntology('../../fsa/Y/feature.txt')
    Lexicon.LoadSegmentLexicon()
    XLocation = '../../fsa/X/'
    Lexicon.LoadExtraReference(XLocation + 'CuobieziX.txt', Lexicon._LexiconCuobieziDict)
    Lexicon.LoadExtraReference(XLocation + 'Fanti.txt', Lexicon._LexiconFantiDict)

    x = Tokenize('科普：。，？带你看懂蜀绣冰壶比赛')
    #old_Tokenize_cn('很少有科普：3 minutes 三分钟带你看懂蜀绣冰壶比赛')

    import cProfile, pstats

    cProfile.run("LoopTest1(100)", 'restatslex')
    pstat = pstats.Stats('restatslex')
    pstat.sort_stats('time').print_stats(10)




