import logging, datetime
import ProcessSentence, Rules

def RuleUnitTest():
    FailedList = []
    TotalTest = 0;
    TotalSuccess = 0
    for RuleFile in sorted(Rules.RuleGroupDict, key=Rules.RuleGroupDict.get):
        logging.debug("Working on tests of " + RuleFile)
        rg = Rules.RuleGroupDict[RuleFile]
        TestCount = len(rg.UnitTest)
        SuccessCount= 0
        RuleNameDict = { rule.RuleName:rule.Origin for rule in rg.RuleList}
        for unittestnode in rg.UnitTest:
            ExtraMessageIndex = unittestnode.TestSentence.find(">")
            if ExtraMessageIndex>0:
                TestSentence = unittestnode.TestSentence[:ExtraMessageIndex]
            else:
                TestSentence = unittestnode.TestSentence

            RuleOrigin = ''
            if unittestnode.RuleName in RuleNameDict:
                RuleOrigin = RuleNameDict[unittestnode.RuleName]
            else:
                for rule in rg.RuleList:
                    if rule.RuleName.startswith(unittestnode.RuleName):
                        RuleOrigin = rule.Origin
                        break
            if not RuleOrigin:
                logging.warning("Can't fine rule {} in {}".format(unittestnode.RuleName, RuleFile))
            log.debug("\n***Test rule {} using sentence: {}. Rule Origin:{}".format(unittestnode.RuleName, TestSentence, RuleOrigin))

            nodes, dag, WinningRules = ProcessSentence.LexicalAnalyze(TestSentence)

            Failed = True
            if WinningRules:
                for WinningRuleID in WinningRules:
                    WinningRule = WinningRules[WinningRuleID]
                    if unittestnode.RuleName in WinningRule:
                        log.debug ("***Found " +WinningRule + " for: \n\t" + TestSentence)
                        Failed = False
                        SuccessCount += 1
                    else:
                        log.debug("Matched this non-related rule:" + WinningRule)

            if Failed:
                FailedList.append([unittestnode.RuleName, TestSentence, ProcessSentence.OutputStringTokens_oneliner(nodes, NoFeature=True)])

        log.info(f"For {RuleFile}, got {SuccessCount}/{TestCount}")
        TotalTest += TestCount
        TotalSuccess += SuccessCount

    log.info("Failed list:\n")
    log.info("Rulename,  Test Sample,   Result of analyzing test sample")
    for sample in FailedList:
        log.info(str(sample))
    log.info(f"Total: {TotalSuccess}/{TotalTest}")
    #log.info(f"{TotalSuccess=}/{TotalTest=}")


if __name__ == "__main__":
    LogFilename = "{}.{}.log".format(ProcessSentence.ProjectName, datetime.datetime.now().strftime('%Y%m%d_%H%M'))
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    log = logging.getLogger('log1')
    debughandler = logging.FileHandler("debug." + LogFilename, 'w', 'utf-8')
    debughandler.setFormatter(formatter)
    debughandler.setLevel(logging.DEBUG)
    log.addHandler(debughandler)
    infohandler = logging.FileHandler("info." + LogFilename, 'w', 'utf-8')
    infohandler.setFormatter(formatter)
    infohandler.setLevel(logging.INFO)
    log.addHandler(infohandler)
    # warninghandler = logging.FileHandler("warning.log", 'w', 'utf-8')
    # warninghandler.setFormatter(formatter)
    # warninghandler.setLevel(logging.WARNING)
    # log.addHandler(warninghandler)


    ProcessSentence.LoadCommon()

    import cProfile, pstats, io

    s = io.StringIO()
    cProfile.run("RuleUnitTest()", 'restatslex')
    pstat = pstats.Stats('restatslex', stream=s)
    pstat.sort_stats('time').print_stats(60)

    log.info(s.getvalue())

    log.info("Done!")