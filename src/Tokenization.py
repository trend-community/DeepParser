#!/bin/python
#read a file in main(), then do tokenization.
import logging, requests, jsonpickle
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
        if self.tail == None:
            self.head = node
            self.tail = node
        else:
            node.prev = self.tail
            node.next = None
            self.tail.next = node
            self.tail = node
        self.size += 1

    def insert(self, node, position):    #Add to the tail
        if self.tail == None and position == 0:
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

        if (index < self.size/2):
            p = self.head
            counter = 0
            for i in range(index):
                p = p.next
            return p
        else:   # for
            p = self.tail
            index = self.size - index -1
            counter = 0
            for i in range(index):
                p = p.prev
            return p
        logging.error(self.__str__())
        raise RuntimeError("SentenceLinkedList.get(" + str(index) + ") should not get to here.")

    def __str__(self):
        output = "[" + str(self.size) + "]"
        p = self.head
        if p != None:
            while p.next != None:
                output += str(p)
                p = p.next
            output += str(p)
        return output

    def toJSON(self):
        a = JsonClass()
        a.text = self.text
        if self.norm != self.text:
            a.norm = self.norm
        if self.atom != self.text:
            a.atom = self.atom
        a.features = [FeatureOntology.GetFeatureName(f) for f in self.features]

        a.StartOffset = self.StartOffset
        a.EndOffset = self.EndOffset



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
            if utils.FeatureID_0 in HeadNode.features:
                NewNode.Head0Text = HeadNode.text
            else:
                NewNode.Head0Text = HeadNode.Head0Text

        if utils.FeatureID_JS2 in startnode.features:
            NewNode.features.add(utils.FeatureID_JS2)
        if utils.FeatureID_JM2 in endnode.features:
            NewNode.features.add(utils.FeatureID_JM2)
        if utils.FeatureID_JM in endnode.features:
            NewNode.features.add(utils.FeatureID_JM)

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
        if self.size <= 1:
            return None
        length = self.size
        start = 0
        if KeepOrigin==False:
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

        #From webservice, only word/StartOffset/features are set,
        #    and the features are "list", need to change to "set"
    def populatedefaultvalue(self):
        self.text = self.word
        self.norm = self.text.lower()
        self.atom = self.text.lower()
        self.features = set()
        for featurename in self.featurenames:
            self.ApplyFeature(FeatureOntology.GetFeatureID(featurename))

        self.EndOffset = self.StartOffset + len(self.word)
        self.sons = []
        self.next = None
        self.prev = None
        self.sons = []
        self.UpperRelationship = ''
        self.Head0Text = ''

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
        self.features.add(featureID)
        FeatureNode = FeatureOntology.SearchFeatureOntology(featureID)
        if FeatureNode:
            self.features.update(FeatureNode.ancestors)

    def ApplyActions(self, actinstring):

        Actions = actinstring.split()
        logging.debug("Word:" + self.text)

        if "NEW" in Actions:
            self.features = set()
        for Action in Actions:
            if Action == "NEW":
                continue  # already process before.

            if Action[-1] == "-":
                FeatureID = FeatureOntology.GetFeatureID(Action.strip("-"))
                if FeatureID in self.features:
                    self.features.remove(FeatureID)
                continue

            if Action[-1] == "+" and Action != "+++":
                MajorPOSFeatures = ["A", "N", "P", "R", "RB", "X", "V"]
                if Action.strip("+") in MajorPOSFeatures:
                    for conflictfeature in MajorPOSFeatures:
                        conflictfeatureid = FeatureOntology.GetFeatureID(conflictfeature)
                        if conflictfeatureid in self.features:
                            self.features.remove(conflictfeatureid)
                            # TODO: Might also remove the child features of them. Check spec.

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
            if ActionID == FeatureOntology.GetFeatureID("Gone"):
                self.Gone = True
            if ActionID != -1:
                self.ApplyFeature(ActionID)
            if Action == "+++":
                self.ApplyFeature(utils.FeatureID_0)
                # strtokens[StartPosition + i + GoneInStrTokens].features.add(ActionID)

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
                logging.warning("Can't get feature name of " + self.word + " for id " + str(feature))
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


def Tokenize_space(sentence):
    StartToken = True
    StartPosition = 0
    #for i in range(1, len(sentence)):   #ignore the first one.
    i = 1
    TokenList = SentenceLinkedList()
    while i<len(sentence):
        c = sentence[i]
        prevc = sentence[i-1]
        if c == "'":
            if 0<i<len(sentence)-1 and sentence[i-1].isalpha() and sentence[i+1].isalpha():
                i+=2
                continue    #when ' sign is inside a word, like can't don't

        if (prevc.isalnum() and not c.isalnum()) or (not prevc.isalnum() and not prevc.isspace()):
            Element = SentenceNode(sentence[StartPosition:i])
            Element.StartOffset = StartPosition
            Element.EndOffset = i
            TokenList.append(Element)
            StartToken = False

        if (c.isalnum() and (not prevc.isalnum()) ) or (not c.isalnum() and not c.isspace()):
            StartToken = True
            StartPosition = i
        i += 1

    if StartToken:  #wrap up the last one
        Element = SentenceNode(sentence[StartPosition:])
        Element.StartOffset = StartPosition
        Element.EndOffset = len(sentence)
        TokenList.append(Element)

    return TokenList


def Tokenize(Sentence):
    Sentence = Sentence.strip()
    if utils.IsAscii(Sentence):
        TokenList = Tokenize_space(Sentence)

        # if FeatureOntology._FeatureSet:
            #this part is to get tokenize from webservice. not actually practical.
        # TokenizeURL = url + "/Tokenize"
        # ret_t = requests.post(TokenizeURL, data=Sentence)
        # nodes_t = jsonpickle.decode(ret_t.text)
    else:
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

        #logging.info("Tokens encode text=\n" + jsonpickle.encode(Tokens))
        # segmented = segmented.replace("\/", IMPOSSIBLESTRING)
        # blocks = segmented.split("/")
        # Tokens = []
        # for block in blocks:
        #     block = block.replace(IMPOSSIBLESTRING, "/")
        #     WordPropertyPair = block.split(":")
        #     Element = SentenceNode(WordPropertyPair[0])
        #     if len(WordPropertyPair)>1:
        #         features = WordPropertyPair[1]
        #         for feature in features.split():
        #             featureid = FeatureOntology.GetFeatureID(feature)
        #             Element.features.add(featureid)
        #
        #     Tokens.append(Element)
    return TokenList


if __name__ == "__main__":
    logging.basicConfig( level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
    target = "This is a 'bad_sentence', not a word. Don't classify it as a character."
    target = """PassiveSimpleING = {<"being|getting" [RB:^.R]? [VBN|ED:VG Passive Simple Ing]>};"""
    print(target)
    # Tokenize(target)
    # print "\n\n NLTK tokenization:"
    # DisplayDS()

    print("\n\n My tokenization:")
    nodes = Tokenize(target)
    DisplayDS_old(nodes)



