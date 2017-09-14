import logging, sys
import Tokenization, FeatureOntology
import ProcessSentence, Rules
from Rules import _RuleList, _ExpertLexicon

if __name__ == "__main__":
    DebugMode = False
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == 'Debug':
            DebugMode = True

        else:
            print(
                "Usage: python SentenceTest.py Debug")
            exit(0)

    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
    FeatureOntology.LoadFullFeatureList('../../fsa/extra/featurelist.txt')
    FeatureOntology.LoadFeatureOntology('../../fsa/Y/feature.txt')
    FeatureOntology.LoadLexicon('../../fsa/Y/lexY.txt')

    Rules.LoadRules("../temp/800VGy.txt.compiled")
    #Rules.LoadRules("../temp/900NPy.xml.compiled")
    #Rules.LoadRules("../../fsa/Y/1800VPy.xml")
    #Rules.LoadRules("../../fsa/Y/1test_rules.txt")
    Rules.ExpandRuleWildCard()

    Rules.ExpandParenthesisAndOrBlock()
    Rules.ExpandRuleWildCard()

    for RuleName, TestSentence in Rules.UnitTest.items():
        ExtraMessageIndex = TestSentence.find(">")
        if ExtraMessageIndex>0:
            TestSentence = TestSentence[:ExtraMessageIndex]
        print("***Test rule " + RuleName + " using sentence: " + TestSentence)

        nodes = Tokenization.Tokenize(TestSentence)

        for node in nodes:
            node.lexicon = FeatureOntology.SearchLexicon(node.word)
            node.features = set()
            if node.lexicon:
                node.features.update(node.lexicon.features)
                if (node.word == node.lexicon.word+"d" or node.word == node.lexicon.word+"ed") \
                    and FeatureOntology.GetFeatureID("V") in node.lexicon.features:
                    node.features.add(FeatureOntology.GetFeatureID("Ved"))
            else:
                node.features.add(FeatureOntology.GetFeatureID('NNP'))
        nodes[0].features.add(FeatureOntology.GetFeatureID('JS'))
        nodes[0].features.add(FeatureOntology.GetFeatureID('JS2'))

        if DebugMode:
            for node in nodes:
                print(node)

        WinningRules = ProcessSentence.SearchMatchingRule(nodes)
        for WinningRule in WinningRules:
            if WinningRule == RuleName or WinningRule.startswith(RuleName + "_"):
                print ("Found " +WinningRule + " for: \n" + TestSentence)


    if DebugMode:
        Rules.OutputRules('concise')