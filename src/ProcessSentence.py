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

    for rulename in WinningRuleDict:
        rule, hits = WinningRuleDict[rulename]
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
    EndTrunk = RuleTokens[RuleEndPosition].EndTrunk
    while RulePos >= 0:
        #TODO: Find the head in this trunk
        EndTrunk -= RuleTokens[RulePos].StartTrunk
        if EndTrunk == 0:
            #found to start position.
            break
        if EndTrunk < 0:
            #Wrong in rule.
            logging.error(str(RuleTokens))
            raise RuntimeError("Wrong in Tokens. Can not find matched trunk!")
        RulePos -= 1
    if RulePos < 0:
        logging.error(str(RuleTokens))
        raise RuntimeError("Wrong in Tokens. Can not find matched trunk until the begining of the rule!")

    ChunkLength = RuleEndPosition - RulePos
    StrStartPosition = StrPosition - ChunkLength
    StrTokenList.combine(StrStartPosition, ChunkLength+1)

#During chunking "+++", concatenate the stem of each token of this group
# (find the starting point and ending point) into the current token stem
# and mark the others Gone
def ApplyChunking2(StrTokens, StrPosition, RuleTokens, RulePosition):
    ToBeGoneList = []
    RuleStartPos = RulePosition
    StrStartPos = StrPosition
    GoneInStrTokens = 0
    while RuleStartPos >= 0:
        while StrTokens[StrStartPos-GoneInStrTokens].Gone or StrTokens[StrStartPos-GoneInStrTokens].SkipRead:
            logging.debug(str(StrTokens[StrStartPos-GoneInStrTokens]) + " is gone!")
            GoneInStrTokens += 1
            if StrStartPos-GoneInStrTokens < 0:
                raise EOFError("Reached the start of the String!")
        if RuleTokens[RuleStartPos].StartTrunk:
            break
        StrStartPos -= 1
        RuleStartPos -= 1
    if RuleStartPos == -1:
        raise EOFError("Can't find StartTrunk")
    StrStartPos = StrStartPos-GoneInStrTokens

    logging.debug("set StrPosition=" + str(StrPosition) + " StrStartPos=" + str(StrStartPos) )
    logging.debug("    GoneInStrTokens=" + str(GoneInStrTokens))

    RuleEndPos = RulePosition
    StrEndPos = StrPosition
    GoneInStrTokens = 0
    while RuleEndPos < len(RuleTokens):
        while StrTokens[StrEndPos+GoneInStrTokens].Gone or StrTokens[StrEndPos+GoneInStrTokens].SkipRead:
            GoneInStrTokens += 1
            if StrEndPos+GoneInStrTokens > len(StrTokens):
                raise EOFError("Reached the end of the String!")
        if RuleTokens[RuleEndPos].EndTrunk:
            break
        StrEndPos += 1
        RuleEndPos += 1
    if RuleEndPos == len(RuleTokens):
        logging.error("String:" + jsonpickle.dumps(StrTokens))
        logging.error("Rule:" + jsonpickle.dumps(RuleTokens))
        raise EOFError("Can't find EndTrunk")
    StrEndPos = StrEndPos+GoneInStrTokens

    logging.debug("StrPosition=" + str(StrPosition) + " StrStartPos=" + str(StrStartPos) + " StrEndPos=" + str(StrEndPos))
    logging.debug("    GoneInStrTokens=" + str(GoneInStrTokens))
    NewStems = []
    for i in range(StrStartPos, StrEndPos+1):
        if StrTokens[i].Gone:
            continue
        NewStems.append( StrTokens[i].stem)     # or StrTokens[i].lexicon.stem?
        if i != StrPosition:
            ToBeGoneList.append(i)
        #StrTokens[i].Gone = True

    StrTokens[StrStartPos].StartTrunk -= 1
    StrTokens[StrEndPos].EndTrunk -= 1

    if IsAscii(NewStems):
        NewStem = " ".join(NewStems)
    else:
        NewStem = "".join(NewStems)
    StrTokens[StrPosition].stem = NewStem
    #StrTokens[StrPosition].Gone = False
    StrTokens[StrPosition].StartOffset = StrTokens[StrStartPos].StartOffset
    StrTokens[StrPosition].EndOffset = StrTokens[StrEndPos].EndOffset

    Lexicon.ApplyWordLengthFeature(StrTokens[StrPosition])

    return 0


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


def MatchAndApplyAllRules(strtokens, ExcludeList):
    WinningRules = []
    for RuleFileName in Rules.RuleGroupDict:
        if RuleFileName in ExcludeList:
            continue
        WinningRules.extend(MatchAndApplyRuleFile(strtokens, RuleFileName))

    return WinningRules

invalidchar_pattern = re.compile(u'[^\u0000-\uD7FF\uE000-\uFFFF]', re.UNICODE)


def MultiLevelSegmentation(Sentence):
    logging.debug("-Start MultiLevelSegmentation: tokenize")

    Sentence = invalidchar_pattern.sub(u'\uFFFD', Sentence)
    NodeList = Tokenization.Tokenize(Sentence)
    logging.debug("-Start ApplyLexiconToNodes")
    Lexicon.ApplyLexiconToNodes(NodeList)

    JSnode = Tokenization.SentenceNode('')
    JSnode.features.add(FeatureOntology.GetFeatureID('JS'))
    NodeList.insert(JSnode, 0)
    NodeList.get(1).features.add(FeatureOntology.GetFeatureID('JS2'))

    if NodeList.tail.text != "." and FeatureOntology.GetFeatureID('punc') not in NodeList.tail.features:
        JMnode = Tokenization.SentenceNode('')
        NodeList.append(JMnode)
    NodeList.tail.features.add(FeatureOntology.GetFeatureID('JM'))
    NodeList.tail.prev.features.add(FeatureOntology.GetFeatureID('JM2'))



    logging.debug("-Start MatchAndApplyRuleFile")
    MatchAndApplyRuleFile(NodeList, "0defLexX.txt")
    logging.debug("-Start LexiconLookup")
    Lexicon.LexiconLookup(NodeList)

    #MatchAndApplyRuleFile(Nodes, "1test_rules.txt")

    logging.debug("-Start MatchAndApplyRuleFile rules except 0defLexX")
    MatchAndApplyAllRules(NodeList, ExcludeList=["0defLexX.txt"])

    logging.debug("-End MultiLevelSegmentation")
    return NodeList


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

    target = "学习不学习,吃了没有?"
    nodes = MultiLevelSegmentation(target)

    # for node in nodes:
    #     print(str(node))

    print(OutputStringTokens_oneliner(nodes))

    # logging.info("\tStart matching rules! counterMatch=%s" % counterMatch)
    # RuleNames = MatchAndApplyAllRules(nodes, ExcludeList=["0defLexX.txt"])
    # print("After match:")
    # for node in nodes:
    #     print(str(node))

    logging.info("\tDone! counterMatch=%s" % counterMatch)

    print(OutputStringTokens_oneliner(nodes, NoFeature=True))
    print(OutputStringTokens_oneliner(nodes))

    print(jsonpickle.encode(nodes))

    print("Winning rules:\n" + OutputWinningRules())

    print(FeatureOntology.OutputMissingFeatureSet())
