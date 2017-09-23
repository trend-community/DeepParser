import logging, sys, re, os
import Tokenization, FeatureOntology
import ProcessSentence, Rules
import requests, json, jsonpickle
from functools import lru_cache

url = "http://localhost:5001"
url_ch = "http://localhost:8080"

IMPOSSIBLESTRING = "@#$%!"


def Tokenize(Sentence):
    if IsAscii(Sentence):
        TokenizeURL = url + "/Tokenize"
        ret_t = requests.post(TokenizeURL, data=Sentence)
        nodes_t = jsonpickle.decode(ret_t.text)
    else:
        TokenizeURL = url_ch + "/Tokenize/"
        #ret_t = requests.get(TokenizeURL + Sentence)
        data = {'Sentence': Sentence}
        segmented = requests.get(TokenizeURL, params=data).text
        #segmented = jsonpickle.decode(segmented)
        segmented = segmented.replace("\/", IMPOSSIBLESTRING)
        blocks = segmented.split("/")
        nodes_t = []
        for block in blocks:
            block = block.replace(IMPOSSIBLESTRING, "\/")
            Element = Tokenization.SentenceNode('')
            WordPropertyPair = block.split(":")
            Element.word = WordPropertyPair[0]
            if len(WordPropertyPair)>1:
                features = WordPropertyPair[1]
                for feature in features.split():
                    featureid = FeatureOntology.GetFeatureID(feature)
                    Element.features.add(featureid)

            nodes_t.append(Element)
    return nodes_t

def IsAscii(Sentence):
    try:
        Sentence.encode(encoding='utf-8').decode('ascii')
    except UnicodeDecodeError:
        return False
    else:
        return True

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

    UnitTest = []
    if not os.path.exists(UnitTestFileName):
        print("Unit Test file " + UnitTestFileName + " does not exist.")
        exit(0)

    with open(UnitTestFileName, encoding="utf-8") as RuleFile:
        for line in RuleFile:
            if line.strip():
                RuleName, TestSentence = Rules._SeparateComment(line.strip())
                unittest = Rules.UnitTestNode(UnitTestFileName, RuleName, TestSentence)
                UnitTest.append(unittest)

    for unittestnode in UnitTest:
        ExtraMessageIndex = unittestnode.TestSentence.find(">")
        if ExtraMessageIndex>0:
            TestSentence = unittestnode.TestSentence[:ExtraMessageIndex]
        else:
            TestSentence = unittestnode.TestSentence
        print("***Test rule " + unittestnode.RuleName + " using sentence: " + TestSentence)

        nodes = Tokenize(TestSentence)

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
