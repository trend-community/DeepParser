import logging, re
import Tokenization, FeatureOntology
import Rules
from LogicOperation import LogicMatch #, LogicMatchFeatures

counterMatch = 0


#Every token in ruleTokens must match each token in strTokens, from head.
def HeadMatch(strTokens, ruleTokens):
    if len(ruleTokens) > len(strTokens):
        return False

    for i in range(len(ruleTokens)):
            if not LogicMatch(ruleTokens[i].word.strip("[").strip("]"), strTokens[i]):
                return False  # otherwise, this rule does not fit for this string

    return True

def ApplyWinningRule(strtokens, rule):
    print("Applying " + rule.output('concise'))
    for i in range(len(rule.Tokens)):
        if hasattr(rule.Tokens[i], 'action'):
            Actions = rule.Tokens[i].action.split()
            logging.warning("Word:" + strtokens[i].word)
            logging.warning("Before applying feature:" + str(strtokens[i].features))
            logging.warning("The features are:" + str(Actions))

            for Action in Actions:
                ActionID = FeatureOntology.GetFeatureID(Action)
                if ActionID != -1:
                    strtokens[i].features.add(ActionID)
            logging.warning("After applying feature:" + str(strtokens[i].features))

    return len(rule.Tokens) #need to modify for those "forward looking rules"

def SearchMatchingRule(strtokens):
    for RuleFileName in Rules.RuleFileList:
        print("Applying:" + RuleFileName)

        for i in range(len(strtokens)):
            logging.warning("Checking tokens start from:" + strtokens[i].word)
            WinningRule = None
            for rule in Rules._ExpertLexicon:
                if rule.FileName == RuleFileName:
                    result = HeadMatch(strtokens[i:], rule.Tokens)
                    if result:
                        if WinningRule and len(WinningRule.Tokens)>len(rule.Tokens):
                            pass
                        else:
                            WinningRule = rule

            if WinningRule:
                skiptokennum = ApplyWinningRule(strtokens[i:], WinningRule)
                i += skiptokennum-2    #go to the next word
                continue

            for rule in Rules._RuleList:
                if rule.FileName == RuleFileName:
                    result = HeadMatch(strtokens[i:], rule.Tokens)
                    if result:
                        if WinningRule and len(WinningRule.Tokens) > len(rule.Tokens):
                            pass
                        else:
                            WinningRule = rule
            if WinningRule:
                skiptokennum = ApplyWinningRule(strtokens[i:], WinningRule)
                i += skiptokennum-2    #go to the next word


if __name__ == "__main__":
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
    FeatureOntology.LoadFullFeatureList('../../fsa/extra/featurelist.txt')
    FeatureOntology.LoadFeatureOntology('../../fsa/Y/feature.txt')
    FeatureOntology.LoadLexicon('../../fsa/Y/lexY.txt')

    #Rules.LoadRules("../../fsa/Y/100y.txt")

    Rules.LoadRules("../../fsa/Y/800VGy.txt")
    Rules.LoadRules("../../fsa/Y/900NPy.xml")
    # Rules.LoadRules("../../fsa/Y/1800VPy.xml")
    # Rules.LoadRules("../../fsa/Y/1test_rules.txt")
    Rules.ExpandRuleWildCard()

    Rules.ExpandParenthesisAndOrBlock()
    Rules.ExpandRuleWildCard()

    target = "she may like the product  "
    logging.info(target)
    nodes = Tokenization.Tokenize(target)
    for node in nodes:
        node.lexicon = FeatureOntology.SearchLexicon(node.word)
        node.features = set()
        if node.lexicon:
            node.features.update(node.lexicon.features)
        else:
            node.features.add(FeatureOntology.GetFeatureID('NNP'))
    nodes[0].features.add(FeatureOntology.GetFeatureID('JS'))
    nodes[0].features.add(FeatureOntology.GetFeatureID('JS2'))
    # default lexY.txt is already loaded. additional lexicons can be load here:
    # FeatureOntology.LoadLexicon("../../fsa/X/lexX.txt")
    for node in nodes:
        output = "Node [" + node.word + "] "
        if node.lexicon:
            output += str(node.lexicon) + "-"
        output += str(node.features) + ";"
        print(output)

    logging.warning("\tStart matching rules! counterMatch=%s" % counterMatch)
    SearchMatchingRule(nodes)
    logging.warning("After match:")
    for node in nodes:
        output = "Node [" + node.word + "] "
        output += str(node.features) + ";"
        print(output)

    logging.warning("\tDone! counterMatch=%s" % counterMatch)
