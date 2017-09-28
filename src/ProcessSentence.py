import logging, re, requests, jsonpickle
import Tokenization, FeatureOntology, Lexicon
import Rules
from LogicOperation import LogicMatch #, LogicMatchFeatures
from utils import *

counterMatch = 0


#Every token in ruleTokens must match each token in strTokens, from head.
def HeadMatch(strTokens, ruleTokens):
    if len(ruleTokens) > len(strTokens):
        return False

    GoneInStrTokens = 0
    for i in range(len(ruleTokens)):
        try:
            #Ignore the "Gone" tokens.
            while strTokens[i+GoneInStrTokens].Gone :
                GoneInStrTokens += 1
                if i+GoneInStrTokens == len(strTokens):
                    return False    #got to the end of the string
            if not LogicMatch(ruleTokens[i].word, strTokens[i+GoneInStrTokens]):
                return False  #  this rule does not fit for this string
        except Exception as e:
            logging.error("Using " + ruleTokens[i].word + " to match:" + strTokens[i+GoneInStrTokens].word )
            logging.error(e)
            #raise
    return True


def ApplyFeature(featureList, featureID):
    featureList.add(featureID)
    FeatureNode = FeatureOntology.SearchFeatureOntology(featureID)
    if  FeatureNode:
        featureList.update(FeatureNode.ancestors)


#During chucking "+++", concatenate the stem of each token of this group
# (find the starting point and ending point) into the current token stem
# and mark the others Gone
def Chunking(StrTokens, StrPosition, RuleTokens, RulePosition):
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

    if IsAscii(NewStems):
        NewStem = " ".join(NewStems)
    else:
        NewStem = "".join(NewStems)
    StrTokens[StrPosition].stem = NewStem
    StrTokens[StrPosition].Gone = False


# Apply the features, and other actions.
#TODO: Apply Mark ".M", group head <, tail > ...
def ApplyWinningRule(strtokens, rule, StartPosition):
    print("Applying Winning Rule:" + rule.RuleName)
    GoneInStrTokens = 0
    for i in range(len(rule.Tokens)):
        while strtokens[StartPosition + i + GoneInStrTokens].Gone:
            GoneInStrTokens += 1
            if i + GoneInStrTokens == len(strtokens):
                raise RuntimeError("Can't be applied: " + rule.RuleName)
        if hasattr(rule.Tokens[i], 'action'):
            Actions = rule.Tokens[i].action.split()
            logging.warning("Word:" + strtokens[StartPosition + i + GoneInStrTokens].word)
            logging.warning("Before applying actions:" + str(strtokens[StartPosition + i + GoneInStrTokens].features))
            logging.warning("The actions are:" + str(Actions))

            if "NEW" in Actions:
                strtokens[StartPosition + i + GoneInStrTokens].features = set()
            for Action in Actions:
                if Action == "NEW":
                    continue
                if Action == "+++":
                    Chunking(strtokens, StartPosition + i + GoneInStrTokens, rule.Tokens, i)
                    continue
                ActionID = FeatureOntology.GetFeatureID(Action)
                if ActionID == FeatureOntology.GetFeatureID("Gone"):
                    strtokens[StartPosition + i + GoneInStrTokens].Gone = True
                if ActionID != -1:
                    ApplyFeature(strtokens[StartPosition + i + GoneInStrTokens].features, ActionID)
                    #strtokens[StartPosition + i + GoneInStrTokens].features.add(ActionID)
            logging.warning("After applying feature:" + str(strtokens[StartPosition + i + GoneInStrTokens].features))

    return len(rule.Tokens) #need to modify for those "forward looking rules"


def MatchAndApplyRuleFile(strtokens, FileName):
    WinningRules = []
    i = 0

    while i < len(strtokens):
        if strtokens[i].Gone:
            i += 1
            continue
        logging.warning("Checking tokens start from:" + strtokens[i].word)
        WinningRule = None
        for rule in Rules._ExpertLexicon:
            if rule.FileName == FileName:
                result = HeadMatch(strtokens[i:], rule.Tokens)
                if result:
                    if WinningRule and len(WinningRule.Tokens) >= len(rule.Tokens):
                        # also consider the priority
                        pass
                    else:
                        WinningRule = rule

        if WinningRule:
            skiptokennum = ApplyWinningRule(strtokens, WinningRule, StartPosition=i)
            i += skiptokennum - 1  # go to the next word
            WinningRules.append(WinningRule.RuleName)
            i += 1
            continue

        for rule in Rules._RuleList:
            if rule.FileName == FileName:
                result = HeadMatch(strtokens[i:], rule.Tokens)
                if result:
                    if WinningRule and len(WinningRule.Tokens) >= len(rule.Tokens):
                        # also consider the priority
                        pass
                    else:
                        WinningRule = rule
        if WinningRule:
            skiptokennum = ApplyWinningRule(strtokens, WinningRule, StartPosition=i)
            i += skiptokennum - 1  # go to the next word
            WinningRules.append(WinningRule.RuleName)

        i += 1
    return WinningRules


def MatchAndApplyAllRules(strtokens):
    WinningRules = []
    for RuleFileName in Rules.RuleFileList:
        logging.info("Applying:" + RuleFileName)
        WinningRules.extend(MatchAndApplyRuleFile(strtokens, RuleFileName))

    return WinningRules


def MultiLevelSegmentation(Sentence):
    Nodes = Tokenization.Tokenize(Sentence)
    Lexicon.ApplyLexiconToNodes(Nodes)
    MatchAndApplyRuleFile(Nodes, "0defLexX.txt")
    Lexicon.LexiconLookup(Nodes)
    MatchAndApplyAllRules(Nodes)
    return Nodes


def LoadCommon(LoadCommonRules=False):
    FeatureOntology.LoadFullFeatureList('../../fsa/extra/featurelist.txt')
    FeatureOntology.LoadFeatureOntology('../../fsa/Y/feature.txt')
    Lexicon.LoadLexicon('../../fsa/Y/lexY.txt')
    Lexicon.LoadLexicon('../../fsa/X/lexX.txt')
    Lexicon.LoadLexicon('../../fsa/X/brandX.txt')
    Lexicon.LoadLexicon('../../fsa/X/idiom4X.txt')
    Lexicon.LoadLexicon('../../fsa/X/idiomX.txt')
    Lexicon.LoadLexicon('../../fsa/X/locX.txt')
    Lexicon.LoadLexicon('../../fsa/X/perX.txt')
    Lexicon.LoadLexicon('../../fsa/X/defLexX.txt', forLookup=True)

    logging.warning("Parameter is:" + str(LoadCommonRules))
    if LoadCommonRules:
        Rules.LoadRules("../../fsa/X/0defLexX.txt")
        #Rules.LoadRules("../temp/800VGy.txt.compiled")
        #Rules.LoadRules("../temp/900NPy.xml.compiled")
        #Rules.LoadRules("../temp/1800VPy.xml.compiled")
        #Rules.LoadRules("../../fsa/Y/900NPy.xml")
        #Rules.LoadRules("../../fsa/Y/1800VPy.xml")
        # Rules.LoadRules("../../fsa/Y/1test_rules.txt")
        Rules.LoadRules("../../fsa/X/mainX2.txt")
        Rules.LoadRules("../../fsa/X/ruleLexiconX.txt")
        #Rules.LoadRules("../../fsa/Y/100y.txt")
        # Rules.LoadRules("../../fsa/X/180NPx.txt")
        # Rules.LoadRules("../../fsa/X/270VPx.txt")

        Rules.ExpandRuleWildCard()
        Rules.ExpandParenthesisAndOrBlock()
        Rules.ExpandRuleWildCard()

        Rules.OutputRuleFiles("../temp/")

if __name__ == "__main__":
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
    FeatureOntology.LoadFullFeatureList('../../fsa/extra/featurelist.txt')
    FeatureOntology.LoadFeatureOntology('../../fsa/Y/feature.txt')

    #Lexicon.LoadLexicon('../../fsa/X/lexX.txt')
    Lexicon.LoadLexicon('../../fsa/Y/lexY.txt')
    #Lexicon.LoadLexicon('../../fsa/X/brandX.txt')
    #Lexicon.LoadLexicon('../../fsa/X/idiom4X.txt')
    #Lexicon.LoadLexicon('../../fsa/X/idiomX.txt')
    #Lexicon.LoadLexicon('../../fsa/X/locX.txt')
    #Lexicon.LoadLexicon('../../fsa/X/perX.txt')

    #Rules.LoadRules("../../fsa/Y/100y.txt")
    #Rules.LoadRules("../../fsa/X/mainX2.txt")
    # Rules.LoadRules("../../fsa/X/ruleLexiconX.txt")
    # Rules.LoadRules("../../fsa/Y/100y.txt")

    #Rules.LoadRules("../../fsa/Y/800VGy.txt")
    #Rules.LoadRules("../temp/800VGy.txt.compiled")
    #Rules.LoadRules("../../fsa/Y/900NPy.xml")
    #Rules.LoadRules("../../fsa/Y/1800VPy.xml")
    Rules.LoadRules("../../fsa/X/0defLexX.txt")
    Rules.LoadRules("../../fsa/Y/1test_rules.txt")
    Rules.ExpandRuleWildCard()

    Rules.ExpandParenthesisAndOrBlock()
    Rules.ExpandRuleWildCard()

    target = "八十五分不等于五分。 "
    logging.info(target)
    nodes = Tokenization.Tokenize(target)

    Lexicon.ApplyLexiconToNodes(nodes)

    JSnode = Tokenization.SentenceNode('')
    nodes = [JSnode] + nodes
    if nodes[-1].word != ".":
        JWnode = Tokenization.SentenceNode('')
        nodes = nodes + [JWnode]
    nodes[0].features.add(FeatureOntology.GetFeatureID('JS'))
    nodes[1].features.add(FeatureOntology.GetFeatureID('JS2'))
    nodes[-1].features.add(FeatureOntology.GetFeatureID('JW'))
    Lexicon.LexiconLookup(nodes)

    for node in nodes:
        output = "Node [" + node.word + "] "
        if node.lexicon:
            output += str(node.lexicon) + "-"
        output += str(node.features) + ";"
        print(output)

    logging.warning("\tStart matching rules! counterMatch=%s" % counterMatch)
    RuleNames, _ = MatchAndApplyAllRules(nodes)
    print("After match:")
    for node in nodes:
        output = "Node [" + node.word + "] "
        if node.lexicon:
            output += str(node.lexicon) + "-"
        output += str(node.features) + ";"
        print(output)

    logging.warning("\tDone! counterMatch=%s" % counterMatch)

    print(OutputStringTokens_oneliner(nodes))