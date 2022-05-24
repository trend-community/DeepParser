# coding=utf-8
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
import pickle
counterMatch = 0

#WinningRuleDict = {}
invalidchar_pattern = re.compile(u'[^\u0000-\uD7FF\uE000-\uFFFF]', re.UNICODE)
PipeLine = []
XLocation = ""



def MarkWinningTokens(strtokens, rule, StartPosition):
    result = ""

    p = strtokens.head
    counter = 0
    StopPosition = StartPosition+rule.StrTokenLength - 1
    while p:
        if counter == StartPosition:
            result += "<em>"
        result += p.text
        if counter == StopPosition:
            result += "</em>"
        if LanguageType == 'western':
        #if strtokens.isPureAscii:
            result += " "
        p = p.next
        counter += 1

    return result.strip()

def MarkDAGWinningTokens(dag):
    result = ""

    for node in sorted(dag.nodes.values(), key=operator.attrgetter("StartOffset") ):
        if node.visited:
            result += "<em>{}</em>".format(node.text)
        else:
            result += node.text
        if LanguageType == 'western':
            result += " "

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

    for k in rule.GlobalVariablesNegation:  #negation
        if k in utils.GlobalVariables and rule.GlobalVariablesNegation[k] == utils.GlobalVariables[k]:
            return False

    for k in rule.GlobalVariables:
        if k not in utils.GlobalVariables or rule.GlobalVariables[k] != utils.GlobalVariables[k]:
            return False

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
            logging.error("  For Tokens {} \n  i={}, StartPosition={}".format(str(strTokenList), i, StartPosition))
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
            token.ApplyActions(rule.Tokens[i].action, strtokens)

    if rule.Chunks:
        MaxChunkLevelNum = max(chunk.ChunkLevel for chunk in rule.Chunks)
        for ChunkLevel in range(1,MaxChunkLevelNum+1):
            for chunk in rule.Chunks:   # the chunks are presorted to process right chucks first.
                if chunk.ChunkLevel != ChunkLevel:
                    continue
                newnode = strtokens.combine(StartPosition+chunk.StartOffset, chunk.StringChunkLength, chunk.HeadOffset)
                newnode.ApplyActions(chunk.Action, strtokens)
                newnode.ApplyDefaultUpperRelationship()

    #strtokens._setnorms()

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
            Dag.ApplyDagActions(OpenNode, node, rule.Tokens[i].action, rule, i)

    for nodeid in Dag.nodes:
        #logging.info("node: {}".format(nodeid))
        Dag.nodes[nodeid].TempPointer = ''  # remove TempPointer after applying action.

    return 0
#
# #list1 is combination of norm and Head0Text.
# # either of them equals to the item in list2, that means match.
# #from functools import lru_cache
# #@lru_cache(maxsize=100000)
# def ListMatch(list1, list2):
#     # if len(list1) != 2 or  len(list1[0]) != len(list2):
#     #     logging.error("Coding error. The size should be the same in ListMatch")
#     #     return False
#     # for i in range(num):
#     #     if list2[i] == '' or \
#     #         list1[i][0] == list2[i] or \
#     #             list1[i][1] and list1[i][1] == list2[i]:
#     #         pass
#     #     else:
#     #         return False
#
#     i = -1
#     for l2item in list2:
#         i += 1
#         if l2item == '' or \
#             list1[i][0] == l2item or \
#             list1[i][1] and list1[i][1] == l2item:
#             pass
#         else:
#             return False
#     return True

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

            if 0 < rule.LengthLimit < (strtokenlist.tail.EndIndex-strtokenlist.head.StartIndex):
                #logging.debug("This sentence is too long to try this rule:{}".format(rule.Origin))
                continue

            if rule.WindowLimit > 0:
                StartIndex = strtokenlist.get(i).StartIndex
                EndIndex = strtokenlist.get(i+rule.StrTokenLength-1).EndIndex
                if rule.WindowLimit <= (EndIndex - StartIndex):
                    logging.debug("The window for the tokens are larger than windowlimit")
                    continue

            # if rule.norms and not ListMatch(strtokenlist.norms[i:i+rule.StrTokenLength], rule.norms):
            #     continue
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

            # by default the RestartPosition is 1. Move to next.
            for _x in range(WinningRule.RestartPosition):
                strtoken = strtoken.next
            i += WinningRule.RestartPosition
        else:   # no winning rule. Move to next
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
    for nodeID in sorted(Dag.nodes, key=lambda nodeid:Dag.nodes[nodeid].StartIndex,  reverse=Rule.RightFirst):    # reversed = True if the rule is required to be "right first"
        if  Dag.nodes[nodeID].visited:
            continue
        if  FeatureID_GONE in Dag.nodes[nodeID].features:     # ignore GONE node
            continue
        if level == 0:     #when the OpneNode is None, level should be 0
            OpenNodeID = nodeID

        # if 0 < Rule.WindowLimit and  Rule.WindowLimit < Dag.MaxDistanceToMatchedNodes(Rule, nodeID) :
        #     continue    # this node is outside the window limit, skip.

        if Dag.TokenMatch(nodeID, ruletoken, OpenNodeID, Rule, level):
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
        rule = rulegroup.RuleList[rule_sequence]

        if counter > 10 * RuleLength:
            logging.warning(f"The rules in {RuleFileName} are tricky, and I have tried {counter} times, more than 10*{RuleLength} and keep looping. time to break.")
            logging.warning(f"This rule is paused: {rule}")
            rule_sequence += 1
            counter = 0
            continue

        # ##Priority:default is 0. (Top) is 1. (Bottom) is -1.
        # if AppliedPriority in (0, 1) and rule.Priority < AppliedPriority:
        #     break   #stop running if a higher priority rule is applied. Sept 9, 2018.
        # Disable this on Dec 16, 2020

        if 0 < rule.LengthLimit < len(Dag.nodes):
            rule_sequence += 1
            logging.debug("This sentence is too long to try this rule:{}".format(rule.Origin))
            continue

        FailInGlobalVariablesNegation = False
        for k in rule.GlobalVariablesNegation:  # negation
            if k in utils.GlobalVariables and rule.GlobalVariablesNegation[k] == utils.GlobalVariables[k]:
                FailInGlobalVariablesNegation = True
                break
        if FailInGlobalVariablesNegation:
            rule_sequence += 1
            continue  # next rule

        FailInGlobalVariables = False
        logging.debug(f"MatchAndApplyDagRuleFile: For rule {rule}, Rule condistion is: {rule.GlobalVariables}. Current GlobalVariables={utils.GlobalVariables}")
        for k in rule.GlobalVariables:
            if k not in utils.GlobalVariables or rule.GlobalVariables[k] != utils.GlobalVariables[k]:
                FailInGlobalVariables = True
                break
        if FailInGlobalVariables:
            rule_sequence += 1
            continue  # next rule

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
                        WinningRules[rule.ID] = '<li> [{}] {} <li class="indent"> {}'.format(
                            rule.FileName, rule.Origin, MarkDAGWinningTokens(Dag))
                    else:
                        WinningRules[rule.ID] += ' <li class="indent"> {}'.format(
                            MarkDAGWinningTokens(Dag))

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
            else:
                logging.info("Window size limit applied for {} while the max distance is {}".format(rule, Dag.MaxDistanceOfMatchNodes( rule)))
                rule_sequence -= 1  # allow the same rule to match other nodes too.

        Dag.ClearVisited()
        for node_id in Dag.nodes:
            # if logging.root.isEnabledFor(logging.INFO):
            #     logging.info("node: {}".format(node))
            Dag.nodes[node_id].TempPointer = ''   #remove TempPointer from failed rules.

        rule_sequence += 1

    Dag.ClearHITFeatures()
    return WinningRules


def RemoveDoneAndDone2(nodes):
    p = nodes.head.next
    while p.next:
        if FeatureID_Done in p.features:
            p.features.remove(FeatureID_Done)
        if FeatureID_Done2 in p.features:
            p.features.remove(FeatureID_Done2)

        p = p.next


def DynamicPipeline(NodeList, schema):
    WinningRules = {}
    Dag = DependencyTree.DependencyTree()

    # PipeLineLocation = ParserConfig.get("main", "Pipelinefile")
    # # XLocation = os.path.dirname(PipeLineLocation)     # need to get relative location, not the absolute location.
    # XLocation, _ = os.path.split(PipeLineLocation)
    # XLocation += "/"
    # if XLocation.startswith("."):
    #     XLocation = os.path.join(os.path.dirname(__file__), XLocation)

    LookupSourceExecuted = set()    # each source can only executed once.
    for action in PipeLine:
        action_upper = action.upper()
        if action_upper == "SEGMENTATION":
            continue

        if action_upper == "SEGMENTATION COMPLETE" and schema == "segonly":
            break
        if action_upper == "SHALLOW COMPLETE" and schema == "shallowcomplete":
            break

        #applies caseab, caseAb, caseaB, or caseAB
        if action_upper == "CASES":
            Lexicon.ApplyCaseFeatureToNodes(NodeList)

        if action_upper.startswith("FSA "):
            Rulefile = action[3:].strip()
            RuleLocation = os.path.join(XLocation, Rulefile)
            try:
                WinningRules.update(MatchAndApplyRuleFile(NodeList, RuleLocation))
            except KeyError as e:
                # assume in the middle of Rules.Loadfile, this function is called to segment for fuzzy word
                logging.info("KeyError in ProcessSentence:" + str(e))
                break   # stop the rest of the DynamicPipeline. Go directly to return.
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

        # Note: The lexicons in  "Lookup Lex" and "Lookup Customer" are being used in
        # _Tokenize_Lexicon_maxweight() and ApplyFeature().
        if action_upper.startswith("LOOKUP DEFLEX:") or action_upper.startswith("LOOKUP EXTERNAL:") \
                or action_upper.startswith("LOOKUP COMPOUND:") or action_upper.startswith("LOOKUP STEMCOMPOUND:"):
            lookupSourceName = action_upper[6:action_upper.index(":")].strip()
            if utils.LanguageType == "western" and lookupSourceName in ["COMPOUND", "DEFLEX"] :
                #these two are done in Tokenize_CnEnMix(). no need to do it again
                continue

            if lookupSourceName not in LookupSourceExecuted:
                LookupSourceExecuted.add(lookupSourceName)
                for x in LexiconLookupSource:
                    if x.name == lookupSourceName:
                        Lexicon.LexiconLookup(NodeList, x)
                        if x.name == "COMPOUND":
                            Lexicon.LexiconLookup(NodeList, LexiconLookupSource.COMPOUND_SENSITIVE) #extra

        if action.startswith("DAGFSA "):
            if len(Dag.nodes) == 0:
                try:
                    Dag.transform(NodeList)
                except Exception as e:
                    logging.error("Failed to transfer the NodeList to Dag due to:\n{}".format(e))
                    return NodeList, Dag, WinningRules
            Rulefile = action[7:].strip()
            RuleLocation = os.path.join(XLocation, Rulefile)
            try:
                WinningRules.update(MatchAndApplyDagRuleFile(Dag, RuleLocation))
            except KeyError as e:
                # assume in the middle of Rules.Loadfile, this function is called to segment for fuzzy word
                logging.info("KeyError in ProcessSentence. Expected:" + str(e))
                break   # stop the rest of the DynamicPipeline. Go directly to return.

        if action.startswith("DAGFSA_APP "):
            if len(Dag.nodes) == 0:
                try:
                    Dag.transform(NodeList)
                except Exception as e:
                    logging.error("Failed to transfer the NodeList to Dag due to:\n{}".format(e))
                    return NodeList, Dag, WinningRules
            Rulefile = action[10:].strip()
            RuleLocation = os.path.join(XLocation, Rulefile)
            WinningRules.update(MatchAndApplyDagRuleFile(Dag, RuleLocation))

        # remove Done and Done2 feature for each node.
        RemoveDoneAndDone2(NodeList)

    if len(Dag.nodes) == 0 and NodeList.size > 0:
        try:
            Dag.transform(NodeList)
        except Exception as e:
            logging.error("Failed to transfer the NodeList to Dag due to:\n{}".format(e))

    return NodeList, Dag, WinningRules


def PrepareJSandJM(nodes):
    # nodes.head.ApplyFeature(utils.FeatureID_JS2)
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

    PUNCSet = {".", "?", "!", ";", "...", ":", "。","？"}
    if utils.FeatureID_SYM not in nodes.tail.features and \
            nodes.tail.text not in PUNCSet  :
        JMnode = Tokenization.SentenceNode('')
        JMnode.StartOffset = nodes.tail.EndOffset
        JMnode.EndOffset = nodes.tail.EndOffset
        JMnode.StartIndex = nodes.tail.EndIndex
        JMnode.EndIndex = nodes.tail.EndIndex
        # JMnode.ApplyFeature(utils.FeatureID_punc) # disabled this on 20201012
        nodes.append(JMnode)
    nodes.tail.ApplyFeature(utils.FeatureID_JM)
    nodes.tail.ApplyFeature(utils.FeatureID_JM2)

    # add extra JM node:  20201105
    JMnode = Tokenization.SentenceNode('')
    JMnode.StartOffset = nodes.tail.EndOffset
    JMnode.EndOffset = nodes.tail.EndOffset
    JMnode.StartIndex = nodes.tail.EndIndex
    JMnode.EndIndex = nodes.tail.EndIndex
    # JMnode.ApplyFeature(utils.FeatureID_punc) # disabled this on 20201012
    nodes.append(JMnode)
    nodes.tail.ApplyFeature(utils.FeatureID_JM)

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
        return None, None, None

    Lexicon.ApplyLexiconToNodes(NodeList)
    # print("after ApplyLexiconToNodes" + OutputStringTokens_oneliner(NodeList))

    PrepareJSandJM(NodeList)
    if utils.LanguageType == "western":
        Lexicon.LexiconLookup(NodeList, LexiconLookupSource.STEMCOMPOUND)
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


### If a sentence is longer than maxquerysentencelength, then we truncate it with the last ， before maxquerysentencelength.
# to have offset, not to have overlap sentences.
# origin version:         #Sentences = [x.strip() for x in re.split("[。\n]", Document) if x.strip()]
# if IsOCRPage is marked True in config.ini, then ignore the line break, unless the line is shorter than OcrLineLength
# TransferLinebreak: transfer, asis, rulebreak
def SplitDocument(Document, Newline = '', TransferLinebreak='transfer'):
    if utils.ParserConfig.has_option("website", "maxquerysentencelength"):
        MAXQUERYSENTENCELENGTH = int(utils.ParserConfig.get("website", "maxquerysentencelength"))
    else:
        MAXQUERYSENTENCELENGTH = 100

    if utils.ParserConfig.has_option("main", "isocrpage"):
        ISOCRPAGE = utils.ParserConfig.get("main", "isocrpage").upper()
        if ISOCRPAGE == 'TRUE':
            ISOCRPAGE = True
    else:
        ISOCRPAGE = False
    if utils.ParserConfig.has_option("main", "ocrlinelength"):
        OCRLINELENGTH = int(utils.ParserConfig.get("main", "ocrlinelength"))
    else:
        OCRLINELENGTH = 30

    if TransferLinebreak == 'transfer':

        if Newline:
            Document = Document.replace(Newline, '\n')

        # return [x.strip() for x in re.split("[。\n]", Document) if x.strip()]  #first version
        #sentences_firstcopy = [x.strip() for x in re.split("[。；\n]", Document)]
        sentences_firstcopy = utils.split_keep_multidelimiters(Document, "。；\n")

        sentences = []
        if ISOCRPAGE:
            Document = Document.replace("\r\n", "\n")
            sentences_secondcopy = []
            currentline = []
            thislinelength = 0
            _prevc = ''
            for _c in Document:
                if _c == "。" or _c == "，" or  ( _c == ' ' and _prevc in ['?', '!'] ) or \
                    ( _c == ' ' and _prevc == '.' and LanguageType == "western" ):   # Chinese and English line break
                    currentline.append(_c)
                    sentences_secondcopy.append("".join(currentline))
                    currentline = []
                elif _c == "\n":
                    if thislinelength < OCRLINELENGTH:
                        sentences_secondcopy.append("".join(currentline))
                        currentline = []
                    thislinelength = 0
                else:
                    currentline.append(_c)
                    thislinelength += 1
                _prevc = _c
            if currentline:
                sentences_secondcopy.append("".join(currentline))

            sentences_thirdcopy = [sentences_secondcopy[0]]
            for i in range(1, len(sentences_secondcopy)):
                if len(sentences_secondcopy[i-1]) < OCRLINELENGTH/2 and 0 < len(sentences_secondcopy[i]) < OCRLINELENGTH/2:
                    sentences_thirdcopy[-1] = "\n".join((sentences_thirdcopy[-1], sentences_secondcopy[i]))
                else:
                    sentences_thirdcopy.append(sentences_secondcopy[i])

            sentences_totruncate = sentences_thirdcopy
        else:
            sentences_totruncate = sentences_firstcopy

        for s in sentences_totruncate:
            while len(s) > MAXQUERYSENTENCELENGTH:
                if LanguageType == "western":
                    commasign = ","
                else:
                    commasign = "，"
                index_lastcomma = s.rfind(commasign, 0, MAXQUERYSENTENCELENGTH)
                if index_lastcomma > MAXQUERYSENTENCELENGTH/10:
                    sentences.append(s[:index_lastcomma])
                    #s = s[index_lastcomma:]
                    s = s[int(index_lastcomma*0.9):]
                else:
                    sentences.append(s[:MAXQUERYSENTENCELENGTH])
                    #s = s[MAXQUERYSENTENCELENGTH:]
                    s = s[int(MAXQUERYSENTENCELENGTH * 0.9):]
            if len(s) <= MAXQUERYSENTENCELENGTH:
                sentences.append(s)
        return sentences

    else:   # no split, remove the soft line-breaks.
        # If the TransferLinebreak == rulebreak, then replace the current break to rulebreak "\linebreak"
        # otherwise, keep the current break.
        rulebreak = "\\n"   # or maybe "\\linebreak"
        if Newline:
            Document = Document.replace(Newline, '\a')  # replaced with any control character that is impossible to have in origin text.

        if ISOCRPAGE:
            sentences_secondcopy = []
            currentline = []
            thislinelength = 0
            for _c in Document:
                if _c == "\a":
                    if thislinelength < OCRLINELENGTH:
                        sentences_secondcopy.append("".join(currentline))
                        currentline = []
                    thislinelength = 0
                else:
                    currentline.append(_c)
                    thislinelength += 1
            if currentline:
                sentences_secondcopy.append("".join(currentline))

            if TransferLinebreak == "rulebreak":
                sentence = rulebreak.join(sentences_secondcopy)
            elif TransferLinebreak == "asis":
                sentence = Newline.join(sentences_secondcopy)  #back to the origin
            else:
                logging.error("Wrong TransferLineBreak parameter: {}".format(TransferLinebreak))
                raise(RuntimeError("Wrong TransferLinkeBreak parameter"))
        else:
            if TransferLinebreak == "rulebreak":
                sentence = Document.replace('\a', rulebreak)
            elif TransferLinebreak == "asis":
                if Newline:
                    sentence = Document.replace('\a', Newline)  #back to the origin
                else:
                    sentence = Document
            else:
                logging.error("Wrong TransferLineBreak parameter: {}".format(TransferLinebreak))
                raise(RuntimeError("Wrong TransferLinkeBreak parameter"))

        return [sentence]   # make the sentence as an element of an array.


def DocumentAnalyze(Document, Schema = "full", Newline = '', TransferLinebreak='transfer'):
    dag_combined = DependencyTree.DependencyTree()
    winningrules_combined = {}

    Sentences = SplitDocument(Document, Newline, TransferLinebreak)
    logging.info("{} lines, {} characters:\n{}".format(len(Sentences), len(Document), Sentences))
    StartOffset = 0
    for sentence in Sentences:
        _, _dag, _winningrules = LexicalAnalyze(sentence, Schema)
        if _dag:
            for node in _dag.nodes.values():
                node.StartOffset += StartOffset

            dag_combined.nodes.update(_dag.nodes)
            dag_combined.graph.update(_dag.graph)
            if _winningrules:
                winningrules_combined.update(_winningrules)

        StartOffset += len(sentence) + 1

    return dag_combined, winningrules_combined


def LexicalAnalyze(Sentence, schema = "full"):
    if not hasattr(LexicalAnalyze, "MaxQuerySentenceLength"):
        if utils.LanguageType == "asian":
            LexicalAnalyze.MaxQuerySentenceLength = 200
        else:
            LexicalAnalyze.MaxQuerySentenceLength = 2000
        if utils.ParserConfig.has_option("website", "maxquerysentencelength"):
            LexicalAnalyze.MaxQuerySentenceLength = int(utils.ParserConfig.get("website", "maxquerysentencelength"))

    Dag = None
    Sentence = Sentence[:LexicalAnalyze.MaxQuerySentenceLength]
    try:
        logging.debug("-Start LexicalAnalyze: tokenize")

        Sentence = invalidchar_pattern.sub(u'\uFFFD', Sentence)
        if Sentence in Cache.SentenceCache:

            (ResultNodeList, Dag) = Cache.SentenceCache[Sentence]
            ResultWinningRules = None
            #return Cache.SentenceCache[Sentence], Dag, None  # assume ResultWinningRules is none.
        else:
            ResultNodeList, Dag, ResultWinningRules = LexicalAnalyzeTask(Sentence, schema)
            if schema == "full" and utils.runtype != "debug" :
                if len(Cache.SentenceCache) < utils.maxcachesize:
                    Cache.SentenceCache[Sentence] = (ResultNodeList, Dag)
            if utils.DisableDB is False:
                Cache.WriteSentenceDB(Sentence,  (ResultNodeList, Dag))
                Cache.WriteWinningRules_Async(Sentence, ResultWinningRules)
        # if ParserConfig.get("main", "runtype").lower() == "debug":
        #     t = Thread(target=Cache.WriteWinningRules_Async, args=(Sentence, ResultWinningRules))
        #     t.start()
        logging.debug("-End LexicalAnalyze")

    except Exception as e:
        logging.error("Overall Error in LexicalAnalyze({}) :".format(Sentence))
        logging.error(e)
        logging.error(traceback.format_exc())
        return None, None, []

    ResetGlobalVariables_Sentence(Dag)     # The global variables of "SENT_*": end of life cycle. "temp_SVO*": change to SVO
    return ResultNodeList, Dag, ResultWinningRules


def LoadPipeline(PipelineLocation):
    # if PipelineLocation.startswith("."):
    #     PipelineLocation = os.path.join(os.path.dirname(__file__),  PipelineLocation)
    with open(PipelineLocation, encoding="utf-8") as dictionary:
        for line in dictionary:
            action, _ = SeparateComment(line)
            if not action:
                continue
            PipeLine.append(action.strip())


#If the system files are new, then all rule files need to reload.
def SystemFileOlderThanDB():
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


def UpdateSystemFileFromDB():
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

def  LoadCommon():
    sys.setrecursionlimit(10**5)    # mostly for the recursive deepcopy when transform into DAG.
    if not utils.DisableDB:
        InitDB()

        import Cache
        Cache.LoadSentenceDB()

    LoadFrom = ParserConfig.get("main", "loadfrom").lower()
    if LoadFrom == "dump":
        LoadCommon_FromDump()
    elif LoadFrom == "database":
        LoadCommon_FromDB()
    else:
        LoadCommon_FromFiles()

    logging.info("Pipeline: {}".format(ParserConfig.get("main", "Pipelinefile")))

    rulenum = 0
    for rg in Rules.RuleGroupDict:
        rulenum += len(Rules.RuleGroupDict[rg].RuleList)
    logging.info("Features: {}\tAlias:{}\tLexicons: {}\tRules: {}".format(len(FeatureOntology._FeatureDict),
                  len(FeatureOntology._AliasDict), len(Lexicon._LexiconDict), rulenum))

    utils.initiated = True


def LoadCommon_FromDB():
    global PipeLine
    raise(Exception("TODO: Load From DB"))
    ### TODO: should I store the pipeline and 8 lexicon variables into db as well?


def LoadCommon_FromDump():
    global PipeLine, XLocation

    PipeLineLocation = ParserConfig.get("main", "Pipelinefile")
    # XLocation = os.path.dirname(PipeLineLocation)     # need to get relative location, not the absolute location.
    XLocation, _ = os.path.split(PipeLineLocation)
    XLocation += "/"
    #
    # with open(os.path.join(XLocation, "dump", "FeatureList.dump"), "rb") as dump:
    #     FeatureOntology._FeatureList = pickle.load( dump )
    # with open(os.path.join(XLocation, "dump", "FeatureOntologyDict.dump"), "rb") as dump:
    #     FeatureOntology._FeatureOntologyDict = pickle.load( dump )
    # also need to LoadAppendixList() and InitGlobalFeatureID(). so let's load
    FeaturefileLocation = os.path.join(XLocation, "feature.txt")
    FeatureOntology.LoadFeatureOntology(FeaturefileLocation)

    import gzip

    with gzip.open(os.path.join(XLocation, "dump", "rulegroups.dump"), "rb") as dump:
        Rules.RuleGroupDict = pickle.load( dump )

    with gzip.open(os.path.join(XLocation, "dump", "LexiconDict.dump"), "rb") as dump:
        Lexicon._LexiconDict = pickle.load( dump )
    with gzip.open(os.path.join(XLocation, "dump", "LexiconSensitiveDict.dump"), "rb") as dump:
        Lexicon._LexiconSensitiveDict = pickle.load( dump )
    with gzip.open(os.path.join(XLocation, "dump", "LexiconSegmentDict.dump"), "rb") as dump:
        Lexicon._LexiconSegmentDict = pickle.load( dump )
    with gzip.open(os.path.join(XLocation, "dump", "LexiconLookupSet.dump"), "rb") as dump:
        Lexicon._LexiconLookupSet = pickle.load( dump )
    with gzip.open(os.path.join(XLocation, "dump", "LexiconSegmentSlashDict.dump"), "rb") as dump:
        Lexicon._LexiconSegmentSlashDict = pickle.load( dump )
    with gzip.open(os.path.join(XLocation, "dump", "LexiconSpellingDict.dump"), "rb") as dump:
        Lexicon._LexiconSpellingDict = pickle.load(dump)

    with gzip.open(os.path.join(XLocation, "dump", "pipeline.dump"), "rb") as dump:
        PipeLine = pickle.load(dump)

    #
    # with open(os.path.join(XLocation, "dump", "rulegroups.dump"), "rb") as dump:
    #     Rules.RuleGroupDict = pickle.load(dump)
    #
    # with open(os.path.join(XLocation, "dump", "LexiconDict.dump"), "rb") as dump:
    #     Lexicon._LexiconDict = pickle.load(dump)
    # with open(os.path.join(XLocation, "dump", "LexiconSegmentDict.dump"), "rb") as dump:
    #     Lexicon._LexiconSegmentDictDict = pickle.load(dump)
    # with open(os.path.join(XLocation, "dump", "LexiconLookupSet.dump"), "rb") as dump:
    #     Lexicon._LexiconLookupSet = pickle.load(dump)
    # with open(os.path.join(XLocation, "dump", "LexiconSegmentSlashDict.dump"), "rb") as dump:
    #     Lexicon._LexiconSegmentSlashDict = pickle.load(dump)
    # with open(os.path.join(XLocation, "dump", "LexiconCuobieziDict.dump"), "rb") as dump:
    #     Lexicon._LexiconCuobieziDict = pickle.load(dump)
    # with open(os.path.join(XLocation, "dump", "LexiconFantiDict.dump"), "rb") as dump:
    #     Lexicon._LexiconFantiDict = pickle.load(dump)
    # with open(os.path.join(XLocation, "dump", "CompositeKG.dump"), "rb") as dump:
    #     Lexicon.CompositeKG = pickle.load(dump)
    # with open(os.path.join(XLocation, "dump", "CompositeKGSetADict.dump"), "rb") as dump:
    #     Lexicon.CompositeKGSetADict = pickle.load(dump)
    #
    # with open(os.path.join(XLocation, "dump", "pipeline.dump"), "rb") as dump:
    #     PipeLine = pickle.load(dump)

    logging.info("Done of LoadCommon_FromDump()!")


def Pipeline_LoadRule(_XLocation, action):
    action_upper = action.upper()
    if action_upper.startswith("FSA "):
        Rulefile = action[3:].strip()
        RuleLocation = os.path.join(_XLocation, Rulefile)
        verify_filename(RuleLocation)
        Rules.LoadRules(RuleLocation)

    # elif action_upper.startswith("DAGFSA_APP "):  # FUZZY
    #     Rulefile = action[10:].strip()
    #     RuleLocation = os.path.join(XLocation, Rulefile)
    #     reallocation = get_actual_filename(RuleLocation)
    #     if reallocation.replace("/", "_").replace("\\", "_") != RuleLocation.replace("/", "_").replace("\\", "_"):
    #         logging.error(
    #             "The location of {} is miss-spelled (CASE SENSTIVE), and it should be {}.  Please check: {}".format(RuleLocation, reallocation, action))
    #         raise Exception("Pipeline Content Error")
    #     Rules.LoadRules(RuleLocation, fuzzy=True)

    elif action_upper.startswith("DAGFSA "):
        Rulefile = action[6:].strip()
        RuleLocation = os.path.join(XLocation, Rulefile)
        verify_filename(RuleLocation)
        Rules.LoadRules(RuleLocation, isDagRule=True)


def Pipeline_LoadLexicon(_XLocation, action):
    action_upper = action.upper()
    # (O.O)
    if action_upper.startswith("STEMMING:"):
        Stemfiles = action[action.index(":") + 1:].strip().split(",")
        inf = Stemfiles[0].strip()
        InfLocation = os.path.join(XLocation, inf)
        Rules.LoadRules(InfLocation)
        Lexicon.LoadPrefixSuffix(InfLocation)
        for stem in Stemfiles[1:]:
            stem = stem.strip()
            if stem:
                stemlocation = os.path.join(XLocation, stem)
                verify_filename(stemlocation)
                Lexicon.LoadLexicon(stemlocation, lookupSource=LexiconLookupSource.STEMMING)

    elif action_upper.startswith("LOOKUP CUSTOMER:"):
        LookupInfo = action[action.index(":") + 1:].strip()
        try:
            LookupFile, ExtraInfo = LookupInfo.split(maxsplit=1)
        except ValueError:
            logging.error(f"There is no extra info for this Lookup Customer: {action}")
            logging.warning("     You can either add extra feature info for this dictionary, or move this to Lookup Lex.")
            return
        lookuplocation = os.path.join(XLocation, LookupFile)
        verify_filename(lookuplocation)
        Lexicon.LoadLexicon(lookuplocation, ExtraInfo=ExtraInfo)

    elif action_upper.startswith("LOOKUP "):
        if action_upper.startswith("LOOKUP SEGMENTSLASH:"):
            logging.warning("SEGMENTSLASH files are deprecated. The segments in Main and 5/6 rules are loaded automatically. ")
            return

        Lookupfiles = ''
        try:
            Lookupfiles = action[action.index(":") + 1:].strip().split(",")
        except ValueError:  # there is no file after :
            logging.debug("There is no file to load, just an execute lookup.")
            pass

        for lookup in Lookupfiles:
            lookup = lookup.strip()
            if lookup:
                lookuplocation = os.path.join(XLocation, lookup)
                verify_filename(lookuplocation)
                if action_upper.startswith("LOOKUP SPELLING:"):
                    Lexicon.LoadExtraReference(lookuplocation, Lexicon._LexiconSpellingDict)
                elif action.startswith("LOOKUP ENCODING:"):
                    logging.error("LOOKUP ENCODING is deprecated. Use LOOKUP SPELLING instead")
                #     Lexicon.LoadExtraReference(lookuplocation, Lexicon._LexiconFantiDict)
                elif action_upper.startswith("LOOKUP MAIN:"):
                    Lexicon.LoadMainLexicon(lookuplocation)
                elif action_upper.startswith("LOOKUP SENSITIVE:"):
                    Lexicon.LoadLexicon(lookuplocation, Sensitive=True)

                elif action_upper.startswith("LOOKUP LEX:"):
                    Lexicon.LoadLexicon(lookuplocation)
                elif action_upper.startswith("LOOKUP COMPOUND:"):
                    Lexicon.LoadLexicon(lookuplocation, lookupSource=LexiconLookupSource.COMPOUND)
                elif action_upper.startswith("LOOKUP DEFLEX:"):
                    Lexicon.LoadLexicon(lookuplocation, lookupSource=LexiconLookupSource.DEFLEX)
                elif action_upper.startswith("LOOKUP EXTERNAL:"):
                    Lexicon.LoadLexicon(lookuplocation, lookupSource=LexiconLookupSource.EXTERNAL)
                else:
                    logging.warning("Wrong Lookup statement in pipeline: {}".format(action))
                # if action.startswith("Lookup oQcQ:"):
                #     Lexicon.LoadLexicon(lookuplocation,lookupSource=LexiconLookupSource.oQcQ)
                # if action.startswith("Lookup IE:"):
                #     Lexicon.LoadCompositeKG(lookuplocation)


def LoadCommon_FromFiles():
    global XLocation

    PipeLineLocation = ParserConfig.get("main", "Pipelinefile")
    # XLocation = os.path.dirname(PipeLineLocation)     # need to get relative location, not the absolute location.
    XLocation, _ = os.path.split(PipeLineLocation)
    XLocation += "/"

    FeaturefileLocation = os.path.join(XLocation, "feature.txt")
    GlobalmacroLocation = os.path.join(XLocation, "../ontology/GlobalMacro.txt")
    # PunctuatefileLocation = os.path.join(XLocation, "../Y/LexY-EnglishPunctuate.txt")

    FeatureOntology.LoadFeatureOntology(FeaturefileLocation)


    Rules.LoadGlobalMacro(GlobalmacroLocation)
    Lexicon.LoadExtraReference(os.path.join(XLocation, "../ontology/linkDisplay.txt"), Lexicon._LexiconlinkDisplay)

    LoadPipeline(PipeLineLocation)

    logging.debug("Runtype:" + ParserConfig.get("main", "runtype"))
    logging.debug("utils.Runtype:" + utils.ParserConfig.get("main", "runtype"))


    # Lexicon.LoadLexicon(PunctuatefileLocation)

    for action in PipeLine:
        try:
            Pipeline_LoadLexicon(XLocation, action)
            Pipeline_LoadRule(XLocation, action)
        except RuntimeError as e:
            logging.error(f"Failed in loading pipeline. Please check {action}")
            raise e

    Lexicon.LoadSegmentLexicon()
    Lexicon.ApplyStemFeatures()
    #UpdateSystemFileFromDB(XLocation)

    if not utils.DisableDB:
        CloseDB(utils.DBCon)
    if ParserConfig.get("main", "runtype") == "Debug":
        logging.debug("Start writing temporary rule files")
        Rules.OutputRuleFiles(ParserConfig.get("main", "compiledfolder"))
        FeatureOntology.OutputFeatureOntologyFile(ParserConfig.get("main", "compiledfolder"))
        logging.debug("Start writing temporary lex file.")
        #Lexicon.OutputLexiconFile(ParserConfig.get("main", "compiledfolder"))

        #DumpPipelineFiles(XLocation)

    logging.info("StemFeatures:{}".format([FeatureOntology.GetFeatureName(x) for x in FeatureOntology.StemFeatureIDSet]))
    logging.info("Done of LoadCommon_FromFiles()!")


def DumpPipelineFiles():
    #Rules._PreProcess_RuleIDNormalize()
    if not os.path.exists(os.path.join(XLocation, "dump")):
        os.mkdir(os.path.join(XLocation, "dump"))

    # if needed, use pickle protocal 3 (python 3.0) for backward compatability. default is 4 (python 3.8 and up)
    import gzip

    with gzip.open(os.path.join(XLocation, "dump", "rulegroups.dump"), "wb") as dump:
        pickle.dump( Rules.RuleGroupDict, dump)

    with gzip.open(os.path.join(XLocation, "dump", "LexiconDict.dump"), "wb") as dump:
        pickle.dump(Lexicon._LexiconDict, dump)
    with gzip.open(os.path.join(XLocation, "dump", "LexiconSensitiveDict.dump"), "wb") as dump:
        pickle.dump(Lexicon._LexiconSensitiveDict, dump)

    with gzip.open(os.path.join(XLocation, "dump", "LexiconSegmentDict.dump"), "wb") as dump:
        pickle.dump(Lexicon._LexiconSegmentDict, dump)
    with gzip.open(os.path.join(XLocation, "dump", "LexiconLookupSet.dump"), "wb") as dump:
        pickle.dump(Lexicon._LexiconLookupSet, dump)
    with gzip.open(os.path.join(XLocation, "dump", "LexiconSegmentSlashDict.dump"), "wb") as dump:
        pickle.dump(Lexicon._LexiconSegmentSlashDict, dump)
    with gzip.open(os.path.join(XLocation, "dump", "LexiconSpellingDict.dump"), "wb") as dump:
        pickle.dump(Lexicon._LexiconSpellingDict, dump)

    with gzip.open(os.path.join(XLocation, "dump", "pipeline.dump"), "wb") as dump:
        pickle.dump( PipeLine, dump)


if __name__ == "__main__":
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    import cProfile, pstats
    cProfile.run("LoadCommon()", 'restatslex')
    pstat = pstats.Stats('restatslex')
    pstat.sort_stats('time').print_stats(20)
    # LoadCommon()

    target = "被告人俞红飞，男，1982年出生于浙江，住浙江海宁市。实话实说，冰箱还可以，但是本次购物体验十分垃圾"


    cProfile.run("LexicalAnalyze(target)", 'restatslex')
    pstat = pstats.Stats('restatslex')
    pstat.sort_stats('time').print_stats(20)

    document = """
浙江省海宁市人民法院
刑 事 判 决 书
（2020）浙0481刑初181号
公诉机关浙江省海宁市人民检察院。
被告人沈银锋，男，1988年8月18日出生于浙江省绍兴市上虞区，汉族，初中肄业文化，农民，住浙江省绍兴市上虞区。因犯寻衅滋事罪，2005年2月28日被绍兴市上虞区人民法院判处有期徒刑一年三个月，缓刑二年；因犯诈骗罪，2017年1月10日被绍兴市上虞区人民法院判处有期徒刑一年七个月，并处罚金人民币八千元，2018年3月3日刑满释放。因本案，2019年11月20日被刑事拘留，同年12月27日被依法逮捕。现羁押于海宁市看守所。
浙江省海宁市人民检察院以海检一部刑诉[2020]431号起诉书指控被告人沈银锋犯诈骗罪，于2020年3月27日向本院提起公诉。本院立案后，依法适用简易程序，实行独任审判，于2020年4月7日公开开庭审理了本案。海宁市人民检察院指派检察员刘辉及俞庶言出庭支持公诉。被告人沈银锋到庭参加诉讼，现已审理终结。
公诉机关指控，2019年10月，被告人沈银锋结伙卢某、姜某（均另案处理）经事先预谋，由被告人沈银锋事先将自已右手第5中节指骨敲成骨折后，以“碰瓷”方式骗取他人钱财。10月10日下午，被告人沈银锋和卢某、姜某窜至海宁市位置，由姜某驾驶汽车挤逼被害人王某1驾驶的电瓶三轮车，由被告人沈银锋驾驶电瓶车与被害人电瓶三轮车碰撞，然后去医院检查以右手第5指骨折为由，由卢某出面向被害人索某，骗得被害人王某1人民币3000元。10月20日下午，被告人沈银锋和卢某等人又窜至海盐县通元镇南王线一大桥下面，采用同样的方法骗得被害人黄某人民币4000元。案发后，被告人沈银锋的家属已将赃款全部退赔给两被害人，并取得谅解。
公诉机关认为，被告人沈银锋以非法占有为目的，结伙采用虚构事实、隐瞒真相的方法骗取他人财物，价值7000元，数额较大，犯罪事实清楚，证据确实充分，应当以诈骗罪追究其刑事责任。被告人沈银锋曾因故意犯罪被判处有期徒刑以上之刑罚，在前罪刑罚执行完毕后五年内再犯应当判处有期徒刑以上刑罚之罪，系累犯，依照《刑法》第六十五条第一款之规定，应当从重处罚。归案后，被告人沈银锋能如实供述自已的罪行，依法可从轻处罚。建议本院判处被告人沈银锋有期徒刑七个月，并处罚金人民币三千元。公诉机关提交了被害人王某1、黄某的陈述，证人石某、马某、沈某、王某2等人的证言，接受证据清单和银行交易明细，调取证据清单和门诊病历及DR报告单、影像资料、监控视频、收条及谅解书，前科资料，情况说明及抓获经过，辨认笔录及照片，视频截图等证据证实。
被告人沈银锋对公诉机关指控的事实、罪名及量刑建议没有异议，同意适用简易程序，且签字具结，在开庭审理过程中亦无异议。
经审理查明的事实、证据与公诉机关的指控一致。
本院认为，被告人沈银锋以非法占有为目的，结伙他人采用虚构事实、隐瞒真相等手段，骗取他人财物，价值7000元，数额较大，其行为已构成诈骗罪。公诉机关指控被告人沈银锋所犯罪名成立。被告人沈银锋曾因故意犯罪被判处有期徒刑以上之刑罚，在前罪刑罚执行完毕后五年内再犯应当判处有期徒刑以上刑罚之罪，系累犯，依法应当从重处罚。归案后，被告人沈银锋能如实供述自己的罪行，自愿认罪认罚，并退赔了全部损失，取得被害人的谅解，可以依法及酌情从轻处罚。公诉机关的量刑建议适当，应予采纳。据此，为保护公私财产不受侵犯，惩罚犯罪，依照《中华人民共和国刑法》第二百六十六条，第二十五条第一款，第六十五条第一款，第六十七条第三款，《中华人民共和国刑事诉讼法》第十五条之规定，判决如下：
被告人沈银锋犯诈骗罪，判处有期徒刑七个月，并处罚金人民币三千元。
（刑期从判决执行之日起计算。判决执行之前先行羁押的，羁押一日折抵刑期一日，即自2019年11月20日起至2020年6月19日止。罚金限判决生效后一个月内缴纳。）
如不服本判决，可在接到判决书的第二日起十日内，通过本院或者直接向浙江省嘉兴市中级人民法院提出上诉。书面上诉的，应交上诉状正本一份，副本二份。
审判员　　金仁法
二〇二〇年四月七日
书记员　　张雨洁
    """

    cProfile.run("DocumentAnalyze(document)", 'restatslex')
    pstat = pstats.Stats('restatslex')
    pstat.sort_stats('time').print_stats(20)




