import logging, sys, re
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
    #FeatureOntology.LoadLexicon('../../fsa/X/lexX.txt')

    Rules.LoadRules("../temp/800VGy.txt.compiled")
    #Rules.LoadRules("../temp/900NPy.xml.compiled")
    #Rules.LoadRules("../../fsa/Y/1800VPy.xml")
    #Rules.LoadRules("../../fsa/Y/1test_rules.txt")
    Rules.ExpandRuleWildCard()

    Rules.ExpandParenthesisAndOrBlock()
    Rules.ExpandRuleWildCard()

    Rules.OutputRuleFiles("../temp/")

    for unittestnode in Rules.UnitTest:
        ExtraMessageIndex = unittestnode.TestSentence.find(">")
        if ExtraMessageIndex>0:
            TestSentence = unittestnode.TestSentence[:ExtraMessageIndex]
        else:
            TestSentence = unittestnode.TestSentence
        print("***Test rule " + unittestnode.RuleName + " using sentence: " + TestSentence)

        nodes = Tokenization.Tokenize(TestSentence)

        VFeatureID = FeatureOntology.GetFeatureID("V")
        VBFeatureID = FeatureOntology.GetFeatureID("VB")
        for node in nodes:
            node.lexicon = FeatureOntology.SearchLexicon(node.word)
            node.features = set()
            if node.lexicon:
                node.features.update(node.lexicon.features)
                node.features = FeatureOntology.ApplyWordVariant(node, node.lexicon.word)
                # if (node.word == node.lexicon.word+"d" or node.word == node.lexicon.word+"ed") \
                #     and VFeatureID in node.lexicon.features:
                #     node.features.add(FeatureOntology.GetFeatureID("Ved"))
                #     if VBFeatureID in node.features:
                #         node.features.remove(VBFeatureID)
                # if (node.word == node.lexicon.word + "ing")  \
                #         and VFeatureID in node.lexicon.features:
                #     node.features.add(FeatureOntology.GetFeatureID("Ving"))
                #     if VBFeatureID in node.features:
                #         node.features.remove(VBFeatureID)
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

        if DebugMode:
            for node in nodes:
                print(node)

        WinningRules = ProcessSentence.SearchMatchingRule(nodes)
        for WinningRule in WinningRules:
            if Rules.GetPrefix(WinningRule) == Rules.GetPrefix(unittestnode.RuleName):
                print ("***Found " +WinningRule + " for: \n\t" + TestSentence)


    if DebugMode:
        Rules.OutputRules('concise')