import logging, sys, re, os
import Tokenization, FeatureOntology
import ProcessSentence, Rules
import requests, json, jsonpickle
from functools import lru_cache

url = "http://localhost:5001"

@lru_cache(maxsize=1000)
def GetFeatureID(Feature):
    GetFeatureIDURL = url + "/GetFeatureID/"
    return int(requests.get(GetFeatureIDURL + Feature).text)


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

    UnitTest = []
    if not os.path.exists(UnitTestFileName):
        print("Unit Test file " + UnitTestFileName + " does not exist.")
        exit(0)

    with open(UnitTestFileName, encoding="utf-8") as RuleFile:
        for line in RuleFile:
            RuleName, TestSentence = Rules._SeparateComment(line)
            unittest = Rules.UnitTestNode(UnitTestFileName, RuleName, TestSentence)
            UnitTest.append(unittest)

    for unittestnode in UnitTest:
        ExtraMessageIndex = unittestnode.TestSentence.find(">")
        if ExtraMessageIndex>0:
            TestSentence = unittestnode.TestSentence[:ExtraMessageIndex]
        else:
            TestSentence = unittestnode.TestSentence
        print("***Test rule " + unittestnode.RuleName + " using sentence: " + TestSentence)

        # TokenizeURL = url + "/Tokenize"
        # ret = requests.post(TokenizeURL, data=TestSentence)
        # nodes = jsonpickle.decode(ret.text)
        #
        # for node in nodes:
        #     #node.lexicon = FeatureOntology.SearchLexicon(node.word)
        #     ApplyLexiconURL = url + "/ApplyLexicon"
        #     ret = requests.post(ApplyLexiconURL, data=jsonpickle.encode(node))
        #     newnode = jsonpickle.decode(ret.text)
        #     node.features.update(newnode.features)


        TokenizeAndApplyLexiconURL = url + "/TokenizeAndApplyLexicon"
        ret = requests.post(TokenizeAndApplyLexiconURL, data=TestSentence)
        nodes = jsonpickle.decode(ret.text)


        JSnode = Tokenization.SentenceNode()
        nodes = [JSnode] + nodes
        nodes[0].features.add(GetFeatureID('JS'))

        nodes[1].features.add(GetFeatureID('JS2'))

        if nodes[-1].word != ".":
            JWnode = Tokenization.SentenceNode()
            nodes = nodes + [JWnode]
        nodes[-1].features.add(GetFeatureID('JW'))

        if DebugMode:
            for node in nodes:
                print(node)

        SearchMatchingRuleURL = url + "/SearchMatchingRule"
        ret = requests.post(SearchMatchingRuleURL, data=jsonpickle.encode(nodes))
        WinningRules = jsonpickle.decode(ret.text)
        for WinningRule in WinningRules:
            if Rules.GetPrefix(WinningRule) == Rules.GetPrefix(unittestnode.RuleName):
                print ("***Found " +WinningRule + " for: \n\t" + TestSentence)
