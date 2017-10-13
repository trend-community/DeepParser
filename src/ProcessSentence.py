import logging, re, requests, jsonpickle
import Tokenization, FeatureOntology, Lexicon
import Rules
from LogicOperation import LogicMatch #, LogicMatchFeatures
from utils import *

counterMatch = 0

WinningRuleDict = {}


def MarkWinningTokens(strtokens, rule, StartPosition):
    result = ""
    if len(strtokens) >= 3:
        AddSpace = IsAscii(strtokens[1].word) and IsAscii(strtokens[-2].word) and IsAscii(strtokens[int(len(strtokens)/2)].word)
    else:
        AddSpace = IsAscii(strtokens[1].word)
    for i in range(StartPosition):
        if not strtokens[i].Gone:
            result += strtokens[i].stem
            if AddSpace:
                result += " "

    GoneInStrTokens = 0
    result += "<B>"
    for i in range(len(rule.Tokens)):
        while strtokens[StartPosition + i + GoneInStrTokens].Gone:
            GoneInStrTokens += 1
            if i + GoneInStrTokens == len(strtokens):
                raise RuntimeError("Can't be applied: " + rule.RuleName)
        result += strtokens[StartPosition + i + GoneInStrTokens].stem
        if AddSpace:
            result += " "
    result += "</B>"

    for i in range(StartPosition + len(rule.Tokens) + GoneInStrTokens, len(strtokens)):
        if not strtokens[i].Gone:
            result += strtokens[i].stem
            if AddSpace:
                result += " "

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
        output += json.dumps({' rule file': rule.FileName,  'rule origin': rule.Origin, 'Hits_num': len(hits), 'hits:': hits}, ensure_ascii=False) + "\n"

    return output

#Every token in ruleTokens must match each token in strTokens, from head.
def HeadMatch(strTokens, ruleTokens):
    if len(ruleTokens) > len(strTokens):
        return False

    GoneInStrTokens = 0
    for i in range(len(ruleTokens)):
        if i + GoneInStrTokens >= len(strTokens):
            return False  # got to the end of the string
        try:
            #Ignore the "Gone" tokens.
            while strTokens[i+GoneInStrTokens].Gone :
                GoneInStrTokens += 1
                if i+GoneInStrTokens >= len(strTokens):
                    return False    #got to the end of the string
            if not strTokens[i+GoneInStrTokens].word:
                #logging.warning("Got to " + str(i+GoneInStrTokens) + "th word of tokens:" + strTokens[0].word)
                return False
            if not LogicMatch(ruleTokens[i].word, strTokens[i+GoneInStrTokens]):
                return False  #  this rule does not fit for this string
        except RuntimeError as e:
            logging.error("Using " + ruleTokens[i].word + " to match:" + strTokens[i + GoneInStrTokens].word)
            logging.error(e)
            # raise
        except Exception as e:
            logging.error("Using " + ruleTokens[i].word + " to match:" + strTokens[i+GoneInStrTokens].word )
            logging.error(e)
            raise
        except IndexError as e:
            logging.error("Using " + ruleTokens[i].word + " to match:" + strTokens[i+GoneInStrTokens].word )
            logging.error(e)
            raise

    return True


def ApplyFeature(featureList, featureID):
    featureList.add(featureID)
    FeatureNode = FeatureOntology.SearchFeatureOntology(featureID)
    if  FeatureNode:
        featureList.update(FeatureNode.ancestors)


#During chunking "+++", concatenate the stem of each token of this group
# (find the starting point and ending point) into the current token stem
# and mark the others Gone
def ApplyChunking(StrTokens, StrPosition, RuleTokens, RulePosition):
    RuleStartPos = RulePosition
    StrStartPos = StrPosition
    GoneInStrTokens = 0
    while RuleStartPos >= 0:
        while StrTokens[StrStartPos-GoneInStrTokens].Gone:
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

    RuleEndPos = RulePosition
    StrEndPos = StrPosition
    GoneInStrTokens = 0
    while RuleEndPos < len(RuleTokens):
        while StrTokens[StrEndPos+GoneInStrTokens].Gone:
            GoneInStrTokens += 1
            if StrEndPos+GoneInStrTokens > len(StrTokens):
                raise EOFError("Reached the end of the String!")
        if RuleTokens[RuleEndPos].EndTrunk:
            break
        StrEndPos += 1
        RuleEndPos += 1
    if RuleEndPos == len(RuleTokens):
        raise EOFError("Can't find EndTrunk")
    StrEndPos = StrEndPos+GoneInStrTokens

    NewStems = []
    for i in range(StrStartPos, StrEndPos+1):
        if StrTokens[i].Gone:
            continue
        NewStems.append( StrTokens[i].stem)     # or StrTokens[i].lexicon.stem?
        StrTokens[i].Gone = True

    StrTokens[StrStartPos].StartTrunk -= 1
    StrTokens[StrEndPos].EndTrunk -= 1

    if IsAscii(NewStems):
        NewStem = " ".join(NewStems)
    else:
        NewStem = "".join(NewStems)
    StrTokens[StrPosition].stem = NewStem
    StrTokens[StrPosition].Gone = False
    Lexicon.ApplyWordLengthFeature(StrTokens[StrPosition])


# Apply the features, and other actions.
#TODO: Apply Mark ".M", group head <, tail > ...
def ApplyWinningRule(strtokens, rule, StartPosition):
    logging.info("Applying Winning Rule:" + rule.RuleName)
    StoreWinningRule(strtokens, rule, StartPosition)
    GoneInStrTokens = 0
    if len(rule.Tokens) == 0:
        logging.error("Lenth = 0, error! Need to revisit the parsing process")
        logging.error(str(rule))
        raise(RuntimeError("Rule error"))
    for i in range(len(rule.Tokens)):
        while strtokens[StartPosition + i + GoneInStrTokens].Gone:
            GoneInStrTokens += 1
            if i + GoneInStrTokens == len(strtokens):
                raise RuntimeError("Can't be applied: " + rule.RuleName)
        strtokens[StartPosition + i + GoneInStrTokens].StartTrunk = rule.Tokens[i].StartTrunk
        strtokens[StartPosition + i + GoneInStrTokens].EndTrunk = rule.Tokens[i].EndTrunk

        if hasattr(rule.Tokens[i], 'action'):
            Actions = rule.Tokens[i].action.split()
            logging.debug("Word:" + strtokens[StartPosition + i + GoneInStrTokens].word)
            logging.debug("Before applying actions:" + str(strtokens[StartPosition + i + GoneInStrTokens].features))
            logging.debug("The actions are:" + str(Actions))

            if "NEW" in Actions:
                strtokens[StartPosition + i + GoneInStrTokens].features = set()
            for Action in Actions:
                if Action == "NEW":
                    continue
                if Action == "+++":
                    ApplyChunking(strtokens, StartPosition + i + GoneInStrTokens, rule.Tokens, i)
                    continue
                ActionID = FeatureOntology.GetFeatureID(Action)
                if ActionID == FeatureOntology.GetFeatureID("Gone"):
                    strtokens[StartPosition + i + GoneInStrTokens].Gone = True
                if ActionID != -1:
                    ApplyFeature(strtokens[StartPosition + i + GoneInStrTokens].features, ActionID)
                    #strtokens[StartPosition + i + GoneInStrTokens].features.add(ActionID)
            logging.debug("After applying feature:" + str(strtokens[StartPosition + i + GoneInStrTokens].features))

    return len(rule.Tokens) #need to modify for those "forward looking rules"


def MatchAndApplyRuleFile(strtokens, FileName):
    WinningRules = []
    i = 0

    while i < len(strtokens):
        if strtokens[i].Gone:
            i += 1
            continue
        #logging.debug("Checking tokens start from:" + strtokens[i].word)
        WinningRule = None
        rulegroup = Rules.RuleGroupDict[FileName]
        for rule in rulegroup.ExpertLexicon:
                result = HeadMatch(strtokens[i:], rule.Tokens)
                if result:
                    if WinningRule and len(WinningRule.Tokens) >= len(rule.Tokens):
                        # also consider the priority
                        pass
                    else:
                        WinningRule = rule

        if WinningRule:
            try:
                skiptokennum = ApplyWinningRule(strtokens, WinningRule, StartPosition=i)
            except RuntimeError as e:
                if e.args and e.args[0] == "Rule error":
                    logging.error("The rule is so wrong that it has to be removed from rulegroup " + FileName)
                    rulegroup.ExpertLexicon.remove(WinningRule)
            i += skiptokennum - 1  # go to the next word
            WinningRules.append(WinningRule.RuleName)
            i += 1
            continue

        for rule in rulegroup.RuleList:
                result = HeadMatch(strtokens[i:], rule.Tokens)
                if result:
                    if WinningRule and len(WinningRule.Tokens) >= len(rule.Tokens):
                        # also consider the priority
                        pass
                    else:
                        WinningRule = rule
        if WinningRule:
            try:
                skiptokennum = ApplyWinningRule(strtokens, WinningRule, StartPosition=i)
            except RuntimeError as e:
                if e.args and e.args[0] == "Rule error":
                    logging.error("The rule is so wrong that it has to be removed from rulegroup " + FileName)
                    rulegroup.RuleList.remove(WinningRule)
                    skiptokennum = 0
            i += skiptokennum - 1  # go to the next word
            WinningRules.append(WinningRule.RuleName)

        i += 1
    return WinningRules


def MatchAndApplyAllRules(strtokens, ExcludeList=[]):
    WinningRules = []
    for RuleFileName in Rules.RuleGroupDict:
        if RuleFileName in ExcludeList:
            continue
        logging.info("Applying:" + RuleFileName)
        WinningRules.extend(MatchAndApplyRuleFile(strtokens, RuleFileName))

    return WinningRules


def MultiLevelSegmentation(Sentence):
    logging.debug("-Start MultiLevelSegmentation: tokenize")
    Nodes = Tokenization.Tokenize(Sentence)
    logging.debug("-Start ApplyLexiconToNodes")
    Lexicon.ApplyLexiconToNodes(Nodes)

    JSnode = Tokenization.SentenceNode('')
    Nodes = [JSnode] + Nodes
    if Nodes[-1].word != "." and FeatureOntology.GetFeatureID('punc') not in Nodes[-1].features:
        JWnode = Tokenization.SentenceNode('')
        Nodes = Nodes + [JWnode]
    Nodes[0].features.add(FeatureOntology.GetFeatureID('JS'))
    Nodes[1].features.add(FeatureOntology.GetFeatureID('JS2'))
    Nodes[-1].features.add(FeatureOntology.GetFeatureID('JM'))

    logging.debug("-Start MatchAndApplyRuleFile")
    MatchAndApplyRuleFile(Nodes, "0defLexX.txt")
    logging.debug("-Start LexiconLookup")
    Lexicon.LexiconLookup(Nodes)

    #MatchAndApplyRuleFile(Nodes, "1test_rules.txt")

    logging.debug("-Start MatchAndApplyRuleFile rules except 0defLexX")
    MatchAndApplyAllRules(Nodes, ExcludeList=["0defLexX.txt"])

    logging.debug("-End MultiLevelSegmentation")
    return Nodes


def LoadCommon(LoadCommonRules=False):
    #FeatureOntology.LoadFullFeatureList('../../fsa/extra/featurelist.txt')
    FeatureOntology.LoadFeatureOntology('../../fsa/Y/feature.txt')
    #Lexicon.LoadLexicon('../../fsa/Y/lexY.txt')
    Lexicon.LoadLexicon('../../fsa/X/LexX.txt')
    Lexicon.LoadLexicon('../../fsa/X/LexXplus.txt')
    Lexicon.LoadLexicon('../../fsa/X/brandX.txt')
    Lexicon.LoadLexicon('../../fsa/X/idiom4X.txt')
    Lexicon.LoadLexicon('../../fsa/X/idiomX.txt')
    Lexicon.LoadLexicon('../../fsa/X/locX.txt')
    Lexicon.LoadLexicon('../../fsa/X/perX.txt')
    Lexicon.LoadLexicon('../../fsa/X/defLexX.txt', forLookup=True)

    if LoadCommonRules:
        Rules.LoadRules("../../fsa/X/0defLexX.txt")
        # Rules.LoadRules("../../fsa/Y/800VGy.txt")
        # Rules.LoadRules("../../fsa/Y/900NPy.xml")
        # Rules.LoadRules("../../fsa/Y/1800VPy.xml")
        # Rules.LoadRules("../../fsa/Y/1test_rules.txt")
        Rules.LoadRules("../../fsa/X/mainX2.txt")
        Rules.LoadRules("../../fsa/X/ruleLexiconX.txt")
        # Rules.LoadRules("../../fsa/Y/100y.txt")
        Rules.LoadRules("../../fsa/X/10compound.txt")
        Rules.LoadRules("../../fsa/X/180NPx.txt")

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
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    LoadCommon(True)

    target = "八十五分不等于五分。 "
    nodes = MultiLevelSegmentation(target)

    for node in nodes:
        print(str(node))

    print(OutputStringTokens_oneliner(nodes))

    logging.info("\tStart matching rules! counterMatch=%s" % counterMatch)
    RuleNames = MatchAndApplyAllRules(nodes)
    print("After match:")
    for node in nodes:
        print(str(node))

    logging.info("\tDone! counterMatch=%s" % counterMatch)

    print(OutputStringTokens_oneliner(nodes))

    print("Winning rules:\n" + OutputWinningRules())

    print(FeatureOntology.OutputMissingFeatureSet())
