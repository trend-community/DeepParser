import logging, sys, re, os
import Tokenization, FeatureOntology, Lexicon
import ProcessSentence, Rules
import requests, json, jsonpickle
from utils import *


if __name__ == "__main__":
    DebugMode = False
    NoFeature = False
    level = logging.INFO
    if len(sys.argv) > 1:
        UnitTestFileName = sys.argv[1]
        if len(sys.argv) > 2:
            command = sys.argv[2]
            if command == 'Debug':
                DebugMode = True
                level = logging.DEBUG
            if command == 'NoFeature':
                NoFeature = True
    else:
        print(
            "Usage: python MultiLevelSegment_ResefulService.py unittestfile [Debug]/[NoFeature]")
        exit(0)

    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=level, format='%(asctime)s [%(levelname)s] %(message)s')

    FeatureOntology.LoadFeatureOntology('../../fsa/Y/feature.txt')

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
                unittest = Rules.UnitTestNode(RuleName, TestSentence)
                UnitTest.append(unittest)

    for unittestnode in UnitTest:
        logging.debug("-Start one unit test")
        ExtraMessageIndex = unittestnode.TestSentence.find(">")
        if ExtraMessageIndex>0:
            TestSentence = unittestnode.TestSentence[:ExtraMessageIndex]
        else:
            TestSentence = unittestnode.TestSentence
        TestSentence = TestSentence.strip("/")
        if DebugMode:
            print("***Test rule " + unittestnode.RuleName + " using sentence: " + TestSentence)

        MultiLevelSegmentationURL = url + "/MultiLevelSegmentation/"
        logging.debug("-request MultiLevelSegmentation")
        ret = requests.get(MultiLevelSegmentationURL + TestSentence)
        logging.debug("-get request")
        nodes = jsonpickle.decode(ret.text)

        if DebugMode:
            for node in nodes:
                print(node)

        print(OutputStringTokens_oneliner(nodes, NoFeature))

    print("Winning rules:\n" + ProcessSentence.OutputWinningRules())