import logging, sys, re
import Tokenization, FeatureOntology, Lexicon
import ProcessSentence, Rules

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
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    ProcessSentence.LoadCommon(True)

    for RuleFile in Rules.RuleGroupDict:
        print("Working on tests of " + RuleFile)
        rg = Rules.RuleGroupDict[RuleFile]
        for unittestnode in rg.UnitTest:
            ExtraMessageIndex = unittestnode.TestSentence.find(">")
            if ExtraMessageIndex>0:
                TestSentence = unittestnode.TestSentence[:ExtraMessageIndex]
            else:
                TestSentence = unittestnode.TestSentence
            print("***Test rule " + unittestnode.RuleName + " using sentence: " + TestSentence)

            nodes = ProcessSentence.MultiLevelSegmentation(TestSentence)

            if DebugMode:
                for node in nodes:
                    print(node)

            WinningRules = ProcessSentence.MatchAndApplyAllRules(nodes)
            for WinningRule in WinningRules:
                if Rules.GetPrefix(WinningRule) == Rules.GetPrefix(unittestnode.RuleName):
                    print ("***Found " +WinningRule + " for: \n\t" + TestSentence)

            if DebugMode:
                for node in nodes:
                    print(node)
    print("Winning rules:\n" + ProcessSentence.OutputWinningRules())

