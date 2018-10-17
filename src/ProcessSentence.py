import concurrent.futures
import traceback
import Tokenization,  Lexicon
import Rules, Cache
#from threading import Thread
from LogicOperation import LogicMatch #, Clear_LogicMatch_notpointer_Cache
import DependencyTree
from utils import *
import utils
from datetime import datetime
counterMatch = 0

#WinningRuleDict = {}
invalidchar_pattern = re.compile(u'[^\u0000-\uD7FF\uE000-\uFFFF]', re.UNICODE)
PipeLine = []



def MarkWinningTokens(strtokens, rule, StartPosition):
    result = ""

    p = strtokens.head
    counter = 0
    StopPosition = StartPosition+rule.StrTokenLength - 1
    while p:
        if counter == StartPosition+1:
            result += "<em>"
        result += p.text
        if counter == StopPosition:
            result += "</em>"
        if strtokens.isPureAscii:
            result += " "
        p = p.next
        counter += 1

    return result.strip()


# def StoreWinningRule(strtokens, rule, StartPosition):
#     global WinningRuleDict
#
#     if rule.ID in WinningRuleDict:
#         _, hits = WinningRuleDict[rule.ID]
#         hits.append(MarkWinningTokens(strtokens, rule, StartPosition))
#     else:
#         WinningRuleDict[rule.ID] = [rule, [MarkWinningTokens(strtokens, rule, StartPosition)]]


# def OutputWinningRules():
#     output = ""
#     for rule, hits in sorted(WinningRuleDict.values()):
#         output += '[Rule file]' + rule.FileName +  '[' + str(rule.ID) + '] [Rule origin]' + rule.Origin + ' [Hits_num]' + str(len(hits)) + ' [Hits]\t' + str(hits) + "\n"
#
#     return output


#Every token in ruleTokens must match each token in strTokens, from StartPosition.
def HeadMatch(strTokenList, StartPosition, rule):
    HaveTempPointer = False

    for i in range(rule.TokenLength):
        try:
            if not LogicMatch(strTokenList, i+StartPosition, rule.Tokens[i], rule.Tokens, i):
        #    if not LogicMatch_old(strTokenList, i + StartPosition, ruleTokens[i].word, ruleTokens, i):
                if HaveTempPointer:
                    RemoveTempPointer(strTokenList)
#                if (rule.ID, i) in Rules.RuleIdenticalNetwork:
#                    FailedRules.update(Rules.RuleIdenticalNetwork[(rule.ID, i)])
                return False  #  this rule does not fit for this string
            if rule.Tokens[i].SubtreePointer:
                StartPosition -= 1  # do not skip to next strToken, if this token is for Subtree.
            else:
                if rule.Tokens[i].pointer:
                    HaveTempPointer = True
                    strTokenList.get(i + StartPosition).TempPointer = rule.Tokens[i].pointer
                    #logging.debug("   Set TempPointer: node {} -> {}".format(strTokenList.get(i + StartPosition).text, rule.Tokens[i].pointer))
        except RuntimeError as e:
            logging.error("Error in HeadMatch rule:" + str(rule))
            logging.error("Using " + rule.Tokens[i].word + " to match:" + strTokenList.get(i+StartPosition).text)
            logging.error(e)
            raise
        except Exception as e:
            logging.error("Using " + rule.Tokens[i].word + " to match:" + strTokenList.get(i+StartPosition).text )
            logging.error(e)
            raise
        except IndexError as e:
            logging.error("Using " + rule.Tokens[i].word + " to match:" + strTokenList.get(i+StartPosition).text )
            logging.error(e)
            raise
    return True


def RemoveTempPointer(StrList):
    x = StrList.head
    while x:
        if x.TempPointer:
            x.TempPointer = ''
        x = x.next


# Apply the features, and other actions.
def ApplyWinningRule(strtokens, rule, StartPosition):
    #Clear_LogicMatch_notpointer_Cache()

    if not strtokens:
        logging.error("The strtokens to ApplyWinningRule is blank!")
        raise(RuntimeError("wrong string to apply rule?"))
    #StoreWinningRule(strtokens, rule, StartPosition)

    if rule.TokenLength == 0:
        logging.error("Lenth = 0, error! Need to revisit the parsing process")
        logging.error(str(rule))
        raise(RuntimeError("Rule error"))

    VirtualRuleToken = 0
    for i in range(rule.TokenLength):
        if rule.Tokens[i].SubtreePointer:
            VirtualRuleToken += 1

        if rule.Tokens[i].action:
            try:
                token = strtokens.searchID(rule.Tokens[i].MatchedNodeID)
            except :
                logging.error("Trying to find str token of the rule token {}".format(rule.Tokens[i]))
                logging.error("The strtokens is: {}".format(jsonpickle.dumps(strtokens)))
                raise
            token.ApplyActions(rule.Tokens[i].action)

    if rule.Chunks:
        MaxChunkLevelNum = max(chunk.ChunkLevel for chunk in rule.Chunks)
        for ChunkLevel in range(1,MaxChunkLevelNum+1):
            for chunk in rule.Chunks:   # the chunks are presorted to process right chucks first.
                if chunk.ChunkLevel != ChunkLevel:
                    continue
                newnode = strtokens.combine(StartPosition+chunk.StartOffset, chunk.StringChunkLength, chunk.HeadOffset)
                newnode.ApplyActions(chunk.Action)
                newnode.ApplyDefaultUpperRelationship()

    RemoveTempPointer(strtokens)
    return 0


# Apply the features, and other actions.
def ApplyWinningDagRule(Dag, rule, OpenNode):
    #Clear_LogicMatch_notpointer_Cache()

    for i in range(rule.TokenLength):
        if rule.Tokens[i].action:
            nodeID = rule.Tokens[i].MatchedNodeID
            node = Dag.nodes[nodeID]
            if logging.root.isEnabledFor(logging.DEBUG):
                logging.debug("Start applying action {} to node {}".format(rule.Tokens[i].action, node.text))
            Dag.ApplyDagActions(OpenNode, node, rule.Tokens[i].action, rule)

    for nodeid in Dag.nodes:
        #logging.info("node: {}".format(nodeid))
        Dag.nodes[nodeid].TempPointer = ''  # remove TempPointer after applying action.

    return 0

#list1 is combination of norm and Head0Text.
# either of them equals to the item in list2, that means match.
#from functools import lru_cache
#@lru_cache(maxsize=100000)
def ListMatch(list1, list2):
    # if len(list1) != 2 or  len(list1[0]) != len(list2):
    #     logging.error("Coding error. The size should be the same in ListMatch")
    #     return False
    # for i in range(num):
    #     if list2[i] == '' or \
    #         list1[i][0] == list2[i] or \
    #             list1[i][1] and list1[i][1] == list2[i]:
    #         pass
    #     else:
    #         return False

    i = -1
    for l2item in list2:
        i += 1
        if l2item == '' or \
            list1[i][0] == l2item or \
            list1[i][1] and list1[i][1] == l2item:
            pass
        else:
            return False
    return True

#Note: the _UsingCache version is slower: 25 seconds instead of 16 seconds, for 100 sentences.
# for 4503026 calls, it took 12 seconds, comparing to 4 seconds.
# ListMatchCache = {}
# def ListMatch_UsingCache(list1, list2):
#     l_hash = str(list1+list2)
#     if l_hash in ListMatchCache:
#         return ListMatchCache[l_hash]
#     if len(list1) != len(list2):
#         logging.error("Coding error. The size should be the same in ListMatch")
#         return False
#     for i in range(len(list1)):
#         if list2[i] is None or list1[i] == list2[i]:
#             pass
#         else:
#             ListMatchCache[l_hash] = False
#             return False
#
#     ListMatchCache[l_hash] = True
#     return True

#
# def ConstructNorms(strtokenlist, start):
#     MaxGramSize = 10    #only care for 10 ngram and less.
#
#     StrNorms = []
#     for i in range( MaxGramSize):
#         if start+i >= len(strtokenlist.norms):
#             break
#
#         newset = set()
#         if i == 0:
#             if strtokenlist.norms[start+i][1]:
#                 newset.update(strtokenlist.norms[start+i][1])
#             newset.update(strtokenlist.norms[start+i][0])
#         else:
#             newset2 = set()
#             for strnorms in StrNorms[i - 1]:
#                 if strtokenlist.norms[start+i][1]:
#                     strnorms_copy = copy.copy(strnorms) + strtokenlist.norms[start+i][1]
#                     newset2.add(strnorms_copy)
#                 newset2.add( strnorms + strtokenlist.norms[start+i][0])
#             newset.update(newset2)
#         StrNorms.append(newset)
#     return StrNorms


#FailedRules: gets set according to RuleIdenticalNetwork. gets reset when apply rule.
def MatchAndApplyRuleFile(strtokenlist, RuleFileName):
    WinningRules = {}
    i = 0
    #logging.debug("Matching using file:" + RuleFileName)
    counter = 0

    strtoken = strtokenlist.head

    while strtoken:
        # strsignatures = strtokenlist.signature(i, min([RuleSizeLimit, strtokenlist.size-i]))

        #logging.debug("Checking tokens start from:" + strtoken.text)
        WinningRule = None
        rulegroup = Rules.RuleGroupDict[RuleFileName]
        #WinningRuleSize = 0
        #StrNorms = ConstructNorms(strtokenlist, i)
        # MaxGramSize = 10

        for rule in rulegroup.RuleList:
            if rule.StrTokenLength > strtokenlist.size-i:
                continue
            # if MaxGramSize > rule.StrTokenLength:
            #     for strnorms in StrNorms[rule.StrTokenLength-1]:
            #         if strnorms in rulegroup.NormHash:
            #             WinningRule = rulegroup.NormHash[strnorms]
            #             break
            # if WinningRule:
            #     break

            if rule.norms and not ListMatch(strtokenlist.norms[i:i+rule.StrTokenLength], rule.norms):
                continue
            counter += 1
            #logging.info("    HeadMatch for rule " + str(rule.ID) + " length:" + str(rule.TokenLength) + " |" + rule.Origin )
            result = HeadMatch(strtokenlist, i, rule)
            if result:
                WinningRule = rule
                break   #Because the file is sorted by rule length, so we are satisfied with the first winning rule.
        if WinningRule:
            if logging.root.isEnabledFor(logging.DEBUG):
                logging.debug("Found winning rule at counter: {}. The winning rule is: {}".format(counter, WinningRule) )
            try:
                if WinningRule.ID not in WinningRules:
                    WinningRules[WinningRule.ID] = '<li> [{}] {} <li class="indent"> {}'.format( WinningRule.FileName, WinningRule.Origin, MarkWinningTokens(strtokenlist, WinningRule, i))
                else:
                    WinningRules[WinningRule.ID] += ' <li class="indent"> {}'.format( MarkWinningTokens(strtokenlist, WinningRule, i))
                ApplyWinningRule(strtokenlist, WinningRule, StartPosition=i)
            except RuntimeError as e:
                if e.args and e.args[0] == "Rule error in ApplyWinningRule.":
                    logging.error("The rule is so wrong that it has to be removed from rulegroup " + RuleFileName)
                    rulegroup.RuleList.remove(WinningRule)
                else:
                    logging.error("Unknown Rule Applying Error when applying{}:\n {}".format(WinningRule.RuleName, e))
                    logging.info("strtokenlist={}".format(strtokenlist))
                    #raise  #ignore this rule, do the next.

            except IndexError as e:
                logging.error("Failed to apply this rule:")
                logging.error(str(WinningRule))
                logging.error(str(e))
                #raise
        i += 1
        strtoken = strtoken.next

    strtokenlist.ClearHITFeatures()
    return WinningRules


def DAGMatch(Dag, Rule, level, OpenNodeID = None):
    #logging.debug("DAGMatch: level {}, OpenNodeID {}".format( level, OpenNodeID))
    if level >= len(Rule.Tokens):
        # now the rule tokens are all matched!
        routeSignature = GetRouteSignature(Rule)
        #logging.info("RouteSignature:{}".format(RouteSignature))
        if not hasattr(DAGMatch, "DagSuccessRoutes"):
            DAGMatch.DagSuccessRoutes = set()       #initialize.

        for route in DAGMatch.DagSuccessRoutes:
            if routeSignature.RuleFileName == route.RuleFileName and \
                    len(routeSignature.Route) < len(route.Route) and \
                    routeSignature.Route.issubset(route.Route):
                return None #a longer route is already matched and applied.
            if routeSignature.RuleID == route.RuleID and \
                    routeSignature.Route == route.Route:
                return None #a longer route is already matched and applied.

        DAGMatch.DagSuccessRoutes.add(routeSignature)
        if logging.root.isEnabledFor(logging.DEBUG):
            logging.debug("Dag.DAGMatch(): Matched all tokens.")
        return Dag.nodes[OpenNodeID]

    if level < 0:
        #Dag.ClearVisited()
        return None

    ruletoken = Rule.Tokens[level]
    for nodeID in Dag.nodes:
        if  Dag.nodes[nodeID].visited:
            continue
        if level == 0:     #when the OpneNode is None, level should be 0
            OpenNodeID = nodeID

        if Dag.TokenMatch(nodeID, ruletoken, OpenNodeID, Rule):
            Dag.nodes[nodeID].visited = True
            ruletoken.MatchedNodeID = nodeID
            Dag.nodes[nodeID].TempPointer = ruletoken.pointer
            if ruletoken.pointer:
                logging.debug("DAGMatch: setting this node {} to TempPointer: {}".format(nodeID, ruletoken.pointer))
            successnode = DAGMatch(Dag, Rule, level+1, OpenNodeID)
            if successnode:
                return successnode
            else:
                Dag.nodes[nodeID].visited = False
                ruletoken.MatchedNodeID = None
                Dag.nodes[nodeID].TempPointer = ''
    return None
    #return DAGMatch(Dag, Rule, level-1, OpenNodeID)


class RouteSignature(object):
    RuleFileName = ""
    RuleID = -1
    Route = None

    def __init__(self, RuleFileName, RuleID, Route):
        self.RuleFileName = RuleFileName
        self.RuleID = RuleID
        self.Route = Route

    def __str__(self):
        return "RuleID:{}\tRoute:{}".format(self.RuleID, self.Route)


def GetRouteSignature(rule):
    RouteSet = frozenset([token.MatchedNodeID for token in rule.Tokens if token.MatchedNodeID is not None])
    return RouteSignature(rule.FileName, rule.ID, RouteSet)


def MatchAndApplyDagRuleFile(Dag, RuleFileName):
    WinningRules = {}
    rulegroup = Rules.RuleGroupDict[RuleFileName]

    rule_sequence = 0
    counter = 0
    RuleLength = len(rulegroup.RuleList)
    AppliedPriority = 2
    while rule_sequence < RuleLength:
        counter += 1
        if counter > 10 * RuleLength:
            break
        rule = rulegroup.RuleList[rule_sequence]
        ##Priority:default is 0. (Top) is 1. (Bottom) is -1.
        if AppliedPriority in (0, 1) and rule.Priority < AppliedPriority:
            break   #stop running if a higher priority rule is applied. Sept 9, 2018.

        if 0 < rule.LengthLimit < len(Dag.nodes):
            rule_sequence += 1
            logging.debug("This sentence is too long to try this rule:{}".format(rule.Origin))
            continue
        #
        # # if logging.root.isEnabledFor(logging.DEBUG):
        # #     logging.debug("DAG: Start checking rule {}".format( rule))
        node = DAGMatch(Dag,  rule, 0)
        if node:
            if rule.WindowLimit == 0 or rule.WindowLimit >= Dag.MaxDistanceOfMatchNodes( rule):
                AppliedPriority = rule.Priority
                if logging.root.isEnabledFor(logging.DEBUG):
                    logging.debug("DAG: Winning rule! {}".format(rule))
                try:
                        if rule.ID not in WinningRules:
                            WinningRules[rule.ID] = '<li> [{}] {} <li class="indent"> {} </li>'.format(rule.FileName, rule.Origin, node.text)
                        else:
                            WinningRules[rule.ID] += ' <li class="indent"> {} </li>'.format( node.text)
                        ApplyWinningDagRule(Dag, rule, node)
                        rule_sequence -= 1  # allow the same rule to match other nodes too.
                except RuntimeError as e:
                    if e.args and e.args[0] == "Rule error in ApplyWinningRule.":
                        logging.error("The rule is so wrong that it has to be removed from rulegroup " + RuleFileName)
                        rulegroup.RuleList.remove(rule)
                    else:
                        logging.error("Unknown Rule Applying Error:" + str(e))

                except IndexError as e:
                    logging.error("Failed to apply this rule:")
                    logging.info(str(rule))
                    logging.error(str(e))
                #search the rest of rules using other nodes

        Dag.ClearVisited()
        for node_id in Dag.nodes:
            # if logging.root.isEnabledFor(logging.INFO):
            #     logging.info("node: {}".format(node))
            Dag.nodes[node_id].TempPointer = ''   #remove TempPointer from failed rules.

        rule_sequence += 1

    Dag.ClearHITFeatures()
    return WinningRules


def DynamicPipeline(NodeList, schema):
    WinningRules = {}
    Dag = DependencyTree.DependencyTree()


    for action in PipeLine:
        if action == "segmentation":
            continue
        if action == "apply lexicons":
            continue

        if action == "SEGMENTATION COMPLETE" and schema == "segonly":
            break
        if action == "SHALLOW COMPLETE" and schema == "shallowcomplete":
            break

        #applies caseab, caseAb, caseaB, or caseAB
        if action == "CASES":
            Lexicon.ApplyCasesToNodes(NodeList)

        if action.startswith("FSA "):
            Rulefile = action[3:].strip()
            WinningRules.update(MatchAndApplyRuleFile(NodeList, Rulefile))
            # if NodeList:
            #     logging.debug(NodeList.root(True).CleanOutput(KeepOriginFeature=True).toJSON())

        # if action.startswith("lookup"):
        #     lookupSourceName = action[6:].strip()
        #     for x in LexiconLookupSource:
        #         if x.name == lookupSourceName:
        #             Lexicon.LexiconLookup(NodeList, x)
        #
        # if action == "APPLY COMPOSITE KG":
        #     Lexicon.ApplyCompositeKG(NodeList)

        if action.startswith("Lookup defLex:") or action.startswith("Lookup External:") \
                or action.startswith("Lookup oQcQ") or action.startswith("Lookup Compound:"):
            lookupSourceName = action[6:action.index(":")].strip()
            for x in LexiconLookupSource:
                if x.name == lookupSourceName:
                    Lexicon.LexiconLookup(NodeList, x)

        if action.startswith("Lookup IE"):
            Lexicon.ApplyCompositeKG(NodeList)
        #
        # if action == "TRANSFORM DAG":
        #     Dag.transform(NodeList)
        #     logging.info("Dag:{}".format(Dag))

        if action.startswith("DAGFSA "):
            if len(Dag.nodes) == 0:
                try:
                    Dag.transform(NodeList)
                except Exception as e:
                    logging.error("Failed to transfer the NodeList to Dag due to:\n{}".format(e))
                    return NodeList, Dag, WinningRules
            Rulefile = action[7:].strip()
            WinningRules.update(MatchAndApplyDagRuleFile(Dag, Rulefile))

        if action.startswith("DAGFSA_APP "):
            if len(Dag.nodes) == 0:
                try:
                    Dag.transform(NodeList)
                except Exception as e:
                    logging.error("Failed to transfer the NodeList to Dag due to:\n{}".format(e))
                    return NodeList, Dag, WinningRules
            Rulefile = action[10:].strip()
            WinningRules.update(MatchAndApplyDagRuleFile(Dag, Rulefile))

    return NodeList, Dag, WinningRules


def PrepareJSandJM(nodes):
    nodes.head.ApplyFeature(utils.FeatureID_JS2)
    JSnode = Tokenization.SentenceNode('')
    JSnode.ApplyFeature(utils.FeatureID_JS)
    JSnode.ApplyFeature(utils.FeatureID_JS2)
    nodes.insert(JSnode, 0)
    p = nodes.head.next
    while p.next:
        if utils.FeatureID_SYM not in p.features:
            p.ApplyFeature(utils.FeatureID_JS2)
            break
        p.ApplyFeature(utils.FeatureID_JS2)
        p = p.next

    PUNCSet = {".", "?", "!", ";", "...", ":", "。"}
    if utils.FeatureID_SYM not in nodes.tail.features and \
            nodes.tail.text not in PUNCSet  :
        JMnode = Tokenization.SentenceNode('')
        JMnode.StartOffset = nodes.tail.EndOffset
        JMnode.EndOffset = nodes.tail.EndOffset
        JMnode.ApplyFeature(utils.FeatureID_punc)
        nodes.append(JMnode)
    nodes.tail.ApplyFeature(utils.FeatureID_JM)
    nodes.tail.ApplyFeature(utils.FeatureID_JM2)
    p = nodes.tail.prev
    while p.prev:
        if utils.FeatureID_SYM not in p.features:
            # first one that is not punc. the real JM2:
            p.ApplyFeature(utils.FeatureID_JM2)
            break
        p.ApplyFeature(utils.FeatureID_JM2)
        p = p.prev


def SeparateSentence(Sentence):
    PUNCSet = {"?", "!", ";", "...", ",", "。", "？", "！", "；", "，", "\t"}
    punclist = []
    i_prev = 0
    for i in range(len(Sentence)):
        if Sentence[i] in PUNCSet and (i_prev+5) < i < (len(Sentence) - 5):
            punclist.append(i)
            i_prev = i

    start = 0
    SubSentences = []
    for separator in punclist:
        SubSentences.append( Sentence[start:separator+1])
        start = separator+1
    if start < len(Sentence):
        SubSentences.append(Sentence[start:])

    #logging.info(str(SubSentences))
    return SubSentences

def LexicalAnalyzeTask( SubSentence, schema):

    NodeList = Tokenization.Tokenize(SubSentence)
    if not NodeList or NodeList.size == 0:
        return None, None

    Lexicon.ApplyLexiconToNodes(NodeList)
    # print("after ApplyLexiconToNodes" + OutputStringTokens_oneliner(NodeList))

    PrepareJSandJM(NodeList)
    #Lexicon.LexiconoQoCLookup(NodeList)

    NodeList, Dag, WinningRules = DynamicPipeline(NodeList, schema)
        # t = Thread(target=Cache.WriteSentenceDB, args=(SubSentence, NodeList))
        # t.start()

    return NodeList, Dag, WinningRules


"""After testing, the _multithread version is not faster than normal one.
abandened. """
def LexicalAnalyze_multithread(Sentence, schema = "full"):
    try:
        if logging.root.isEnabledFor(logging.DEBUG):
            logging.debug("-Start LexicalAnalyze: tokenize")

        Sentence = invalidchar_pattern.sub(u'\uFFFD', Sentence)

        ResultNodeList = None
        ResultWinningRules = {}
        SubSentences = SeparateSentence(Sentence)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            Result = {}

            future_to_subsentence = {executor.submit(LexicalAnalyzeTask, SubSentence, schema): SubSentence for SubSentence in SubSentences}
            for future in concurrent.futures.as_completed(future_to_subsentence):
                (NodeList, WinningRules) = future.result()
                Result[future_to_subsentence[future]] = NodeList
                ResultWinningRules.update(WinningRules)
        #logging.warning("submitted into " + str(len(Result)) + " threads to process.")
        for SubSentence in SubSentences:
            NodeList = Result[SubSentence]
            # logging.info("before adding " + SubSentence + ", the nodelist is: " + str(ResultNodeList))
            # logging.info("\t the new nodes are: " + str(NodeList))
            if ResultNodeList:
                if not ResultNodeList.tail.text:
                    ResultNodeList.remove(ResultNodeList.tail)

                NodeList.remove(NodeList.head)
                ResultNodeList.appendnodelist(NodeList)
            else:
                ResultNodeList = NodeList
        logging.debug("-End LexicalAnalyze")

    except Exception as e:
        logging.error("Overall Error in LexicalAnalyze:")
        logging.error(e)
        logging.error(traceback.format_exc())
        return None, None

    return ResultNodeList, ResultWinningRules

def LexicalAnalyze(Sentence, schema = "full"):
    try:
        logging.debug("-Start LexicalAnalyze: tokenize")

        Sentence = invalidchar_pattern.sub(u'\uFFFD', Sentence)
        if Sentence in Cache.SentenceCache:
            Dag = DependencyTree.DependencyTree()
            Dag.transform(Cache.SentenceCache[Sentence])
            #return Cache.SentenceCache[Sentence], Dag, None  # assume ResultWinningRules is none.

        ResultNodeList, Dag, ResultWinningRules = LexicalAnalyzeTask(Sentence, schema)

        if schema == "full" and utils.runtype != "debug" and utils.DisableDB is False:
            if len(Cache.SentenceCache) < utils.maxcachesize:
                Cache.SentenceCache[Sentence] = ResultNodeList
                Cache.WriteSentenceDB(Sentence, ResultNodeList)
        # if ParserConfig.get("main", "runtype").lower() == "debug":
        #     t = Thread(target=Cache.WriteWinningRules_Async, args=(Sentence, ResultWinningRules))
        #     t.start()
            #Cache.WriteWinningRules(Sentence, ResultWinningRules)
        logging.debug("-End LexicalAnalyze")

    except Exception as e:
        logging.error("Overall Error in LexicalAnalyze({}) :".format(Sentence))
        logging.error(e)
        logging.error(traceback.format_exc())
        return None, None, None

    return ResultNodeList, Dag, ResultWinningRules


def LoadPipeline(PipelineLocation):
    if PipelineLocation.startswith("."):
        PipelineLocation = os.path.join(os.path.dirname(os.path.realpath(__file__)),  PipelineLocation)
    with open(PipelineLocation, encoding="utf-8") as dictionary:
        for line in dictionary:
            action, _ = SeparateComment(line)
            if not action:
                continue
            PipeLine.append(action.strip())

def SystemFileOlderThanDB(XLocation):
    if utils.DisableDB:
        return False
    Systemfilelist = ["../Y/feature.txt","../Y/GlobalMacro.txt"]

    for file in Systemfilelist:
        fileLocation = os.path.join(XLocation,file)
        cur = utils.DBCon.cursor()
        strsql = "select ID, modifytime from systemfiles where filelocation=?"
        cur.execute(strsql, [file, ])
        resultrecord =  cur.fetchone()
        cur.close()

        if not resultrecord or not resultrecord[1]:
            return False


        FileDBTime = resultrecord[1]  # utc time.
        FileDiskTime = datetime.utcfromtimestamp(os.path.getmtime(fileLocation)).strftime('%Y-%m-%d %H:%M:%S')

        if FileDiskTime > FileDBTime:
            return False

    return True


def UpdateSystemFileFromDB(XLocation):
    if utils.DisableDB:
        return

    Systemfilelist = ["../Y/feature.txt", "../Y/GlobalMacro.txt"]
    for file in Systemfilelist:
        fileLocation = os.path.join(XLocation, file)
        cur = utils.DBCon.cursor()
        strsql = "select ID, modifytime from systemfiles where filelocation=?"
        cur.execute(strsql, [file, ])
        resultrecord = cur.fetchone()
        FileDiskTime = datetime.utcfromtimestamp(os.path.getmtime(fileLocation)).strftime('%Y-%m-%d %H:%M:%S')
        if resultrecord:
            strsql = "update systemfiles set modifytime=? where filelocation=?"
            cur.execute(strsql, [FileDiskTime, file])

        else:
            strsql = "INSERT into systemfiles (filelocation, modifytime) VALUES(?, ?)"
            cur.execute(strsql, [file, FileDiskTime])

        cur.close()

def LoadCommon():
    if not utils.DisableDB:
        InitDB()

        import Cache
        Cache.LoadSentenceDB()

    PipeLineLocation = ParserConfig.get("main", "Pipelinefile")
    FILE_ABS_PATH = os.path.dirname(os.path.abspath(__file__))
    XLocation = FILE_ABS_PATH  + '/' + os.path.dirname(PipeLineLocation) + "/"
    #XLocation = os.path.dirname(PipeLineLocation) + "/"

    FeaturefileLocation = os.path.join(XLocation, "../Y/feature.txt")
    GlobalmacroLocation = os.path.join(XLocation, "../Y/GlobalMacro.txt")
    # PunctuatefileLocation = os.path.join(XLocation, "../Y/LexY-EnglishPunctuate.txt")


    FeatureOntology.LoadFeatureOntology(FeaturefileLocation)
    systemfileolderthanDB = SystemFileOlderThanDB(XLocation)

    LoadPipeline(PipeLineLocation)

    if logging.root.isEnabledFor(logging.DEBUG):
        logging.debug("Runtype:" + ParserConfig.get("main", "runtype"))
    if logging.root.isEnabledFor(logging.DEBUG):
        logging.debug("utils.Runtype:" + utils.ParserConfig.get("main", "runtype"))

    Rules.LoadGlobalMacro(GlobalmacroLocation)


    # Lexicon.LoadLexicon(PunctuatefileLocation)

    for action in PipeLine:
        if action.startswith("FSA "):
            Rulefile = action[3:].strip()
            Rules.LoadRules(XLocation, Rulefile,systemfileolderthanDB)

        if action.startswith("DAGFSA "):
            Rulefile = action[6:].strip()
            Rules.LoadRules(XLocation, Rulefile,systemfileolderthanDB)

        if action.startswith("DAGFSA_APP "): #FUZZY
            Rulefile = action[10:].strip()
            Rules.LoadRules(XLocation, Rulefile,systemfileolderthanDB, fuzzy=True)

        if action.startswith("Lookup Spelling:"):
            Spellfile = action[action.index(":")+1:].strip().split(",")
            for spell in Spellfile:
                spell = spell.strip()
                if spell:
                    Lexicon.LoadExtraReference(XLocation + spell, Lexicon._LexiconCuobieziDict)

        if action.startswith("Lookup Encoding:"):
            Encodefile = action[action.index(":")+1:].strip().split(",")
            for encode in Encodefile:
                encode = encode.strip()
                if encode:
                    Lexicon.LoadExtraReference(XLocation + encode, Lexicon._LexiconFantiDict)

        if action.startswith("Lookup Main:"):
            Mainfile = action[action.index(":")+1:].strip().split(",")
            for main in Mainfile:
                main = main.strip()
                if main:
                    Lexicon.LoadMainLexicon(XLocation + main)

        if action.startswith("Lookup SegmentSlash:"):
            Slashfile = action[action.index(":")+1:].strip().split(",")
            for slash in Slashfile:
                slash = slash.strip()
                if slash:
                    Lexicon.LoadSegmentSlash(XLocation + slash)

        if action.startswith("Lookup Lex:"):
            Lexfile = action[action.index(":")+1:].strip().split(",")
            for lex in Lexfile:
                lex = lex.strip()
                if lex:
                    Lexicon.LoadLexicon(XLocation + lex)

        # (O.O)
        if action.startswith("Stemming:"):
            Stemfile = action[action.index(":") + 1:].strip().split(",")
            inf = Stemfile[0].strip()
            Rules.LoadRules(XLocation, inf, systemfileolderthanDB)
            Lexicon.LoadSuffix(XLocation + inf, inf)
            for stem in Stemfile[1:]:
                stem = stem.strip()
                if stem:
                    Lexicon.LoadLexicon(XLocation + stem, lookupSource=LexiconLookupSource.stemming)

        if action.startswith("Lookup Compound:"):
            Compoundfile = action[action.index(":")+1:].strip().split(",")
            for compound in Compoundfile:
                compound = compound.strip()
                if compound:
                    Lexicon.LoadLexicon(XLocation + compound, lookupSource=LexiconLookupSource.Compound)

        if action.startswith("Lookup defLex:"):
            Compoundfile = action[action.index(":")+1:].strip().split(",")
            for compound in Compoundfile:
                compound = compound.strip()
                if compound:
                    Lexicon.LoadLexicon(XLocation + compound, lookupSource=LexiconLookupSource.defLex)

        if action.startswith("Lookup External:"):
            Externalfile = action[action.index(":")+1:].strip().split(",")
            for external in Externalfile:
                external = external.strip()
                if external:
                    Lexicon.LoadLexicon(XLocation + external,lookupSource=LexiconLookupSource.External)

        if action.startswith("Lookup oQcQ:"):
            oQoCfile = action[action.index(":")+1:].strip().split(",")
            for oQoC in oQoCfile:
                oQoC = oQoC.strip()
                if oQoC:
                    Lexicon.LoadLexicon(XLocation + oQoC,lookupSource=LexiconLookupSource.oQcQ)

        if action.startswith("Lookup IE:"):
            compositefile = action[action.index(":")+1:].strip().split(",")
            for composite in compositefile:
                comp = composite.strip()
                if comp:
                    Lexicon.LoadCompositeKG(XLocation + comp)

    Lexicon.LoadSegmentLexicon()
    UpdateSystemFileFromDB(XLocation)

    if not utils.DisableDB:
        CloseDB(utils.DBCon)
    if ParserConfig.get("main", "runtype") == "Debug":
        logging.debug("Start writing temporary rule files")
        Rules.OutputRuleFiles(ParserConfig.get("main", "compiledfolder"))
        FeatureOntology.OutputFeatureOntologyFile(ParserConfig.get("main", "compiledfolder"))
        logging.debug("Start writing temporary lex file.")
        #Lexicon.OutputLexiconFile(ParserConfig.get("main", "compiledfolder"))


    #Rules._PreProcess_RuleIDNormalize()
    logging.debug("Done of LoadCommon!")

        #print(Lexicon.OutputLexicon(False))

if __name__ == "__main__":
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s [%(levelname)s] %(message)s')
    LoadCommon()

    #target = "卡雷尼奥.杜兰（Carrenoduran） 淡水珍珠项链近正圆强光微暇女送妈妈8-9mm47cm XL06122"

    # import cProfile, pstats
    # cProfile.run("LexicalAnalyze(target)", 'restatslex')
    # pstat = pstats.Stats('restatslex')
    # pstat.sort_stats('time').print_stats(10)



    # m_nodes, winningrules = LexicalAnalyze(target)
    # if not m_nodes:
    #     logging.warning("The result is None!")
    #     exit(1)
    #
    # logging.info("\tDone! counterMatch=%s" % counterMatch)
    #
    # print(OutputStringTokens_oneliner(m_nodes, NoFeature=True))
    # print(OutputStringTokens_oneliner(m_nodes))
    #
    #
    # print("Winning rules:\n" + OutputWinningRules())
    #
    # print(FeatureOntology.OutputMissingFeatureSet())
    #
    # print(m_nodes.root().CleanOutput().toJSON())
    # print(m_nodes.root().CleanOutput_FeatureLeave().toJSON())
    # print(m_nodes.root(True).CleanOutput(KeepOriginFeature=True).toJSON())

    print_var(globals(), "0.log")
    nodelist, dag, winningrules = LexicalAnalyze("千呼万唤不出来")
    print("dag: {}".format(dag))
    print("winning rules: {}".format(winningrules))

    # print_var(globals(), "1.log")
    # for x in range(1000):
    #     nodelist, dag, winningrules = LexicalAnalyze("2千呼万唤不出来")
    #     print("dag: {}".format(dag))
    #     print("winning rules: {}".format(winningrules))

    print_var(globals(), "2.log")
    nodelist, dag, winningrules = LexicalAnalyze("3千呼万唤不出来")
    print("dag: {}".format(dag))
    print("winning rules: {}".format(winningrules))
    print_var(globals(), "3.log")

    # nodelist, dag, winningrules = LexicalAnalyze("千呼万唤不出来")
    # print("dag: {}".format(dag))
    # print("winning rules: {}".format(winningrules))

    #LexicalAnalyze("张三做好事所有人都觉得是沽名钓誉")
