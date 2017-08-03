import logging
import Tokenization, FeatureOntology
import Rules
from LogicOperation import LogicMatch, LogicMatchFeatures

counterMatch = 0


def TokenMatch(strtoken, ruletoken):
    if not strtoken:
        return False
    global counterMatch
    word = strtoken.word.lower()
    if strtoken.lexicon:
        word = strtoken.lexicon.word.lower()
    counterMatch += 1
    rule = ruletoken.word.strip("[").strip("]")
    if not rule:  # "[]", not sure what that is.
        return False
    if rule.startswith("\""):  # word  comparison
        return LogicMatch(rule.strip("\""), word)  # case insensitive
    if rule.startswith("'"):
        if strtoken.lexicon and hasattr(strtoken.lexicon, "stem"):  # stem comparison
            return LogicMatch(rule.strip("\'"), strtoken.lexicon.stem)
        else:
            return LogicMatch(rule.strip("\'"), word)
    if rule.startswith("/"):
        if strtoken.lexicon and hasattr(strtoken.lexicon, "norm"):  # stem comparison
            return LogicMatch(rule.strip("/"), strtoken.lexicon.norm)
        else:
            return LogicMatch(rule.strip("/"), word)

    # compare feature
    if strtoken.lexicon:
        return LogicMatchFeatures(rule, strtoken.lexicon.features)
    else:
        return False
        # featureID = FeatureOntology.GetFeatureID(rule)

        # if featureID and featureID in lextoken.features:
        #     return True
        # else:
        #     return False


def Match(strTokens, ruleTokens):
    space = [[0 for j in range(len(strTokens) + 1)]
             for i in range(len(ruleTokens) + 1)
             ]

    for i in range(1, len(ruleTokens) + 1):
        MatchOnce = False
        for j in range(1, len(strTokens) + 1):
            if TokenMatch(strTokens[j - 1], ruleTokens[i - 1]):
                space[i][j] = 1 + space[i - 1][j - 1]
                MatchOnce = True
        if not MatchOnce:  # at least match once.
            return False  # otherwise, this rule does not fit for this string

    maxValue = 0
    for j in range(1, len(strTokens) + 1):
        maxValue = space[len(ruleTokens)][j] if space[len(ruleTokens)][j] > maxValue else maxValue

    if maxValue == len(ruleTokens):
        # if maxValue > 0:
        print("Match!!! %s" % maxValue)
        return True
    else:
        return False


def SearchMatchingRule(strtokens):
    for rule in Rules._ExpertLexicon:
        result = Match(strtokens, rule.Tokens)
        if result:
            print(rule)

    for rule in Rules._RuleList:
        result = Match(strtokens, rule.Tokens)
        if result:
            print(rule)


if __name__ == "__main__":
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    FeatureOntology.LoadFullFeatureList('../../fsa/extra/featurelist.txt')
    FeatureOntology.LoadFeatureOntology('../../fsa/Y/feature.txt')
    FeatureOntology.LoadLexicon('../../fsa/Y/lexY.txt')

    Rules.LoadRules("../../fsa/Y/900NPy.xml")
    Rules.LoadRules("../../fsa/Y/1800VPy.xml")
    #Rules.LoadRules("../../fsa/Y/test_rules.txt")
    Rules.ExpandRuleWildCard()

    target = "you three come here"
    logging.info(target)
    nodes = Tokenization.Tokenize(target)
    for node in nodes:
        node.lexicon = FeatureOntology.SearchLexicon(node.word)

    # default lexY.txt is already loaded. additional lexicons can be load here:
    # FeatureOntology.LoadLexicon("../../fsa/X/lexX.txt")
    for node in nodes:
        output = "Node [" + node.word + "] "
        if node.lexicon:
            output += str(node.lexicon) + ";"
        print(output)

    logging.warning("\tStart matching rules! counterMatch=%s" % counterMatch)
    SearchMatchingRule(nodes)
    logging.warning("\tDone! counterMatch=%s" % counterMatch)
