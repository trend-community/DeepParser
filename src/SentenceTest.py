import logging, re
import Tokenization, FeatureOntology
import ProcessSentence, Rules
from Rules import _RuleList, _ExpertLexicon

if __name__ == "__main__":
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
    FeatureOntology.LoadFullFeatureList('../../fsa/extra/featurelist.txt')
    FeatureOntology.LoadFeatureOntology('../../fsa/Y/feature.txt')
    FeatureOntology.LoadLexicon('../../fsa/Y/lexY.txt')

    #Rules.LoadRules("../../fsa/Y/800VGy.txt")
    Rules.LoadRules("../../fsa/Y/900NPy.xml")
    #Rules.LoadRules("../../fsa/Y/1800VPy.xml")
    Rules.LoadRules("../../fsa/Y/1test_rules.txt")
    Rules.ExpandRuleWildCard()

    Rules.ExpandParenthesisAndOrBlock()
    Rules.ExpandRuleWildCard()

    for RuleName, TestSentence in Rules.UnitTest.items():
        nodes = Tokenization.Tokenize(TestSentence)

        for node in nodes:
            node.lexicon = FeatureOntology.SearchLexicon(node.word)
            node.features = set()
            if node.lexicon:
                node.features.update(node.lexicon.features)
            else:
                node.features.add(FeatureOntology.GetFeatureID('NNP'))
        nodes[0].features.add(FeatureOntology.GetFeatureID('JS'))
        nodes[0].features.add(FeatureOntology.GetFeatureID('JS2'))

        WinningRules = ProcessSentence.SearchMatchingRule(nodes)
        for WinningRule in WinningRules:
            if WinningRule.startswith(RuleName):
                print ("Found " +WinningRule + " for: \n" + TestSentence)
        logging.warning("After match:")
        for node in nodes:
            output = "Node [" + node.word + "] "
            output += str(node.features) + ";"
            print(output)

