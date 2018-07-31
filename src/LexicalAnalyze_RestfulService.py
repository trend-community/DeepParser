import argparse, logging, os, configparser
import requests, urllib, random



ParserConfig = configparser.ConfigParser()
ParserConfig.read(os.path.join(os.path.dirname(os.path.realpath(__file__)),'config.ini'))

def LexicalAnalyzeURL():
    if not hasattr(LexicalAnalyzeURL, "Servers"):
        LexicalAnalyzeURL.Servers = [x.strip() for x in ParserConfig.get("client", "url_larestfulservice").splitlines() if x]
    rand = random.randrange(len(LexicalAnalyzeURL.Servers))
    return LexicalAnalyzeURL.Servers[rand] + "/LexicalAnalyze"


def LATask(extraparameter, Sentence):
    url = LexicalAnalyzeURL() + extraparameter + "&Sentence=" +  urllib.parse.quote("\"" + Sentence + "\"")
    ret = requests.get(url)
    return ret.text


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("inputfile", help="input file")
    parser.add_argument("--debug")
    parser.add_argument("--schema", help="full[default]/segonly/shallowcomplete")
    parser.add_argument("--action", help="none[default]/headdown")
    parser.add_argument("--type", help="segmentation/json/simple/simpleEx/graph/simplegraph[default]",
                        choices=['segmentation','json', 'simple', 'simpleEx', 'sentiment', 'graph', 'simplegraph'],
                        default='simplegraph')
    parser.add_argument("--keeporigin")
    args = parser.parse_args()

    DebugMode = False
    level = logging.INFO
    if args.debug:
        DebugMode = True
        level = logging.DEBUG

    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=level, format='%(asctime)s [%(levelname)s] %(message)s')

    #FeatureOntology.LoadFeatureOntology('../../fsa/Y/feature.txt')

    UnitTest = []
    if not os.path.exists(args.inputfile):
        print("Unit Test file " + args.inputfile + " does not exist.")
        exit(0)

    key = ''
    try:
        key = ParserConfig.get("client", "key")
    except :
        logging.error("Please provide legitimate authentication key in config.ini.")



    #logging.info("Start processing sentences")
    extra = "?Type={}&Key={}".format(args.type, key)
    if args.schema:
        extra += "&Schema=" + args.schema
    if args.action:
        extra += "&Action=" + args.action

    #Simple version, not multi-thread
    # with open(args.inputfile, encoding="utf-8") as RuleFile:
    #     for line in RuleFile:
    #         sentence = line.strip()
    #         if sentence:
    #             print(LATask(extra, sentence)  + '\t' + sentence)


    # below is a complicate version that can fully utilize the parser,
    # using thread_num in the config file.

    import concurrent.futures

    with open(args.inputfile, encoding="utf-8") as RuleFile:
        for line in RuleFile:
            if line.strip():
                UnitTest.append(line.strip())

    with concurrent.futures.ThreadPoolExecutor(max_workers=int(ParserConfig.get("client", "thread_num"))) as executor:
        Result = {}
        # We can use a with statement to ensure threads are cleaned up promptly
        # Start the load operations and mark each future with its URL
        future_to_url = {executor.submit(LATask, extra, sentence): sentence for sentence in UnitTest}
        future_new = {}
        logging.info("There are " + str(len(future_to_url)) + " to process.")
        for future in concurrent.futures.as_completed(future_to_url):
            s = future_to_url[future]
            try:
                data = future.result()
            except Exception as exc:
                logging.debug('%r generated an exception: \n %s' % (s, exc))
                future_new[executor.submit(LATask, extra, s)] = s
            else:
                if data:
                    Result[s] = data
                else:
                    future_new[executor.submit(LATask, extra, s)] = s
        logging.info("Redo the failed items: size=" + str(len(future_new)))
        for future in concurrent.futures.as_completed(future_new):
            s = future_new[future]
            try:
                data = future.result()
            except Exception as exc:
                logging.warning('%r Failed at second try: \n %s' % (s, exc))
            else:
                Result[s] = data
        logging.info("Done of retrieving data")

    for sentence in UnitTest:
        if sentence in Result:
            if args.keeporigin:
                print(Result[sentence] + '\t' + sentence)
            else:
                print(Result[sentence]  )
        else:
            print("Failed: " + sentence )
