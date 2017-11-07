import logging, re, requests, jsonpickle
import Tokenization, FeatureOntology, Lexicon
import Rules
from LogicOperation import LogicMatch #, LogicMatchFeatures
from utils import *

counterMatch = 0

WinningRuleDict = {}


def MarkWinningTokens(strtokens, rule, StartPosition):
    result = ""
    if strtokens.size >= 3:
        AddSpace = IsAscii(strtokens.get(1).text) and IsAscii(strtokens.get(strtokens.size-2).text) and IsAscii(strtokens.get(int(strtokens.size/2)).text)
    else:
        AddSpace = IsAscii(strtokens.get(1).text)

    p = strtokens.head
    counter = 0
    StopPosition = StartPosition+len(rule.Tokens) - 1
    while p:
        if counter == StartPosition:
            result += "<B>"
        result += p.text
        if counter == StopPosition:
            result += "</B>"
        if AddSpace:
            result += " "
        p = p.next
        counter += 1

    return result.strip()


def StoreWinningRule(strtokens, rule, StartPosition):
    global WinningRuleDict

    if rule.ID in WinningRuleDict:
        _, hits = WinningRuleDict[rule.ID]
        hits.append(MarkWinningTokens(strtokens, rule, StartPosition))
    else:
        WinningRuleDict[rule.ID] = [rule, [MarkWinningTokens(strtokens, rule, StartPosition)]]


def OutputWinningRules():
    output = ""

    for rule, hits in sorted(WinningRuleDict.values()):
        output += '[Rule file]' + rule.FileName +  ' [Rule origin]' + rule.Origin + ' [Hits_num]' + str(len(hits)) + ' [Hits]\t' + str(hits) + "\n"

    return output

#Every token in ruleTokens must match each token in strTokens, from StartPosition.
def HeadMatch(strTokenList, StartPosition, ruleTokens):
    Start = 0
    if ruleTokens[0].StartTrunk:    # the first rule token is StartTrunk,
        Start = 0  #1                   # then pretend there is one [] in fron of it, so
                                    # the first strTokenList is matched, can skip to next one;
    for i in range(Start, len(ruleTokens)):
        try:
            if not LogicMatch(strTokenList, i+StartPosition, ruleTokens[i].word, ruleTokens, i):
                return False  #  this rule does not fit for this string
        except RuntimeError as e:
            logging.error("Using " + ruleTokens[i].word + " to match:" + strTokenList.get(i).word)
            logging.error(e)
            # raise
        except Exception as e:
            logging.error("Using " + ruleTokens[i].word + " to match:" + strTokenList.get(i).word )
            logging.error(e)
            raise
        except IndexError as e:
            logging.error("Using " + ruleTokens[i].word + " to match:" + strTokenList.get(i).word )
            logging.error(e)
            raise

    return True


def ApplyFeature(featureList, featureID):
    featureList.add(featureID)
    FeatureNode = FeatureOntology.SearchFeatureOntology(featureID)
    if  FeatureNode:
        featureList.update(FeatureNode.ancestors)


#search from the end. The rule position is the first one that has EndChunk
# temporary, only do one level.
# might need to restructure the rules.
#   compile it to two parts: presentation (for matching), and action.
def ApplyChunking(StrTokenList, StrPosition, RuleTokens, RuleEndPosition):
    RulePos = RuleEndPosition
    EndTrunk = 0
    HeadIndex = 0
    while RulePos >= 0:
        # Find the head in this trunk: The one with not "^.M" in Action.
        EndTrunk += RuleTokens[RulePos].EndTrunk
        EndTrunk -= RuleTokens[RulePos].StartTrunk
        if not hasattr(RuleTokens[RulePos], 'action') or '^' not in RuleTokens[RulePos].action:
            HeadIndex = RulePos
            logging.debug("Found Head!" + str(HeadIndex) + " rule: " + str(RuleTokens[RulePos]))
        if EndTrunk == 0:
            #found to start position.
            break
        if EndTrunk < 0:
            #this is actually correct in current step.
            break
            #Wrong in rule.
            # logging.info("StrPosition=" + str(StrPosition) + "RuleEndPosition=" + str(RuleEndPosition))
            # logging.error("Endtrunk<0" + jsonpickle.dumps(RuleTokens))
            # raise RuntimeError("Wrong in Tokens. Can not find matched trunk!")
        RulePos -= 1
    if RulePos < 0:
        logging.error("RulePos < 0 " + str([str(r) for r in RuleTokens]))
        raise RuntimeError("Wrong in Tokens. Can not find matched trunk until the begining of the rule!")

    RuleStartPosition = RulePos
    ChunkLength = RuleEndPosition - RuleStartPosition
    StrStartPosition = StrPosition - ChunkLength
    StrTokenList.combine(StrStartPosition, ChunkLength+1, HeadIndex-RuleStartPosition)
    return ChunkLength+1


# Apply the features, and other actions.
#TODO: Apply Mark ".M", group head <, tail > ...
def ApplyWinningRule(strtokens, rule, StartPosition):

    if not strtokens:
        logging.error("The strtokens to ApplyWinningRule is blank!")
        raise(RuntimeError("wrong string to apply rule?"))
    if strtokens.size > 2:
        logging.info("Applying Winning Rule:" + rule.RuleName +" to "
                     + strtokens.get(1).text + strtokens.get(2).text + "...")
        logging.debug(jsonpickle.dumps(strtokens))
    StoreWinningRule(strtokens, rule, StartPosition)

    if len(rule.Tokens) == 0:
        logging.error("Lenth = 0, error! Need to revisit the parsing process")
        logging.error(str(rule))
        raise(RuntimeError("Rule error"))
    for i in range(len(rule.Tokens)):
        token = strtokens.get(i+StartPosition)
        try:
            logging.debug("Before:\n" + "in position " + str(StartPosition + i )
                          + " Rule is:" + jsonpickle.dumps(rule.Tokens[i]))
        except IndexError as e:
            logging.error("Wrong when trying to debug and dump. maybe the string is not long enough?")
            logging.error(str(rule))
            logging.error(str(e))
            return len(rule.Tokens)

        if hasattr(rule.Tokens[i], 'action'):
            Actions = rule.Tokens[i].action.split()
            logging.debug("Word:" + token.text)

            if "NEW" in Actions:
                token.features = set()
            for Action in Actions:
                if Action == "NEW":
                    continue        #already process before.

                if Action[-1] == "-":
                    FeatureID = FeatureOntology.GetFeatureID(Action.strip("-"))
                    if FeatureID in token.features:
                        token.features.remove(FeatureID)
                    continue

                if Action[-1] == "+" and Action != "+++":
                    MajorPOSFeatures = ["A", "N", "P", "R", "RB", "X", "V"]
                    if Action.strip("+") in MajorPOSFeatures:
                        for conflictfeature in MajorPOSFeatures:
                            conflictfeatureid = FeatureOntology.GetFeatureID(conflictfeature)
                            if conflictfeatureid in token.features:
                                token.features.remove(conflictfeatureid)
                                #TODO: Might also remove the child features of them. Check spec.

                    FeatureID = FeatureOntology.GetFeatureID(Action.strip("+"))
                    ApplyFeature(token.features, FeatureID)
                    continue

                if Action[0] == "^":
                    #TODO: linked the str tokens.
                    token.UpperRelationship = Action
                    continue

                ActionID = FeatureOntology.GetFeatureID(Action)
                if ActionID == FeatureOntology.GetFeatureID("Gone"):
                    token.Gone = True
                if ActionID != -1:
                    ApplyFeature(token.features, ActionID)
                    #strtokens[StartPosition + i + GoneInStrTokens].features.add(ActionID)

    i = len(rule.Tokens)-1    # process from the end to start.
    while i >= 0:
        try:
            logging.debug("Checking " + str(i) + " while Endtrunk=" + str(rule.Tokens[i].EndTrunk))
            if rule.Tokens[i].EndTrunk:
                logging.debug("Before Chunking:\n" + "in position " + str(StartPosition + i)
                              + " Rule is:" + jsonpickle.dumps(rule.Tokens[i]))
                CheunkedTokenNum = ApplyChunking(strtokens, StartPosition + i, rule.Tokens, i)
                i -= CheunkedTokenNum
        except IndexError as e:
            logging.error("Error when checking EndTrunk and apply trunking")
            logging.error(str(e))
            return len(rule.Tokens)
        i -= 1

    logging.debug(jsonpickle.dumps(strtokens))
    #TODO: find the specific item of "last trunk" to return.
    #or maybe the item number of "collapsed" tokens.
    return 0 #need to modify for those "forward looking rules"


def MatchAndApplyRuleFile(strtokenlist, RuleFileName):
    WinningRules = []
    i = 0
    logging.debug("Matching using file:" + RuleFileName)

    while i < strtokenlist.size:
        logging.debug("Checking tokens start from:" + strtokenlist.get(i).text)
        WinningRule = None
        rulegroup = Rules.RuleGroupDict[RuleFileName]
        WinningRuleSize = 0
        for rule in rulegroup.ExpertLexicon:
            if i+len(rule.Tokens) > strtokenlist.size:
                continue
            if WinningRuleSize < len(rule.Tokens):
                result = HeadMatch(strtokenlist, i, rule.Tokens)
                if result:
                    WinningRule = rule
                    WinningRuleSize = len(WinningRule.Tokens)
                    if WinningRuleSize+i >= strtokenlist.size:
                        logging.debug("Found a winning rule that matchs up to the end of the string.")
                        break

        if WinningRule:
            try:
                skiptokennum = ApplyWinningRule(strtokenlist, WinningRule, StartPosition=i)
            except RuntimeError as e:
                if e.args and e.args[0] == "Rule error":
                    logging.error("The rule is so wrong that it has to be removed from rulegroup " + RuleFileName)
                    rulegroup.ExpertLexicon.remove(WinningRule)
            #i += skiptokennum  # go to the next word
            WinningRules.append(WinningRule.RuleName)
            i += 1
            continue

        WinningRuleSize = 0
        for rule in rulegroup.RuleList:
            if i + len(rule.Tokens) > strtokenlist.size:
                continue
            if WinningRuleSize < len(rule.Tokens):
                result = HeadMatch(strtokenlist, i, rule.Tokens)
                if result:
                    WinningRule = rule
                    WinningRuleSize = len(WinningRule.Tokens)
                    if WinningRuleSize + i >= strtokenlist.size:
                        logging.debug("Found a winning rule that matchs up to the end of the string.")
                        break
        if WinningRule:
            try:
                skiptokennum = ApplyWinningRule(strtokenlist, WinningRule, StartPosition=i)
                logging.debug("After applied: " + jsonpickle.dumps(strtokenlist))
            except RuntimeError as e:
                if e.args and e.args[0] == "Rule error":
                    logging.error("The rule is so wrong that it has to be removed from rulegroup " + RuleFileName)
                    rulegroup.RuleList.remove(WinningRule)
                    skiptokennum = 0
            #i += skiptokennum - 1  # go to the next word
            WinningRules.append(WinningRule.RuleName)

        i += 1
    return WinningRules


def _MatchAndApplyAllRules(strtokens, ExcludeList):
    WinningRules = []
    for RuleFileName in sorted(Rules.RuleGroupDict, key=Rules.RuleGroupDict.get):
        if RuleFileName in ExcludeList:
            continue
        WinningRules.extend(MatchAndApplyRuleFile(strtokens, RuleFileName))

    return WinningRules

invalidchar_pattern = re.compile(u'[^\u0000-\uD7FF\uE000-\uFFFF]', re.UNICODE)


def MultiLevelSegmentation(Sentence):
    try:
        logging.debug("-Start MultiLevelSegmentation: tokenize")

        Sentence = invalidchar_pattern.sub(u'\uFFFD', Sentence)
        NodeList = Tokenization.Tokenize(Sentence)
        if not NodeList:
            return None
        logging.debug("-Start ApplyLexiconToNodes")
        Lexicon.ApplyLexiconToNodes(NodeList)

        NodeList.head.features.add(FeatureOntology.GetFeatureID('JS2'))
        JSnode = Tokenization.SentenceNode('')
        JSnode.features.add(FeatureOntology.GetFeatureID('JS'))
        NodeList.insert(JSnode, 0)

        if NodeList.tail.text != "." and FeatureOntology.GetFeatureID('punc') not in NodeList.tail.features:
            JMnode = Tokenization.SentenceNode('')
            JMnode.StartOffset = NodeList.tail.EndOffset
            JMnode.EndOffset = NodeList.tail.EndOffset
            NodeList.append(JMnode)
        NodeList.tail.features.add(FeatureOntology.GetFeatureID('JM'))
        NodeList.tail.prev.features.add(FeatureOntology.GetFeatureID('JM2'))

        WinningRules = []

        logging.debug("-Start MatchAndApplyRuleFile")
        WinningRules.extend(MatchAndApplyRuleFile(NodeList, "0defLexX.txt"))
        logging.debug("-Start LexiconLookup")
        Lexicon.LexiconLookup(NodeList)

        #MatchAndApplyRuleFile(Nodes, "1test_rules.txt")

        logging.debug("-Start MatchAndApplyRuleFile rules except 0defLexX")
        WinningRules.extend(_MatchAndApplyAllRules(NodeList, ExcludeList=["0defLexX.txt"]))

        logging.debug("-End MultiLevelSegmentation")

    except Exception as e:
        logging.error("Overall Error in MultiLevelSegmentation:")
        logging.error(e)
        return None

    return NodeList, WinningRules


def LoadCommon(LoadCommonRules=False):
    #FeatureOntology.LoadFullFeatureList('../../fsa/extra/featurelist.txt')
    FeatureOntology.LoadFeatureOntology('../../fsa/Y/feature.txt')
    #Lexicon.LoadLexicon('../../fsa/Y/lexY.txt')
    #Lexicon.LoadLexicon('../../fsa/X/QueryLexicon.txt')

    Lexicon.LoadLexicon('../../fsa/X/LexX.txt')
    Lexicon.LoadLexicon('../../fsa/X/LexXplus.txt')
    Lexicon.LoadLexicon('../../fsa/X/brandX.txt')
    Lexicon.LoadLexicon('../../fsa/X/idiom4X.txt')
    Lexicon.LoadLexicon('../../fsa/X/idiomX.txt')
    Lexicon.LoadLexicon('../../fsa/X/locX.txt')
    Lexicon.LoadLexicon('../../fsa/X/perX.txt')
    Lexicon.LoadLexicon('../../fsa/X/defPlus.txt')
    Lexicon.LoadLexicon('../../fsa/X/defLexX.txt', forLookup=True)


    # Lexicon.LoadLexicon('../../fsa/X/Q/lexicon/CleanLexicon_gram_2_list.txt')
    # Lexicon.LoadLexicon('../../fsa/X/Q/lexicon/CleanLexicon_gram_3_list.txt')
    # Lexicon.LoadLexicon('../../fsa/X/Q/lexicon/CleanLexicon_gram_4_list.txt')
    # Lexicon.LoadLexicon('../../fsa/X/Q/lexicon/CleanLexicon_gram_5_list.txt')

    if LoadCommonRules:
        Rules.LoadRules("../../fsa/X/0defLexX.txt")
        # Rules.LoadRules("../../fsa/Y/800VGy.txt")
        # Rules.LoadRules("../../fsa/Y/900NPy.xml")
        # Rules.LoadRules("../../fsa/Y/1800VPy.xml")
        # Rules.LoadRules("../../fsa/Y/1test_rules.txt")

        Rules.LoadRules("../../fsa/X/idiomPlus.txt")
        Rules.LoadRules("../../fsa/X/1Expert.txt")
        Rules.LoadRules("../../fsa/X/1Grammar.txt")
        Rules.LoadRules("../../fsa/X/5ngramMain.txt")


        Rules.LoadRules("../../fsa/X/8Expert.txt")
        Rules.LoadRules("../../fsa/X/8Grammar.txt")
        Rules.LoadRules("../../fsa/X/10Expert.txt")
        Rules.LoadRules("../../fsa/X/10Grammar.txt")
        Rules.LoadRules("../../fsa/X/20Expert.txt")
        Rules.LoadRules("../../fsa/X/20Grammar.txt")
        Rules.LoadRules("../../fsa/X/30Expert.txt")
        Rules.LoadRules("../../fsa/X/30Grammar.txt")
        Rules.LoadRules("../../fsa/X/40Expert.txt")
        Rules.LoadRules("../../fsa/X/40Grammar.txt")
        Rules.LoadRules("../../fsa/X/50Expert.txt")
        Rules.LoadRules("../../fsa/X/50Grammar.txt")
        Rules.LoadRules("../../fsa/X/60Expert.txt")
        Rules.LoadRules("../../fsa/X/60Grammar.txt")
        Rules.LoadRules("../../fsa/X/70Expert.txt")
        Rules.LoadRules("../../fsa/X/70Grammar.txt")
        Rules.LoadRules("../../fsa/X/80Expert.txt")
        Rules.LoadRules("../../fsa/X/80Grammar.txt")
        Rules.LoadRules("../../fsa/X/90Expert.txt")
        Rules.LoadRules("../../fsa/X/90Grammar.txt")
        Rules.LoadRules("../../fsa/X/100Expert.txt")
        Rules.LoadRules("../../fsa/X/100Grammar.txt")
        Rules.LoadRules("../../fsa/X/180NPx.txt")

        #Rules.LoadRules("../../fsa/X/Q/rule/xac")
        # Rules.LoadRules("../../fsa/X/Q/rule/xab")
        # Rules.LoadRules("../../fsa/X/Q/rule/xac")
        # Rules.LoadRules("../../fsa/X/Q/rule/CleanRule_gram_4_list.txt")
        # Rules.LoadRules("../../fsa/X/Q/rule/CleanRule_gram_5_list.txt")

        #Rules.LoadRules("../../fsa/X/270VPx.txt")

        Rules.ExpandRuleWildCard()
        Rules.ExpandParenthesisAndOrBlock()
        Rules.ExpandRuleWildCard()
        Rules.PreProcess_CheckFeatures()

        Rules.OutputRuleFiles("../temp/")
        #print(Lexicon.OutputLexicon(False))

if __name__ == "__main__":
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
    LoadCommon(True)

    target = "LCD屏幕面层很不错"
    nodes, winningrules = MultiLevelSegmentation(target)
    if not nodes:
        logging.warning("The result is None!")
        exit(1)


    logging.info("\tDone! counterMatch=%s" % counterMatch)

    print(OutputStringTokens_oneliner(nodes, NoFeature=True))
    print(OutputStringTokens_oneliner(nodes))

    print(nodes.root().CleanOutput().toJSON())

    print("Winning rules:\n" + OutputWinningRules())

    print(FeatureOntology.OutputMissingFeatureSet())

