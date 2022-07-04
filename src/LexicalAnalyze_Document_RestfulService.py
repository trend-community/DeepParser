import argparse, logging, os, configparser
import requests,  random


ParserConfig = configparser.ConfigParser()
ParserConfig.read(os.path.join(os.path.dirname(os.path.realpath(__file__)),'config.ini'))

def LexicalAnalyzeURL():
    if not hasattr(LexicalAnalyzeURL, "Servers"):
        LexicalAnalyzeURL.Servers = [x.strip() for x in ParserConfig.get("client", "url_larestfulservice").splitlines() if x]
    rand = random.randrange(len(LexicalAnalyzeURL.Servers))
    return LexicalAnalyzeURL.Servers[rand] + "/DocumentAnalyze"


def LATask( Sentence):
    QueryData={'Key':ParserConfig.get("client", "key"),
        'type':args.type,
        'document':Sentence,
        'newline':'. ',
               'transferlinebreak': 'transfer'}
    ret = requests.post(LexicalAnalyzeURL(), data=QueryData)
    return ret.text


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("inputfile", help="input file")
    parser.add_argument("--debug")
    parser.add_argument("--schema", help="full[default]/segonly/shallowcomplete")
    parser.add_argument("--action", help="none[default]/headdown")
    parser.add_argument("--type", help="segmentation/json/simple/simpleEx/graph/graphjson/simplegraph[default]/pnorm",
                        default='simplegraph')
    parser.add_argument("--keeporigin")
    parser.add_argument("--sentencecolumn", help="if the file has multiple columns, list the specific column to process (1-based)",
                        default=0)
    parser.add_argument("--delimiter", default="\t")
    args = parser.parse_args()

    DebugMode = False
    level = logging.INFO
    if args.debug:
        DebugMode = True
        level = logging.DEBUG

    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=level, format='%(asctime)s [%(levelname)s] %(message)s')

    UnitTest = []
    if not os.path.exists(args.inputfile):
        print("Sentence file " + args.inputfile + " does not exist.")
        exit(0)


    with open(args.inputfile, encoding="GBK", errors='ignore') as RuleFile:
        document = RuleFile.read()

    result = LATask(document)

    print(result)
