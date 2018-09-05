import logging, sys, jsonpickle
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

    ProcessSentence.LoadCommon()

    FailedList = []
    for RuleFile in sorted(Rules.RuleGroupDict, key=Rules.RuleGroupDict.get):
        print("Working on tests of " + RuleFile)
        rg = Rules.RuleGroupDict[RuleFile]
        for unittestnode in rg.UnitTest:
            ExtraMessageIndex = unittestnode.TestSentence.find(">")
            if ExtraMessageIndex>0:
                TestSentence = unittestnode.TestSentence[:ExtraMessageIndex]
            else:
                TestSentence = unittestnode.TestSentence
            print("\n***Test rule " + unittestnode.RuleName + " using sentence: " + TestSentence)

            nodes, WinningRules = ProcessSentence.LexicalAnalyze(TestSentence)

            if DebugMode:
                print(jsonpickle.dumps(nodes.root()))

            Failed = True
            for WinningRuleID in WinningRules:
                WinningRule = WinningRules[WinningRuleID]
                if WinningRule.startswith(unittestnode.RuleName):
                    print ("***Found " +WinningRule + " for: \n\t" + TestSentence)
                    Failed = False
                else:
                    print("Matched this non-related rule:" + WinningRule)

            if Failed:
                FailedList.append([unittestnode.RuleName, TestSentence, ProcessSentence.OutputStringTokens_oneliner(nodes, NoFeature=True)])

    print("Winning rules:\n" + ProcessSentence.OutputWinningRules())

    print("\nFailed list:")
    print("Rulename,  Test Sample,   Result of analyzing test sample")
    for sample in FailedList:
        print(str(sample))

    logging.info("Done!")