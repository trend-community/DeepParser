import argparse, os, logging
import ProcessSentence
import utils
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
                    if int(args.sentencecolumn) == 0:
                        UnitTest.append(line.strip())
                    else:
                        columns = line.split(args.delimiter)
                        if len(columns) >= int(args.sentencecolumn):
                            UnitTest.append(columns[int(args.sentencecolumn) - 1].strip())

    for TestSentence in UnitTest:
        nodes, dag, _ = ProcessSentence.LexicalAnalyze(TestSentence, schema=args.schema)
        if not nodes:
            logging.warning("The result for this sentence is None! " + str(TestSentence))
            continue
        if len(dag.nodes) == 0:
            dag.transform(nodes)
        if args.type == 'json':
            output = nodes.root().CleanOutput().toJSON()
        elif  args.type == 'simple':
            output = utils.OutputStringTokens_oneliner(nodes, NoFeature=True)
        elif args.type == "sentiment":
            if len(dag.nodes) == 0:
                dag.transform(nodes)
            # print (OutputStringTokens_onelinerSA(dag))
            output = utils.OutputStringTokens_onelinerSA(dag)
        elif args.type == 'graph':
            output = dag.digraph(args.type)
        elif args.type == 'simplegraph':
            output = dag.digraph(args.type)
        else:   #simpleEx
            output = utils.OutputStringTokens_oneliner_ex(nodes)

        if args.keeporigin:
            output += '\t' + TestSentence
        print(output)
    if args.winningrules:
        print("Winning rules:\n" + ProcessSentence.OutputWinningRules())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("inputfile", help="input file")
    parser.add_argument("--debug", action='store_true')
    parser.add_argument("--winningrules", action='store_true')
    parser.add_argument("--keeporigin",  action='store_true')
    parser.add_argument("--type", help="json/simple/simpleEx/sentiment/graph/simplegraph/graphjson",
                        default='simplegraph')
    parser.add_argument("--sentencecolumn", help="if the file has multiple columns, list the specific column to process (1-based)",
                        default=0)
    parser.add_argument("--delimiter", default="\t")
    parser.add_argument("--schema", help="full(default)/segonly/shallowcomplete",
                        default="full")
    args = parser.parse_args()

    DebugMode = False
    level = logging.WARNING
    if args.debug:
        DebugMode = True
        level = logging.INFO

    if args.type == 'json':
        pass

    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=level, format='%(asctime)s [%(levelname)s] %(message)s')

    ProcessSentence.LoadCommon()


    # ProcessFile(args.inputfile)


    import cProfile, pstats
    cProfile.run("ProcessFile(args.inputfile)", 'restats')
    p = pstats.Stats('restats')
    p.sort_stats('time').print_stats(60)

    #from LogicOperation import hitcount
    #logging.warning("LogicMatch hit count:{}".format(hitcount))
    # import os
    # import psutil
    #
    # process = psutil.Process(os.getpid())
    # print(process.memory_info().rss)

    #Rules.OutputRuleFiles("../temp/rule.after/")
