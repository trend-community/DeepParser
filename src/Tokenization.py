#!/bin/python
#Process Sentence tokens.

import string
import FeatureOntology, Lexicon
import utils    #for the Feature_...
from utils import *


class SentenceLinkedList:
    def __init__(self):
        self.head = None
        self.tail = None
        self.size = 0
        self.norms = []
        self.get_cache = {} # this cache is reset at each _setnorms().
        self.isPureAscii = True     # set at append() and insert().

    def append(self, node):    #Add to the tail
        if not self.head:
            self.head = node
            self.tail = node
        else:
            node.prev = self.tail
            node.next = None
            self.tail.next = node
            self.tail = node
        self.size += 1
        self._setnorms()
        if self.isPureAscii and IsAscii(node.text):
            self.isPureAscii = True
        else:
            self.isPureAscii = False

    def appendnodelist(self, nodelist):    #Add to the tail
        if not self.head:
            self.head = nodelist.head
            self.tail = nodelist.tail
        else:
            nodelist.head.prev = self.tail
            #node.next = None       #if the node has next, then keep the next.
            self.tail.next = nodelist.head
            self.tail = nodelist.tail
        self.size += nodelist.size
        self._setnorms()
        # if self.isPureAscii and IsAscii(node.text):
        #     self.isPureAscii = False

    def insert(self, node, position):    #Add to the specific position
        if position == 0:
            if not self.head:
                self.head = node
                self.tail = node
            else:
                node.prev = None
                node.next = self.head
                self.head.prev = node
                self.head = node
        elif position == self.size:
            node.prev = self.tail
            self.tail.next = node
            self.tail = node
        else:
            x = self.get(position)
            node.prev = x.prev
            node.next = x
            x.prev.next = node
            x.prev = node

        self.size += 1
        self._setnorms()
        if self.isPureAscii and IsAscii(node.text):
            self.isPureAscii = True
        else:
            self.isPureAscii = False

    def remove(self, node):
        if node == self.head:
            self.head = node.next
        else:
            node.prev.next = node.next

        if node == self.tail:
            self.tail = node.prev
        else:
            node.next.prev = node.prev

        self.size -= 1
        self._setnorms()

    def searchID(self, ID):
        p = self.head
        nodestack = set()
        while p:
            if p.ID == ID:
                return p

            if p.sons:
                if p.next:
                    nodestack.add(p.next)
                p = p.sons[0]
            else:
                p = p.next
                if p is None and nodestack:
                    p = nodestack.pop()
        logging.error("Failed to find {} in the nodelist.searchID!".format(ID))
        raise Exception("Failed searchID.")
        #return None


    def ClearHITFeatures(self):
        p = self.head
        nodestack = set()
        while p:
            if FeatureID_HIT in p.features:
                p.features.remove(FeatureID_HIT)
            if FeatureID_HIT2 in p.features:
                p.features.remove(FeatureID_HIT2)
            if FeatureID_HIT3 in p.features:
                p.features.remove(FeatureID_HIT3)

            if p.sons:
                if p.next:
                    nodestack.add(p.next)
                p = p.sons[0]
            else:
                p = p.next
                if p is None and nodestack:
                    p = nodestack.pop()


    def get(self, index):
        if index in self.get_cache:
            return self.get_cache[index]

        if not self.head:
            raise RuntimeError("This SentenceLinkedList is null! Can't get.")
        if index >= self.size or index < 0:
            logging.error(self.__str__())
            raise RuntimeError("Can't get " + str(index) + " from the sentence!")
            #return None

        if index <= self.size/2:
            p = self.head
            for i in range(index):
                p = p.next
        else:   # for
            p = self.tail
            for i in range(self.size - index -1):
                p = p.prev

        self.get_cache[index] = p
        return p
        # logging.error(self.__str__())
        # raise RuntimeError("SentenceLinkedList.get(" + str(index) + ") should not get to here.")

    def __str__(self):
        output = "[" + str(self.size) + "]"
        p = self.head
        while p:
            output += str(p)
            p = p.next
        output += str(p)
        return output

    def _setnorms(self):
        self.norms = []
        p = self.head
        while p:
            self.norms += [(p.norm.lower(), p.Head0Text.lower())]
            p = p.next
        self.get_cache.clear()

    #
    # def signature(self, start, limit):
    #     startnode = self.get(start)
    #     p = startnode
    #     sig = [ [] for _ in range(limit)]
    #     accumulatesig = []
    #     for i in range(limit):
    #         accumulatesig.append(p.text)
    #         accumulatesig.append(p.features)
    #         sig[i] = accumulatesig
    #         p = p.next
    #
    #     return sig

    def newnode(self, start, count, compound=False):
        #logging.info("new node: start=" + str(start) + " count=" + str(count))
        if not self.head:
            raise RuntimeError("This SentenceLinkedList is null! Can't combine.")
        if start+count > self.size:
            logging.error(self.__str__())
            raise RuntimeError("Can't get " + str(count) + " items start from " + str(start) + " from the sentence!")

        startnode = self.get(start)
        endnode = self.get(start+count-1)
        p = startnode
        sons = []
        EndOffset = p.StartOffset
        NewText = ""
        NewNorm = ""
        NewAtom = ""
        hasUpperRelations = []
        for i in range(count):
            if i == 0:
                spaces = ""
            else:
                if compound:
                    spaces = "_"
                else:
                    spaces = " " * (p.StartOffset - EndOffset)
            EndOffset = p.EndOffset
            NewText += spaces + p.text
            NewNorm += spaces + p.norm
            NewAtom += spaces + p.atom
            if p.UpperRelationship and p.UpperRelationship != 'H':
                hasUpperRelations.append(FeatureOntology.GetFeatureID("has"+p.UpperRelationship))
            sons.append(p)
            p = p.next

        NewNode = SentenceNode(NewText)
        NewNode.norm = NewNorm
        NewNode.atom = NewAtom
        NewNode.sons = sons
        NewNode.StartOffset = startnode.StartOffset
        NewNode.EndOffset = endnode.EndOffset
        Lexicon.ApplyWordLengthFeature(NewNode)
        for haverelation in hasUpperRelations:
            NewNode.ApplyFeature(haverelation)
        return NewNode, startnode, endnode

    def combine(self, start, count, headindex=0, compound=False):
        if count == 1:
            return self.get(start+headindex) #we don't actually want to just wrap one word as one chunk
        NewNode, startnode, endnode = self.newnode(start, count, compound)

        if headindex >= 0:  # in lex lookup, the headindex=-1 means the feature of the combined word has nothing to do with the sons.
            HeadNode = self.get(start+headindex)
            NewNode.features.update([f for f in HeadNode.features if f not in FeatureOntology.NotCopyList] )
            if utils.FeatureID_0 in HeadNode.features:
                NewNode.Head0Text = HeadNode.norm
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
        endnode.next = None

        self.size = self.size - count + 1
        self._setnorms()

        #logging.debug("NewNode.text: " + NewNode.text + " features:" + str(NewNode.features))
        #logging.debug("combined as:" + str(NewNode))
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
        if length > 1:
            r, _, _ = self.newnode(start, length)
            return r
        else:   # if there is only 1 node, then return this node directly, not to create a parent node. Mar 6, 2018
            return self.get(start)


class SentenceNode(object):
    idCounter = 0
    def __init__(self, word):
        SentenceNode.idCounter += 1
        self.ID = SentenceNode.idCounter
        self.text = word
        self.norm = word.lower()
        self.pnorm = ''
        self.iepair = ''
        self.atom = word.lower()
        self.features = set()

        self.StartOffset = 0
        self.EndOffset = 0
        self.next = None
        self.prev = None
        self.sons = []
        self.UpperRelationship = ''
        #Lexicon.ApplyWordLengthFeature(self)
        self.Head0Text = ''
        self.TempPointer = ''
        #self.FailedRuleTokens = set()
        #self.signature = None
        self.visited = False

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


    def get_chunk_label(self):
        feature_names = [FeatureOntology.GetFeatureName(f) for f in self.features if f not in FeatureOntology.NotShowList]
        BarFeature = utils.LastItemIn2DArray(feature_names, FeatureOntology.BarTags)
        if BarFeature:
            if self.UpperRelationship == SYM_PAIR_HEAD[0]:
                return SYM_PAIR_HEAD[1] + BarFeature + ' '
            elif self.UpperRelationship:
                return self.UpperRelationship + SYM_HYPHEN + BarFeature + ' '
            else:
                return BarFeature + ' '
        return ''  
        
        
    def get_leaf_label(self):
        if not self.text: # deal with empty node
            return ''
        ret = ''
        feature_names = [FeatureOntology.GetFeatureName(f) \
                for f in self.features if f not in FeatureOntology.NotShowList]
        BarFeature = utils.LastItemIn2DArray(feature_names, FeatureOntology.BarTags)
        if not self.UpperRelationship and BarFeature:                       # syntactic role is empty
            ret = BarFeature  + "/" 
        elif self.UpperRelationship == SYM_PAIR_HEAD[0] and BarFeature:     # syntactic role is HEAD
            ret = SYM_PAIR_HEAD[1] + BarFeature  + "/" 
        elif self.UpperRelationship == SYM_PAIR_HEAD[0] and not BarFeature:
            ret = SYM_PAIR_HEAD[1]
        elif self.UpperRelationship != SYM_PAIR_HEAD[0] and BarFeature:     # syntactic role is not HEAD
            ret = self.UpperRelationship + "/" # SYM_HYPHEN + BarFeature # Wei note: POS left out.  For leaf label POS, we do not really care in tracking as long as Relationship is right.
        elif self.UpperRelationship != SYM_PAIR_HEAD[0] and not BarFeature:
            ret = self.UpperRelationship
        return ret
        
        
    def oneliner_ex(self, layer_counter):
        """
            oneliner function - EX version(add labels, use diff parenthesis, ...)
            details in fsa/Y/FSAspecs
        """
        output = ""
        if self.sons \
                and utils.FeatureID_0 not in self.features:
            output += IMPOSSIBLESTRINGLP
            output += self.get_chunk_label() # add XP AND syntactic role label 

            if layer_counter > 0:
                layer_counter -= 1

            for son in self.sons:
                son_output, layer_counter = son.oneliner_ex(layer_counter)
                output += son_output + " "

            output = utils.format_parenthesis(output.strip(), layer_counter)
            layer_counter += 1
        else:
            output += self.get_leaf_label() # + " " # add syntactic role label OR head label 
            output += self.text
        return output.strip(), layer_counter


    def oneliner(self, NoFeature = True):
        """
            basic oneliner function
        """
        output = ""
        if self.sons \
                and utils.FeatureID_0 not in self.features:
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

    def onelinerSegment(self):
        """
            basic oneliner function
        """
        output = ""
        if self.sons \
                and utils.FeatureID_0 not in self.features:
            for son in self.sons:
                output += son.onelinerSegment()
            output = output.strip()
        else:
            if self.text:
                output = self.text+"/"
        return output.strip()



    def oneliner_merge(self, layer_counter):
        """
            oneliner function - merge some tokens for KG
        """
        output = ""
        if self.sons \
                and utils.FeatureID_0 not in self.features:
            output += "<"

            if layer_counter > 0:
                layer_counter -= 1

            for son in self.sons:
                output += son.oneliner_merge(layer_counter) + " "
            output = output.strip() + ">"

            layer_counter += 1
            logging.info('layer_counter:' + str(layer_counter) + ' node:' + self.text + ' output:' + output)
            if self.should_merge():
                merged = '<' + self.text.replace(' ', '') + '>'
                logging.info('merged:' + merged)
                output = re.sub('<.*>', merged, output)
        else:
            output = self.text
        return output.strip()


    def should_merge(self):
        feature_names = [FeatureOntology.GetFeatureName(f) for f in self.features]
        text_len = len(self.text.replace(' ', ''))
        logging.info('feature_names:' + str(feature_names) + ' node len:' + str(len(self.text.replace(' ', ''))))
        if utils.has_overlap(feature_names, FeatureOntology.MergeTokenList) > 0 \
                and 2 <= text_len <= 5:
            return True
        elif ('mn' in feature_names or 'NP' in feature_names) and 2 <= text_len <= 4:
            return True
        return False


    def ApplyDefaultUpperRelationship(self):
        for son in self.sons:
            if not son.UpperRelationship:
                if utils.FeatureID_0 in self.features:
                    son.UpperRelationship = "x"
                else:
                    son.UpperRelationship = "X"


    def ApplyFeature(self, featureID):
        self.features.add(featureID)
        FeatureNode = FeatureOntology.SearchFeatureOntology(featureID)
        if FeatureNode and FeatureNode.ancestors:
            self.features.update(FeatureNode.ancestors)
        #self.signature=pickle.dumps({"w":self.text, "f": self.features})


    def ApplyActions(self, actinstring):
        #self.FailedRuleTokens.clear()
        Actions = actinstring.split()
        #logging.debug("Word:" + self.text)

        if "NEW" in Actions:
            self.features = set()
        if "NEUTRAL"in Actions :
            FeatureOntology.ProcessSentimentTags(self.features)

        HasBartagAction = False
        for Action in Actions:
            # if Action == "NEW":
            #     continue  # already process before.
            # if Action == "NEUTRAL":
            #     continue  # already process before.

            if Action[-1] == "-":
                if Action[0] == "^":    #Remove UpperRelationship
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
                        self.sons=[]        #remove the sons of this
                        self.Head0Text = '' #remove Head0Text.

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

                    for bar0id in [utils.FeatureID_AC, utils.FeatureID_NC, utils.FeatureID_VC]:
                        if bar0id in self.features:
                            self.features.remove(bar0id)

                    FeatureID = FeatureOntology.GetFeatureID(Action.strip("+"))
                    self.ApplyFeature(FeatureID)
                continue

            if Action[0] == "^":
                if "." in Action:
                    self.UpperRelationship = Action.split(".")[-1]
                    RelationActionID = FeatureOntology.GetFeatureID(self.UpperRelationship)
                    if RelationActionID != -1:
                        self.ApplyFeature(RelationActionID)
                    else:
                        logging.warning("Wrong Relation Action to apply:" + self.UpperRelationship + " in action string: " + actinstring)
                    # apply this "has" to the parent (new) node (chunk)
                    # RelationActionID = FeatureOntology.GetFeatureID("has" + self.UpperRelationship)
                    # if RelationActionID != -1:
                    #     self.ApplyFeature(RelationActionID)
                    # else:
                    #     logging.warning("Wrong Relation Action to apply:" + self.UpperRelationship + " in action string: " + actinstring)

                else:
                    logging.error("The Action is wrong: It does not have dot to link to proper pointer")
                    logging.error("  actinstring:" + actinstring)
                    self.UpperRelationship = Action[1:]
                continue

            if Action[0] == '\'':
                #Make the norm of the token to this key
                self.norm = Action[1:-1]
                continue
            if Action[0] == '%':
                #Make the pnorm of the token to this key
                self.pnorm = Action[1:-1]
                continue
            if Action[0] == '/':
                #Make the atom of the token to this key
                self.atom = Action[1:-1]
                continue
            ActionID = FeatureOntology.GetFeatureID(Action)
            if ActionID != -1:
                self.ApplyFeature(ActionID)
            else:
                logging.warning("Wrong Action to apply:" + Action +  " in action string: " + actinstring)


                # strtokens[StartPosition + i + GoneInStrTokens].features.add(ActionID)
        if HasBartagAction:     #only process bartags if there is new bar tag, or trunking (in the combine() function)
            FeatureOntology.ProcessBarTags(self.features)

        #self.signature = pickle.dumps({"w": self.text, "f": self.features})


    def GetFeatures(self):
        featureList = []
        for feature in self.features:
            if feature in FeatureOntology.NotShowList:
                continue
            f = FeatureOntology.GetFeatureName(feature)
            if f:
                featureList.append(f)
            else:
                logging.warning("Can't get feature name of " + self.text + " for id " + str(feature))
        return ",".join(sorted(featureList))

    def CleanOutput(self, KeepOriginFeature=False):
        a = JsonClass()
        a.ID = self.ID
        a.text = self.text
        if self.norm != self.text:
            a.norm = self.norm
        if self.pnorm:
            a.pnorm = self.pnorm
        if self.iepair:
            a.iepair = self.iepair
        if self.atom != self.text:
            a.atom = self.atom
        a.features = sorted([FeatureOntology.GetFeatureName(f) for f in self.features if f not in FeatureOntology.NotShowList])

        if KeepOriginFeature:
            a.features = sorted([FeatureOntology.GetFeatureName(f) for f in self.features ])
            if self.Head0Text:
                a.Head0Text = self.Head0Text

        a.StartOffset = self.StartOffset
        a.EndOffset = self.EndOffset
        if self.UpperRelationship:
            a.UpperRelationship = self.UpperRelationship

        if self.sons \
                and utils.FeatureID_0 not in self.features:  #not to export lower than 0
            a.sons = [s.CleanOutput(KeepOriginFeature) for s in self.sons]

        return a

    def CleanOutput_Propagate(self, propogate_features=None):
        Features_ToPropogate = {utils.FeatureID_Subj, utils.FeatureID_Obj, utils.FeatureID_Pred}
        propogate_f = Features_ToPropogate.intersection(self.features)

        a = JsonClass()
        a.text = self.text
        if self.norm != self.text:
            a.norm = self.norm
        if self.pnorm:
            a.pnorm = self.pnorm
        if self.iepair:
            a.iepair = self.iepair
        if self.atom != self.text:
            a.atom = self.atom
        a.features = [FeatureOntology.GetFeatureName(f) for f in self.features if f not in FeatureOntology.NotShowList]

        if utils.FeatureID_H in self.features and propogate_features:
            #logging.info("\t\tApplying " + str(propogate_features) + " to " + str(self))
            a.features.extend([FeatureOntology.GetFeatureName(f) for f in propogate_features])
            propogate_f.update(propogate_features)

        a.StartOffset = self.StartOffset
        a.EndOffset = self.EndOffset
        if self.UpperRelationship:
            a.UpperRelationship = self.UpperRelationship

        if self.sons \
                and utils.FeatureID_0 not in self.features:
            a.sons = [s.CleanOutput_Propagate(propogate_f) for s in self.sons]

        return a

    def CleanOutput_FeatureLeave(self):
        a = JsonClass()
        a.text = self.text
        if self.norm != self.text:
            a.norm = self.norm
        if self.pnorm:
            a.pnorm = self.pnorm
        if self.iepair:
            a.iepair = self.iepair
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
        if self.sons \
                and utils.FeatureID_0 not in self.features:
            a.sons = [s.CleanOutput_FeatureLeave() for s in self.sons]

        #logging.info("in featureleave" + str(self) + "f:" + str(features))
        return a




#2018030: Make space as one token. Will be removed and add spaceH/spaceQ for adjacent token in the next step.
def _Tokenize_Space(sentence):
    segments = []
    attribute_prev = True     #will be overwritten immediately when i==0
    substart = 0
    for i in range(len(sentence)):
        isdigit = sentence[i].isdigit()
        isalpha = sentence[i].isalpha()
        isspace = sentence[i].isspace()
        if i == 0:
            attribute_prev = [isdigit, isalpha, isspace]
            continue
        if  [isdigit, isalpha, isspace] != attribute_prev \
                or sentence[i] in string.punctuation or sentence[i-1] in string.punctuation:   #always make punctuation a single token
            segments += [sentence[substart:i]]
            substart = i
            attribute_prev = [isdigit, isalpha, isspace]
    if substart < len(sentence):
        segments += [sentence[substart:]]
    return segments


# for the mix of Chinese/Ascii. Should be called for all sentences.
def Tokenize_CnEnMix(sentence):
    sentence = ReplaceCuobieziAndFanti(sentence)

    segmentedlist = _Tokenize_Lexicon_minseg(sentence)

    TokenList = SentenceLinkedList()
    start = 0
    SpaceQ = False
    HanziQ = False
    spacetoken = None
    attribute_prev = None
    for t in segmentedlist:
        isspace = t[0].isspace()
        if isspace: #
            attribute_prev = None
            if SpaceQ and spacetoken:
                spacetoken.text += t
                spacetoken.EndOffset += len(t)
            else:
                TokenList.tail.ApplyFeature(utils.FeatureID_SpaceH)
                if HanziQ:  #if the previous token is Hanzi, and next token is Hanzi, then have a "space" token.
                    spacetoken = SentenceNode(t)
                    spacetoken.norm = ' '   # no matter how many spaces in text, the norm has only 1 space
                    spacetoken.atom = ' '
                    spacetoken.StartOffset = start
                    spacetoken.EndOffset = start + len(t)
                    spacetoken.ApplyFeature(utils.FeatureID_CM)
                    HanziQ = False
                    #TokenList.append(spacetoken)
                SpaceQ = True
            start = start + len(t)
            continue

        isHanzi = not IsAscii(t)
        ispunctuate = t[0] in string.punctuation
        if ispunctuate or isHanzi:# or len(t) > 1:         #when len(t)>1, that is a word.
            attribute_prev = None
            token = SentenceNode(t)
            token.StartOffset = start
            token.EndOffset = start + len(t)
            HanziQ = not IsAscii(t)

            if SpaceQ:
                token.ApplyFeature(utils.FeatureID_SpaceQ)
                SpaceQ = False
                if HanziQ and not IsAscii(TokenList.tail.norm):
                    #if the previous is space, the last one in TokenList is Hanzi, and current one is Hanzi
                    # then add space token with the CM feature.
                    TokenList.append(spacetoken)

            TokenList.append(token)
            start = start + len(t)
            continue

        #t is len of 1.
        isdigit = t.isdigit()
        isalpha = t.isalpha()
        if attribute_prev == [isHanzi, isdigit, isalpha, isspace]:
            TokenList.tail.text += t
            TokenList.tail.norm += t.lower()
            #TokenList.tail.pnorm += t.lower()
            TokenList.tail.atom += t.lower()
            TokenList.tail.EndOffset += len(t)
            #Lexicon.ApplyWordLengthFeature(TokenList.tail)
            start += len(t)
        else:
            attribute_prev = [isHanzi, isdigit, isalpha, isspace]
            token = SentenceNode(t)
            if SpaceQ:
                token.ApplyFeature(utils.FeatureID_SpaceQ)
                SpaceQ = False
            TokenList.append(token)
            token.StartOffset = start
            token.EndOffset = start + len(t)
            start += len(t)

#    logging.debug(TokenList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
    PuncSet = {"，", "：","（", "）","／","＜","＞","？","；","“","”","【","】"
        ,"｛","｝","｜","～","！","＠","＃","＄","％","＆","＊","－","＝","＿","＋"
        ,"。。。","。。。。","。。。。。","。。。。。。","．","《","》","。","、","•","丶","￥","@@","——","————"}
    p = TokenList.head
    while p:
        if p.text.isspace():
            if p.prev and p.prev.text in PuncSet:
                TokenList.remove(p)
        p = p.next
    # print (TokenList)

    return TokenList

#
# # for the mix of Chinese/Ascii. Should be called for all sentences.
# def Tokenize_CnEnMix_origin(sentence):
#     subsentence = []
#     subsentence_isascii = []
#     isascii = True
#     isdigit = True
#     isascii_prev = True     #will be overwritten immediately when i==0
#     substart = 0
#     sentence = ReplaceCuobieziAndFanti(sentence)
#
#     for i in range(len(sentence)):
#         isascii = IsAscii(sentence[i])
#         if i == 0:
#             isascii_prev = isascii
#             continue
#         if isascii != isascii_prev:
#             subsentence += [ sentence[substart:i]]
#             substart = i
#             subsentence_isascii.append( isascii_prev)
#             isascii_prev = isascii
#
#     #last part
#     if substart < len(sentence):
#         subsentence += [sentence[substart:]]
#     subsentence_isascii.append(isascii)
#
#     segmentedlist = []
#     for i in range(len(subsentence)):
#         if subsentence_isascii[i]:
#             segmentedlist += _Tokenize_Space(subsentence[i])
#         else:
#             segmentedlist += _Tokenize_Lexicon_minseg(subsentence[i])
#
#     TokenList = SentenceLinkedList()
#     start = 0
#     SpaceQ = False
#     HanziQ = False
#     spacetoken = None
#     for t in segmentedlist:
#         if t[0] == " ": #
#             TokenList.tail.ApplyFeature(utils.FeatureID_SpaceH)
#             if HanziQ:  #if the previous token is Hanzi, and next token is Hanzi, then have a "space" token.
#                 spacetoken = SentenceNode(t)
#                 spacetoken.norm = ' '   # no matter how many spaces in text, the norm has only 1 space
#                 spacetoken.atom = ' '
#                 spacetoken.StartOffset = start
#                 spacetoken.EndOffset = start + len(t)
#                 spacetoken.ApplyFeature(utils.FeatureID_CM)
#                 HanziQ = False
#                 #TokenList.append(spacetoken)
#             SpaceQ = True
#             start = start + len(t)
#             continue
#         token = SentenceNode(t)
#         token.StartOffset = start
#         token.EndOffset = start + len(t)
#         HanziQ = not IsAscii(t)
#
#         if SpaceQ:
#             token.ApplyFeature(utils.FeatureID_SpaceQ)
#             SpaceQ = False
#             if HanziQ and not IsAscii(TokenList.tail.norm):
#                 #if the previous is space, the last one in TokenList is Hanzi, and current one is Hanzi
#                 # then add space token with the CM feature.
#                 TokenList.append(spacetoken)
#
#         TokenList.append(token)
#         start = start + len(t)
#
# #    logging.debug(TokenList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())
#     return TokenList


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
    for i in range(2, sentLen+1):
        for j in range(1, i+1 ):
            if j == i:
                singlevalue = 1
            else:
                singlevalue = Lexicon._LexiconSegmentDict.get(sentence[j-1:i], 0)
                if lexicononly and singlevalue < 1.2:
                    continue
            if singlevalue == 0:
                continue
            if (1/singlevalue) + bestScore[j-1] < bestScore[i]:
                bestPhraseLen[i] = i + 1 - j
                bestScore[i] = (1/singlevalue) + bestScore[j-1]
            elif 1 + bestScore[j - 1] == bestScore[i]:
                if (i + 1 - j) == 2 and bestPhraseLen[i] in [1, 3]:
                    bestPhraseLen[i] = i + 1 - j
                    bestScore[i] = (1/singlevalue) + bestScore[j-1]

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
            subsegments = _Tokenize_Lexicon_minseg(segment, True)
            segments = subsegments + segments
        else:
            segments = [sentence[i - bestPhraseLen[i]:i]] + segments
        i = i - bestPhraseLen[i]

    return segments


def TrySlash(seg):
    if seg in Lexicon._LexiconSegmentSlashDict:
        return Lexicon._LexiconSegmentSlashDict[seg].split("/")
    else:
        return None


def Tokenize(Sentence):
    return Tokenize_CnEnMix(Sentence.strip())

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

    main_x = Tokenize('科普：。，？带你看懂蜀绣冰壶比赛')
    #old_Tokenize_cn('很少有科普：3 minutes 三分钟带你看懂蜀绣冰壶比赛')

    import cProfile, pstats

    cProfile.run("LoopTest1(100)", 'restatslex')
    pstat = pstats.Stats('restatslex')
    pstat.sort_stats('time').print_stats(10)




