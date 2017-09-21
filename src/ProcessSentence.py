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
        try:
            if not LogicMatch(ruleTokens[i].word, strTokens[i]):
                return False  #  this rule does not fit for this string
        except Exception as e:
            logging.error("Using " + ruleTokens[i].word + " to match:" + strTokens[i].word )
            logging.error(e)
            #raise
    return True

def ApplyFeature(featureList, featureID):
    FeatureNode = FeatureOntology.SearchFeatureOntology(featureID)
    if not FeatureNode:
        raise Exception("The feature node should not be null!")
    featureList.add(featureID)
    featureList.update(FeatureNode.ancestors)

# Apply the features, and other actions.
#TODO: Apply Mark ".M", group head <, tail > ...
def ApplyWinningRule(strtokens, rule):
    print("Applying Winning Rule:" + rule.RuleName)
    for i in range(len(rule.Tokens)):
        if hasattr(rule.Tokens[i], 'action'):
            Actions = rule.Tokens[i].action.split()
            logging.warning("Word:" + strtokens[i].word)
            logging.warning("Before applying feature:" + str(strtokens[i].features))
            logging.warning("The features are:" + str(Actions))

            if "NEW" in Actions:
                strtokens[i].features = []
            for Action in Actions:
                if Action == "NEW":
                    continue
                ActionID = FeatureOntology.GetFeatureID(Action)
                if ActionID != -1:
                    ApplyFeature(strtokens[i].features, ActionID)
                    #strtokens[i].features.add(ActionID)
            logging.warning("After applying feature:" + str(strtokens[i].features))

    return len(rule.Tokens) #need to modify for those "forward looking rules"

def SearchMatchingRule(strtokens):
    WinningRules = []
    for RuleFileName in Rules.RuleFileList:
        print("Applying:" + RuleFileName)
        i = 0

        while i < len(strtokens):
            logging.warning("Checking tokens start from:" + strtokens[i].word)
            WinningRule = None
            for rule in Rules._ExpertLexicon:
                if rule.FileName == RuleFileName:
                    result = HeadMatch(strtokens[i:], rule.Tokens)
                    if result:
                        if WinningRule and len(WinningRule.Tokens) >= len(rule.Tokens):
                            #also consider the priority
                            pass
                        else:
                            WinningRule = rule

            if WinningRule:
                skiptokennum = ApplyWinningRule(strtokens[i:], WinningRule)
                i += skiptokennum-1    #go to the next word
                WinningRules.append(WinningRule.RuleName)
                i += 1
                continue

            for rule in Rules._RuleList:
                if rule.FileName == RuleFileName:
                    result = HeadMatch(strtokens[i:], rule.Tokens)
                    if result:
                        if WinningRule and len(WinningRule.Tokens) >= len(rule.Tokens):
                        #also consider the priority
                            pass
                        else:
                            WinningRule = rule
            if WinningRule:
                skiptokennum = ApplyWinningRule(strtokens[i:], WinningRule)
                i += skiptokennum - 1    #go to the next word
                WinningRules.append(WinningRule.RuleName)

            i += 1
    return WinningRules

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
    Rules.LoadRules("../../fsa/Y/1800VPy.xml")
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
            if (node.word == node.lexicon.word + "d" or node.word == node.lexicon.word + "ed") \
                    and FeatureOntology.GetFeatureID("V") in node.lexicon.features:
                node.features.add(FeatureOntology.GetFeatureID("Ved"))
            if (node.word == node.lexicon.word + "ing") \
                    and FeatureOntology.GetFeatureID("V") in node.lexicon.features:
                node.features.add(FeatureOntology.GetFeatureID("Ving"))
        else:
            node.features.add(FeatureOntology.GetFeatureID('NNP'))
    JSnode = Tokenization.SentenceNode()
    nodes = [JSnode] + nodes
    if nodes[-1].word != ".":
        JWnode = Tokenization.SentenceNode()
        nodes = nodes + [JWnode]
    nodes[0].features.add(FeatureOntology.GetFeatureID('JS'))
    nodes[1].features.add(FeatureOntology.GetFeatureID('JS2'))
    nodes[-1].features.add(FeatureOntology.GetFeatureID('JW'))
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
