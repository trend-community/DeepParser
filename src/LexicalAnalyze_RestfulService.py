import argparse
import FeatureOntology, Rules
import requests, urllib
from utils import *
import concurrent.futures

import singleton
me = singleton.SingleInstance()
LexicalAnalyzeURL = ParserConfig.get("client", "url_larestfulservice") + "/LexicalAnalyze?Type=simple"


def LATask(Sentence):
    ret = requests.get(LexicalAnalyzeURL + "&Sentence=\"" +  urllib.parse.quote(Sentence) + "\"")

    return ret.text

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("inputfile", help="input file")
    parser.add_argument("--debug")
    parser.add_argument("--mode", help="json/simple/simpleEx", choices=['json', 'simple', 'simpleEx'])
    args = parser.parse_args()

    DebugMode = False
    level = logging.INFO
    if args.debug:
        DebugMode = True
        level = logging.DEBUG

    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=level, format='%(asctime)s [%(levelname)s] %(message)s')

    FeatureOntology.LoadFeatureOntology('../../fsa/Y/feature.txt')

    UnitTest = []
    if not os.path.exists(args.inputfile):
        print("Unit Test file " + args.inputfile + " does not exist.")
        exit(0)

    with open(args.inputfile, encoding="utf-8") as RuleFile:
        for line in RuleFile:
            if line.strip():
                RuleName, TestSentence = SeparateComment(line.strip())
                if not TestSentence:    # For the testfile that only have test sentence, not rule name
                    TestSentence = RuleName
                    x = urllib.parse.quote(TestSentence)
                    RuleName = ""
                unittest = Rules.UnitTestNode(RuleName, TestSentence)
                UnitTest.append(unittest)

    logging.info("Start processing sentences")
    LexicalAnalyzeURL += "&Type=" + args.mode
    with concurrent.futures.ThreadPoolExecutor(max_workers=int(ParserConfig.get("client", "thread_num"))) as executor:
        Result = {}
    # We can use a with statement to ensure threads are cleaned up promptly
        # Start the load operations and mark each future with its URL
        future_to_url = {executor.submit(LATask, ut.TestSentence): ut.TestSentence for ut in UnitTest}
        future_new = {}
        for future in concurrent.futures.as_completed(future_to_url):
            s = future_to_url[future]
            try:
                data = future.result()
            except Exception as exc:
                logging.warning('%r generated an exception.' % (s, ))
                future_new[executor.submit(LATask, s)] = s
            else:
                Result[s] = data
        logging.info("Check future_new")
        for future in concurrent.futures.as_completed(future_new):
            s = future_new[future]
            try:
                data = future.result()
            except Exception as exc:
                logging.warning('%r Failed at second try: %s' % (s, exc))
            else:
                Result[s] = data
        logging.info("Done of retrieving data")

    for ut in UnitTest:
        if ut.TestSentence in Result:
            print(Result[ut.TestSentence])
        else:
            print("Failed: " + ut.TestSentence )