import argparse
import ProcessSentence, Rules, FeatureOntology
from utils import *

import singleton
me = singleton.SingleInstance()

def ProcessFile(FileName):
    if FileName.startswith("."):
        FileName = os.path.join(os.path.dirname(os.path.realpath(__file__)),  FileName)
    UnitTest = []
    if not os.path.exists(FileName):
        print("Unit Test file " + FileName + " does not exist.")
        exit(0)

    with open(FileName, encoding="utf-8") as RuleFile:
        for line in RuleFile:
            if line.strip():
                RuleName, TestSentence = SeparateComment(line.strip())
                if not TestSentence:  # For the testfile that only have test sentence, not rule name
                    TestSentence = RuleName
                    RuleName = ""
                unittest = Rules.UnitTestNode(RuleName, TestSentence)
                UnitTest.append(unittest)

    for unittestnode in UnitTest:
        ExtraMessageIndex = unittestnode.TestSentence.find(">")
        if ExtraMessageIndex > 0:
            TestSentence = unittestnode.TestSentence[:ExtraMessageIndex]
        else:
            TestSentence = unittestnode.TestSentence
        TestSentence = TestSentence.strip("/")
        if DebugMode:
            print("***Test rule " + unittestnode.RuleName + " using sentence: " + TestSentence)

        nodes, _ = ProcessSentence.LexicalAnalyze(TestSentence)
        if not nodes:
            logging.warning("The result for this sentence is None! " + str(TestSentence))
            continue

        if DebugMode:
            print(nodes)
        if args.mode == 'json':
            print(nodes.root().CleanOutput().toJSON())
        else:
            print(OutputStringTokens_oneliner(nodes, NoFeature=True))

    if args.winningrules:
        print("Winning rules:\n" + ProcessSentence.OutputWinningRules())
    if args.extra:
        print(FeatureOntology.OutputMissingFeatureSet())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("inputfile", help="input file")
    parser.add_argument("--debug")
    parser.add_argument("--mode", help="json/simple", choices=['json', 'simple'])
    parser.add_argument("--winningrules")
    parser.add_argument("--extra")

    args = parser.parse_args()

    DebugMode = False
    level = logging.WARNING
    if args.debug:
        DebugMode = True
        level = logging.DEBUG

    if args.mode == 'json':
        pass

    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=level, format='%(asctime)s [%(levelname)s] %(message)s')

    ProcessSentence.LoadCommon()

    if logging.getLogger().isEnabledFor(logging.DEBUG):
        ProcessFile(args.inputfile)
    else:   #debugging modef
        # ProcessFile(UnitTestFileName)
        # pass
        import cProfile, pstats
        cProfile.run("ProcessFile(args.inputfile)", 'restats')
        p = pstats.Stats('restats')
        p.sort_stats('time').print_stats(30)

    #Rules.OutputRuleFiles("../temp/rule.after/")
