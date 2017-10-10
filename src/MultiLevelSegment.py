import logging, sys, os
import ProcessSentence, Rules
from utils import *

import singleton
me = singleton.SingleInstance()

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
            "Usage: python MultiLevelSegment.py unittestfile [Debug]/[NoFeature]")
        exit(0)

    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=level, format='%(asctime)s [%(levelname)s] %(message)s')

    ProcessSentence.LoadCommon(True)

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
                unittest = Rules.UnitTestNode( RuleName, TestSentence)
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

        nodes = ProcessSentence.MultiLevelSegmentation(TestSentence)

        if DebugMode:
            for node in nodes:
                print(node)
        print(OutputStringTokens_oneliner(nodes, NoFeature))

    print("Winning rules:\n" + ProcessSentence.OutputWinningRules())
