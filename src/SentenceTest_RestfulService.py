import logging, sys, re, os
import Tokenization, FeatureOntology, Lexicon
import ProcessSentence, Rules
import requests, json, jsonpickle
from functools import lru_cache
from utils import *



if __name__ == "__main__":
    DebugMode = False
    if len(sys.argv) > 1:
        UnitTestFileName = sys.argv[1]
        if len(sys.argv) > 2:
            command = sys.argv[2]
            if command == 'Debug':
                DebugMode = True
    else:
        print(
            "Usage: python SentenceTest_ResefulService.py unittestfile [Debug]")
        exit(0)

    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

    FeatureOntology.LoadFullFeatureList('../../fsa/extra/featurelist.txt')
    # Lexicon.LoadLexicon('../../fsa/Y/lexY.txt')
    Lexicon.LoadLexicon('../../fsa/X/defLexX.txt', True)
    #Lexicon.LoadLexicon('../temp/testdefLex.txt', True)

    UnitTest = []
    if not os.path.exists(UnitTestFileName):
        print("Unit Test file " + UnitTestFileName + " does not exist.")
        exit(0)

    with open(UnitTestFileName, encoding="utf-8") as RuleFile:
        for line in RuleFile:
            if line.strip():
                RuleName, TestSentence = SeparateComment(line.strip())
                if not TestSentence:    # For the testfile that only have test sentence, not rule name
                    TestSentence = RuleName
                    RuleName = ""
                unittest = Rules.UnitTestNode(UnitTestFileName, RuleName, TestSentence)
                UnitTest.append(unittest)

    for unittestnode in UnitTest:
        ExtraMessageIndex = unittestnode.TestSentence.find(">")
        if ExtraMessageIndex>0:
            TestSentence = unittestnode.TestSentence[:ExtraMessageIndex]
        else:
            TestSentence = unittestnode.TestSentence
        TestSentence = TestSentence.strip("/")
        if DebugMode:
            print("***Test rule " + unittestnode.RuleName + " using sentence: " + TestSentence)

        nodes = ProcessSentence.Tokenize(TestSentence)

        # for node in nodes:
        #     #node.lexicon = FeatureOntology.SearchLexicon(node.word)
        #     ApplyLexiconURL = url + "/ApplyLexicon"
        #     ret = requests.post(ApplyLexiconURL, data=jsonpickle.encode(node))
        #     newnode = jsonpickle.decode(ret.text)
        #     node.features.update(newnode.features)

        ApplyLexiconToNodes = url + "/ApplyLexiconToNodes"
        ret = requests.post(ApplyLexiconToNodes, data=jsonpickle.encode(nodes))
        nodes = jsonpickle.decode(ret.text)

        # TokenizeAndApplyLexiconURL = url + "/TokenizeAndApplyLexicon"
        # ret = requests.post(TokenizeAndApplyLexiconURL, data=TestSentence)
        # nodes = jsonpickle.decode(ret.text)

        JSnode = Tokenization.SentenceNode('')
        nodes = [JSnode] + nodes
        nodes[0].features.add(FeatureOntology.GetFeatureID('JS'))

        nodes[1].features.add(FeatureOntology.GetFeatureID('JS2'))

        if nodes[-1].word != ".":
            JWnode = Tokenization.SentenceNode('')
            nodes = nodes + [JWnode]
        nodes[-1].features.add(FeatureOntology.GetFeatureID('JW'))

        Lexicon.LexiconLookup(nodes)

        if DebugMode:
            for node in nodes:
                print(node)

        MatchAndApplyRulesURL = url + "/MatchAndApplyRules"
        ret = requests.post(MatchAndApplyRulesURL, data=jsonpickle.encode(nodes))
        [WinningRules, nodes] = jsonpickle.decode(ret.text)
        print(str(WinningRules))
        for WinningRule in WinningRules:
            if Rules.GetPrefix(WinningRule) == Rules.GetPrefix(unittestnode.RuleName):
                print ("***Found " +WinningRule + " for: \n\t" + TestSentence)

        if DebugMode:
            for node in nodes:
                print(node)
        print(OutputStringTokens(nodes))