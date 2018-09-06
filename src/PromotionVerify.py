import argparse
import requests, urllib, random
import ProcessSentence
from utils import *

#File format:  intent\tQ
#intent that we care:
# 1173 能否优惠
# 2184 近期活动咨询
# 940 促销形式
# 54 评价晒单返券和赠品
# 0  赠品领取更换

def LexicalAnalyzeURL():
    if not hasattr(LexicalAnalyzeURL, "Servers"):
        LexicalAnalyzeURL.Servers = [x.strip() for x in ParserConfig.get("client", "url_larestfulservice").splitlines() if x]
    rand = random.randrange(len(LexicalAnalyzeURL.Servers))
    return LexicalAnalyzeURL.Servers[rand] + "/LexicalAnalyze"


def LATask(extraparameter, Sentence):
    url = LexicalAnalyzeURL() + extraparameter + "&Sentence=" +  urllib.parse.quote("\"" + Sentence + "\"")
    logging.debug("Start: " + url)
    ret = requests.get(url)
    return ret.text

class Intent(object):
    def __init__(self, pair):
        if len(pair) != 2:
            logging.error("Wrong Intent initialization parameter: {}".format(pair))
        self.Q = pair[1].strip()
        self.Intent = pair[0].strip()
        self.tags = set()


def ExtractTags(intent, graphjson):
    try:
        g = jsonpickle.decode(graphjson)
        for node in g["nodes"]:
            if 'pnorm' in node:
                intent.tags.add(node["pnorm"])
    except json.decoder.JSONDecodeError :
        logging.error("Failed to decode for this question: {}".format(intent.Q))



intentdict = {}

def ProcessFile(FileName):
    if FileName.startswith("."):
        FileName = os.path.join(os.path.dirname(os.path.realpath(__file__)),  FileName)

    if not os.path.exists(FileName):
        print("Unit Test file " + FileName + " does not exist.")
        exit(0)

    with open(FileName, encoding="utf-8") as RuleFile:
        for line in RuleFile:
            if line.strip():
                intent = Intent(line.split(args.delimiter))
                intentdict[intent.Q] = intent

    # local process
    # for intent in intents:
    #     nodes, dag, _ = ProcessSentence.LexicalAnalyze(intent.Q)
    #     if not nodes:
    #         logging.warning("The result for this sentence '{}' is None! ".format(intent.Q))
    #         continue
    #     for nodeid in dag.nodes:
    #         if dag.nodes[nodeid].pnorm:
    #             intent.tags.add(dag.nodes[nodeid].pnorm)
    #     logging.info("Gold Standard: {}\tResult:{}".format(intent.Intent, intent.tags))

    key = ''
    try:
        key = ParserConfig.get("client", "key")
    except :
        logging.error("Please provide legitimate authentication key in config.ini.")

    extra = "?Type={}&Key={}".format("graphjson", key)


    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=int(ParserConfig.get("client", "thread_num"))) as executor:
        future_to_url = {executor.submit(LATask, extra, Q): Q for Q in intentdict}
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
                    ExtractTags(intentdict[s], data)
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
                ExtractTags(intentdict[s], data)
        logging.info("Done of retrieving data")


    PromotionTags=[["能否优惠"], ["近期活动咨询"], ["促销形式"], ["评价晒单返券和赠品"], ["赠品领取更换"],
                   ["能否优惠", "近期活动咨询"], ["促销形式", "评价晒单返券和赠品", "赠品领取更换"]]
    for Tags in PromotionTags:
        TP = 0
        FP = 0
        FN = 0
        TN = 0
        P = 0
        R = 0
        F = 0
        for Q in intentdict:
            intent = intentdict[Q]
            if intent.Intent in Tags:
                if set(Tags).intersection(intent.tags):
                    TP += 1
                else:
                    FN += 1
            else:
                if set(Tags).intersection(intent.tags):
                    FP += 1
                else:
                    TN += 1
        print("Tag {}: TP={}, FN={}, FP={}, TN={}".format(Tags, TP, FN, FP, TN))
        if (TP+FP) > 0:
            P = TP/(TP+FP)
        if (TP+FN) >0:
            R = TP/(TP+FN)
        if (P+R) > 0:
            F = 2*P*R/(P+R)
        print("\tPrecision={}, Recall={}, F score={}".format(P, R, F))
        print("\tFN cases:")
        for Q in intentdict:
            intent = intentdict[Q]
            if intent.Intent in Tags:
                if not set(Tags).intersection(intent.tags):
                    print("\t\t{}-{}\t{}".format(intent.Intent, intent.tags, intent.Q))
        print("\tFP cases:")
        for Q in intentdict:
            intent = intentdict[Q]
            if intent.Intent not in Tags:
                if set(Tags).intersection(intent.tags):
                    print("\t\t{}-{}\t{}".format(intent.Intent, intent.tags, intent.Q))

    print("Sentence that has more than 1 tags:")
    for Q in intentdict:
        intent = intentdict[Q]
        if len(intent.tags) > 1:
            print("\t{}-{}\t{}".format(intent.Intent, intent.tags, intent.Q))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("inputfile", help="input file")
    parser.add_argument("--delimiter", default="\t")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    ProcessFile(args.inputfile)

